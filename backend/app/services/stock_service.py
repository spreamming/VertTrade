from datetime import date, datetime, timedelta
from threading import Lock
from types import SimpleNamespace

import requests
from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..collectors.kline_collector import fetch_daily_kline
from ..collectors.intraday_kline_collector import fetch_intraday_kline
from ..collectors.moneyflow_collector import (
    MoneyflowDataSourceError,
    fetch_stock_moneyflow,
)
from ..collectors.realtime_quote_collector import (
    RealtimeQuoteDataSourceError,
    fetch_live_quote,
)
from ..collectors.timeshare_collector import fetch_timeshare
from ..collectors.stock_basic_collector import fetch_stock_list
from ..indicators.position_score import calculate_position_score
from ..repositories.kline_repo import KlineRepository
from ..repositories.moneyflow_repo import MoneyflowRepository
from ..repositories.stock_repo import StockRepository
from ..schemas.stock import (
    KlineBar,
    KlineResponse,
    MoneyflowBar,
    MoneyflowResponse,
    StockPosition,
    StockQuote,
    StockSummary,
    TimeSharePoint,
    TimeShareResponse,
)


class StockService:
    # Calendar-day tolerance before treating cached K-line end as stale (weekends/holidays).
    _CACHE_END_TOLERANCE_DAYS = 4
    _LIVE_QUOTE_TTL_SECONDS = 3
    _INTRADAY_KLINE_TTL_SECONDS = 20
    _TIMESHARE_TTL_SECONDS = 15
    _live_quote_cache: dict[str, tuple[datetime, StockQuote]] = {}
    _intraday_kline_cache: dict[tuple[str, str], tuple[datetime, KlineResponse]] = {}
    _timeshare_cache: dict[str, tuple[datetime, TimeShareResponse]] = {}
    _live_quote_locks: dict[str, Lock] = {}
    _kline_fetch_locks: dict[str, Lock] = {}
    _moneyflow_fetch_locks: dict[str, Lock] = {}
    _live_quote_locks_guard = Lock()

    def __init__(self, db: Session):
        self.db = db
        self.stock_repo = StockRepository(db)
        self.kline_repo = KlineRepository(db)
        self.moneyflow_repo = MoneyflowRepository(db)

    @staticmethod
    def _position_lookback_days(window: int) -> int:
        return max(365, int(window * 1.8) + 30)

    @classmethod
    def _cache_end_is_stale(cls, latest_cached: date, end_date: date) -> bool:
        if latest_cached >= end_date:
            return False
        return (end_date - latest_cached).days > cls._CACHE_END_TOLERANCE_DAYS

    def ensure_stock_catalog(self) -> None:
        if self.stock_repo.count() > 0:
            return

        frame = fetch_stock_list()
        rows = frame.to_dict(orient="records")
        self.stock_repo.upsert_many(rows)

    def search_stocks(self, keyword: str, limit: int = 20) -> list[StockSummary]:
        self.ensure_stock_catalog()
        matches = self.stock_repo.search(keyword, limit=limit)
        return [
            StockSummary(code=stock.code, name=stock.name, exchange=stock.exchange)
            for stock in matches
        ]

    @classmethod
    def _fetch_lock_for_code(cls, code: str, kind: str) -> Lock:
        with cls._live_quote_locks_guard:
            locks = cls._kline_fetch_locks if kind == "kline" else cls._moneyflow_fetch_locks
            if code not in locks:
                locks[code] = Lock()
            return locks[code]

    def _kline_needs_fetch(
        self,
        code: str,
        start_date: date,
        end_date: date,
        *,
        refresh: bool,
        start: date | None,
    ) -> tuple[list, bool]:
        cached = self.kline_repo.get_range(code, start_date, end_date)
        latest_cached_date = cached[-1].trade_date if cached else None
        start_not_covered = (
            start is not None and cached and cached[0].trade_date > start_date
        )
        end_is_stale = (
            latest_cached_date is not None
            and self._cache_end_is_stale(latest_cached_date, end_date)
        )
        needs_fetch = refresh or not cached or start_not_covered or end_is_stale
        return cached, needs_fetch

    def _refresh_kline_cache(
        self,
        code: str,
        start_date: date,
        end_date: date,
    ) -> list:
        try:
            frame = fetch_daily_kline(code, start_date, end_date)
        except requests.RequestException as exc:
            cached = self.kline_repo.get_range(code, start_date, end_date)
            if cached:
                return cached
            raise HTTPException(
                status_code=503,
                detail=(
                    "暂时无法从数据源获取行情数据，"
                    "请检查网络连接后重试。"
                ),
            ) from exc

        if frame.empty:
            cached = self.kline_repo.get_range(code, start_date, end_date)
            if not cached:
                raise HTTPException(
                    status_code=404,
                    detail=f"暂无 {code} 的 K 线数据",
                )
            return cached

        rows = frame.to_dict(orient="records")
        self.kline_repo.replace_range(code, rows)
        return self.kline_repo.get_range(code, start_date, end_date)

    def get_kline(
        self,
        code: str,
        start: date | None = None,
        end: date | None = None,
        refresh: bool = False,
    ) -> KlineResponse:
        self.ensure_stock_catalog()
        stock = self.stock_repo.get_by_code(code)
        if stock is None:
            raise HTTPException(status_code=404, detail=f"未找到股票 {code}")

        end_date = end or date.today()
        start_date = start or (end_date - timedelta(days=365))

        cached, needs_fetch = self._kline_needs_fetch(
            code,
            start_date,
            end_date,
            refresh=refresh,
            start=start,
        )
        if needs_fetch:
            lock = self._fetch_lock_for_code(code, "kline")
            with lock:
                cached, needs_fetch = self._kline_needs_fetch(
                    code,
                    start_date,
                    end_date,
                    refresh=refresh,
                    start=start,
                )
                if needs_fetch:
                    cached = self._refresh_kline_cache(code, start_date, end_date)

        bars = [
            KlineBar(
                date=bar.trade_date,
                open=bar.open,
                high=bar.high,
                low=bar.low,
                close=bar.close,
                volume=bar.volume,
                amount=bar.amount,
                turnover_rate=bar.turnover_rate,
            )
            for bar in cached
        ]

        return KlineResponse(code=stock.code, name=stock.name, bars=bars)

    @staticmethod
    def _with_cache_metadata(
        response: KlineResponse | TimeShareResponse,
        cached_at: datetime,
        now: datetime,
        *,
        is_stale: bool,
    ) -> KlineResponse | TimeShareResponse:
        cache_age = (now - cached_at).total_seconds()
        return response.model_copy(
            update={
                "cache_time": cached_at,
                "is_stale": is_stale,
                "cache_age_seconds": cache_age,
            }
        )

    def get_intraday_kline(
        self,
        code: str,
        period: str = "1m",
        refresh: bool = False,
    ) -> KlineResponse:
        if period not in ("1m", "5m", "15m", "30m", "60m"):
            raise HTTPException(
                status_code=400,
                detail="分钟 K 周期仅支持 1m、5m、15m、30m、60m",
            )

        self.ensure_stock_catalog()
        stock = self.stock_repo.get_by_code(code)
        if stock is None:
            raise HTTPException(status_code=404, detail=f"未找到股票 {code}")

        cache_key = (code, period)
        cached = self._intraday_kline_cache.get(cache_key)
        now = datetime.now()
        if not refresh and cached:
            cached_at, cached_response = cached
            cache_age = (now - cached_at).total_seconds()
            if cache_age <= self._INTRADAY_KLINE_TTL_SECONDS:
                return self._with_cache_metadata(
                    cached_response,
                    cached_at,
                    now,
                    is_stale=False,
                )

        try:
            frame, source = fetch_intraday_kline(code, period=period)
        except (requests.RequestException, ValueError) as exc:
            if cached:
                cached_at, cached_response = cached
                return self._with_cache_metadata(
                    cached_response,
                    cached_at,
                    now,
                    is_stale=True,
                )
            raise HTTPException(
                status_code=503,
                detail="暂时无法从数据源获取分钟 K 数据，请稍后重试。",
            ) from exc

        bars = [
            KlineBar(
                date=row["trade_time"],
                open=row["open"],
                high=row["high"],
                low=row["low"],
                close=row["close"],
                volume=row["volume"],
                amount=row["amount"],
                turnover_rate=row["turnover_rate"],
            )
            for row in frame.to_dict(orient="records")
        ]

        response = KlineResponse(
            code=stock.code,
            name=stock.name,
            period=period,
            bars=bars,
            source=source,
            cache_time=now,
            is_stale=False,
            cache_age_seconds=0,
        )
        self._intraday_kline_cache[cache_key] = (now, response)
        return response

    def get_timeshare(self, code: str, refresh: bool = False) -> TimeShareResponse:
        self.ensure_stock_catalog()
        stock = self.stock_repo.get_by_code(code)
        if stock is None:
            raise HTTPException(status_code=404, detail=f"未找到股票 {code}")

        cached = self._timeshare_cache.get(code)
        now = datetime.now()
        if not refresh and cached:
            cached_at, cached_response = cached
            cache_age = (now - cached_at).total_seconds()
            if cache_age <= self._TIMESHARE_TTL_SECONDS:
                return self._with_cache_metadata(
                    cached_response,
                    cached_at,
                    now,
                    is_stale=False,
                )

        try:
            frame, source = fetch_timeshare(code)
        except (requests.RequestException, ValueError) as exc:
            if cached:
                cached_at, cached_response = cached
                return self._with_cache_metadata(
                    cached_response,
                    cached_at,
                    now,
                    is_stale=True,
                )
            raise HTTPException(
                status_code=503,
                detail="暂时无法从数据源获取分时图数据，请稍后重试。",
            ) from exc

        points = [
            TimeSharePoint(
                time=row["time"],
                price=row["price"],
                average_price=row["average_price"],
                volume=row["volume"],
                amount=row["amount"],
            )
            for row in frame.to_dict(orient="records")
        ]
        response = TimeShareResponse(
            code=stock.code,
            name=stock.name,
            source=source,
            points=points,
            cache_time=now,
            is_stale=False,
            cache_age_seconds=0,
        )
        self._timeshare_cache[code] = (now, response)
        return response

    def _build_quote_from_kline(self, kline: KlineResponse, code: str) -> StockQuote:
        if not kline.bars:
            raise HTTPException(status_code=404, detail=f"暂无 {code} 的行情摘要")

        latest = kline.bars[-1]
        previous = kline.bars[-2] if len(kline.bars) > 1 else None
        pre_close = previous.close if previous else None
        change_amount = latest.close - pre_close if pre_close is not None else None
        change_percent = (
            (change_amount / pre_close) * 100
            if pre_close not in (None, 0) and change_amount is not None
            else None
        )

        stock = self.stock_repo.get_by_code(code)
        return StockQuote(
            code=kline.code,
            name=kline.name,
            exchange=stock.exchange if stock else "UNKNOWN",
            latest_price=latest.close,
            change_amount=change_amount,
            change_percent=change_percent,
            open=latest.open,
            high=latest.high,
            low=latest.low,
            pre_close=pre_close,
            volume=latest.volume,
            amount=latest.amount,
            turnover_rate=latest.turnover_rate,
            trade_date=latest.date,
        )

    def _build_position_from_kline(
        self,
        kline: KlineResponse,
        code: str,
        window: int,
    ) -> StockPosition:
        bars = [
            SimpleNamespace(
                trade_date=bar.date,
                high=bar.high,
                low=bar.low,
                close=bar.close,
            )
            for bar in kline.bars
        ]
        result = calculate_position_score(bars, window=window)
        if result is None:
            raise HTTPException(status_code=404, detail=f"暂无 {code} 的价格位置数据")

        return StockPosition(
            code=kline.code,
            name=kline.name,
            window=window,
            sample_size=result.sample_size,
            trade_date=result.trade_date,
            latest_close=result.latest_close,
            rolling_low=result.rolling_low,
            rolling_high=result.rolling_high,
            position_score=result.position_score,
            zone=result.zone,
            label=result.label,
        )

    def _validate_position_window(self, window: int) -> None:
        if window not in (250, 750, 1250):
            raise HTTPException(
                status_code=400,
                detail="价格位置窗口仅支持 250、750、1250 个交易日",
            )

    def get_quote(self, code: str, refresh: bool = False) -> StockQuote:
        kline = self.get_kline(code, refresh=refresh)
        return self._build_quote_from_kline(kline, code)

    @classmethod
    def _live_quote_lock_for_code(cls, code: str) -> Lock:
        with cls._live_quote_locks_guard:
            if code not in cls._live_quote_locks:
                cls._live_quote_locks[code] = Lock()
            return cls._live_quote_locks[code]

    def get_live_quote(self, code: str, refresh: bool = False) -> StockQuote:
        self.ensure_stock_catalog()
        stock = self.stock_repo.get_by_code(code)
        if stock is None:
            raise HTTPException(status_code=404, detail=f"未找到股票 {code}")

        lock = self._live_quote_lock_for_code(code)
        with lock:
            cached = self._live_quote_cache.get(code)
            now = datetime.now()
            if not refresh and cached:
                cached_at, cached_quote = cached
                cache_age = (now - cached_at).total_seconds()
                if cache_age <= self._LIVE_QUOTE_TTL_SECONDS:
                    return cached_quote.model_copy(
                        update={
                            "cache_time": cached_at,
                            "is_live": True,
                            "is_stale": False,
                            "cache_age_seconds": cache_age,
                        }
                    )

            try:
                payload = fetch_live_quote(code)
            except (requests.RequestException, RealtimeQuoteDataSourceError) as exc:
                if cached:
                    cached_at, cached_quote = cached
                    cache_age = (now - cached_at).total_seconds()
                    return cached_quote.model_copy(
                        update={
                            "cache_time": cached_at,
                            "is_live": True,
                            "is_stale": True,
                            "cache_age_seconds": cache_age,
                        }
                    )
                raise HTTPException(
                    status_code=503,
                    detail="暂时无法从数据源获取实时行情，请稍后重试。",
                ) from exc

            quote = StockQuote(
                code=stock.code,
                name=payload["name"] or stock.name,
                exchange=stock.exchange,
                latest_price=payload["latest_price"],
                change_amount=payload["change_amount"],
                change_percent=payload["change_percent"],
                open=payload["open"],
                high=payload["high"],
                low=payload["low"],
                pre_close=payload["pre_close"],
                volume=payload["volume"],
                amount=payload["amount"],
                turnover_rate=payload["turnover_rate"],
                trade_date=payload["trade_date"],
                source=payload["source"],
                is_live=True,
                cache_time=now,
                quote_time=payload.get("quote_time"),
                is_stale=False,
                cache_age_seconds=0,
            )
            self._live_quote_cache[code] = (now, quote)
            return quote

    def get_position(
        self,
        code: str,
        window: int = 250,
        refresh: bool = False,
    ) -> StockPosition:
        self._validate_position_window(window)

        end_date = date.today()
        start_date = end_date - timedelta(days=self._position_lookback_days(window))
        kline = self.get_kline(code, start=start_date, end=end_date, refresh=refresh)
        return self._build_position_from_kline(kline, code, window)

    def get_quote_and_position(
        self,
        code: str,
        window: int = 250,
        refresh: bool = False,
    ) -> tuple[StockQuote, StockPosition]:
        self._validate_position_window(window)

        end_date = date.today()
        start_date = end_date - timedelta(days=self._position_lookback_days(window))
        kline = self.get_kline(code, start=start_date, end=end_date, refresh=refresh)
        quote = self._build_quote_from_kline(kline, code)
        position = self._build_position_from_kline(kline, code, window)
        return quote, position

    def _moneyflow_needs_fetch(
        self,
        code: str,
        start_date: date,
        end_date: date,
        *,
        refresh: bool,
        start: date | None,
    ) -> tuple[list, bool]:
        cached = self.moneyflow_repo.get_range(code, start_date, end_date)
        latest_cached_date = cached[-1].trade_date if cached else None
        start_not_covered = (
            start is not None and cached and cached[0].trade_date > start_date
        )
        end_is_stale = (
            latest_cached_date is not None
            and self._cache_end_is_stale(latest_cached_date, end_date)
        )
        needs_fetch = refresh or not cached or start_not_covered or end_is_stale
        return cached, needs_fetch

    def _refresh_moneyflow_cache(
        self,
        code: str,
        exchange: str,
        start_date: date,
        end_date: date,
    ) -> list:
        try:
            frame = fetch_stock_moneyflow(code, exchange)
        except (requests.RequestException, MoneyflowDataSourceError) as exc:
            cached = self.moneyflow_repo.get_range(code, start_date, end_date)
            if not cached:
                raise HTTPException(
                    status_code=503,
                    detail=(
                        "暂时无法从数据源获取资金流数据，"
                        "请检查网络连接后重试。"
                    ),
                ) from exc
            return cached

        if frame.empty:
            cached = self.moneyflow_repo.get_range(code, start_date, end_date)
            return cached or []

        rows = frame.to_dict(orient="records")
        self.moneyflow_repo.replace_range(code, rows)
        return self.moneyflow_repo.get_range(code, start_date, end_date)

    def get_moneyflow(
        self,
        code: str,
        start: date | None = None,
        end: date | None = None,
        refresh: bool = False,
    ) -> MoneyflowResponse:
        self.ensure_stock_catalog()
        stock = self.stock_repo.get_by_code(code)
        if stock is None:
            raise HTTPException(status_code=404, detail=f"未找到股票 {code}")

        end_date = end or date.today()
        start_date = start or (end_date - timedelta(days=365))

        cached, needs_fetch = self._moneyflow_needs_fetch(
            code,
            start_date,
            end_date,
            refresh=refresh,
            start=start,
        )
        if needs_fetch:
            lock = self._fetch_lock_for_code(code, "moneyflow")
            with lock:
                cached, needs_fetch = self._moneyflow_needs_fetch(
                    code,
                    start_date,
                    end_date,
                    refresh=refresh,
                    start=start,
                )
                if needs_fetch:
                    cached = self._refresh_moneyflow_cache(
                        code,
                        stock.exchange,
                        start_date,
                        end_date,
                    )

        bars = [
            MoneyflowBar(
                date=bar.trade_date,
                main_net_inflow=bar.main_net_inflow,
                main_net_ratio=bar.main_net_ratio,
                super_large_net_inflow=bar.super_large_net_inflow,
                large_net_inflow=bar.large_net_inflow,
                medium_net_inflow=bar.medium_net_inflow,
                small_net_inflow=bar.small_net_inflow,
            )
            for bar in cached
        ]

        return MoneyflowResponse(
            code=stock.code,
            name=stock.name,
            source="akshare_em",
            bars=bars,
        )

    def get_latest_moneyflow(self, code: str, refresh: bool = False) -> MoneyflowBar | None:
        response = self.get_moneyflow(code, refresh=refresh)
        if not response.bars:
            return None
        return response.bars[-1]
