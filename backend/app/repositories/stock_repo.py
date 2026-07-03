from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from ..models import Stock


class StockRepository:
    def __init__(self, db: Session):
        self.db = db

    def count(self) -> int:
        return self.db.scalar(select(func.count()).select_from(Stock)) or 0

    def upsert_many(self, rows: list[dict]) -> int:
        if not rows:
            return 0

        codes = [row["code"] for row in rows]
        existing = {
            stock.code: stock
            for stock in self.db.scalars(select(Stock).where(Stock.code.in_(codes))).all()
        }

        inserted = 0
        for row in rows:
            stock = existing.get(row["code"])
            if stock is None:
                self.db.add(Stock(**row))
                inserted += 1
            else:
                stock.name = row["name"]
                stock.exchange = row["exchange"]

        self.db.commit()
        return inserted

    def search(self, keyword: str, limit: int = 20) -> list[Stock]:
        normalized = keyword.strip()
        if not normalized:
            return []

        pattern = f"%{normalized}%"
        query = (
            select(Stock)
            .where(or_(Stock.code.like(pattern), Stock.name.like(pattern)))
            .order_by(Stock.code)
            .limit(limit)
        )
        return list(self.db.scalars(query).all())

    def get_by_code(self, code: str) -> Stock | None:
        return self.db.scalar(select(Stock).where(Stock.code == code))
