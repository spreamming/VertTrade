from datetime import date

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ..models import KlineDaily


class KlineRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_range(
        self,
        code: str,
        start: date | None = None,
        end: date | None = None,
    ) -> list[KlineDaily]:
        query = select(KlineDaily).where(KlineDaily.code == code)
        if start is not None:
            query = query.where(KlineDaily.trade_date >= start)
        if end is not None:
            query = query.where(KlineDaily.trade_date <= end)
        query = query.order_by(KlineDaily.trade_date)
        return list(self.db.scalars(query).all())

    def replace_range(self, code: str, rows: list[dict]) -> int:
        if not rows:
            return 0

        dates = [row["trade_date"] for row in rows]
        self.db.execute(
            delete(KlineDaily).where(
                KlineDaily.code == code,
                KlineDaily.trade_date.in_(dates),
            )
        )

        for row in rows:
            self.db.add(KlineDaily(code=code, **row))

        self.db.commit()
        return len(rows)

    def get_latest(self, code: str) -> KlineDaily | None:
        query = (
            select(KlineDaily)
            .where(KlineDaily.code == code)
            .order_by(KlineDaily.trade_date.desc())
            .limit(1)
        )
        return self.db.scalar(query)
