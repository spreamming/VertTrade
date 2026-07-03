from datetime import date

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ..models import MoneyflowDaily


class MoneyflowRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_range(
        self,
        code: str,
        start: date | None = None,
        end: date | None = None,
    ) -> list[MoneyflowDaily]:
        query = select(MoneyflowDaily).where(MoneyflowDaily.code == code)
        if start is not None:
            query = query.where(MoneyflowDaily.trade_date >= start)
        if end is not None:
            query = query.where(MoneyflowDaily.trade_date <= end)
        query = query.order_by(MoneyflowDaily.trade_date)
        return list(self.db.scalars(query).all())

    def get_latest(self, code: str) -> MoneyflowDaily | None:
        query = (
            select(MoneyflowDaily)
            .where(MoneyflowDaily.code == code)
            .order_by(MoneyflowDaily.trade_date.desc())
            .limit(1)
        )
        return self.db.scalar(query)

    def replace_range(self, code: str, rows: list[dict]) -> int:
        if not rows:
            return 0

        dates = [row["trade_date"] for row in rows]
        self.db.execute(
            delete(MoneyflowDaily).where(
                MoneyflowDaily.code == code,
                MoneyflowDaily.trade_date.in_(dates),
            )
        )

        for row in rows:
            self.db.add(MoneyflowDaily(code=code, source="akshare_em", **row))

        self.db.commit()
        return len(rows)
