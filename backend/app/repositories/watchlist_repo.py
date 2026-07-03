from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from ..models import WatchlistItem


class WatchlistRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_items(self, group_name: str | None = None) -> list[WatchlistItem]:
        query = select(WatchlistItem)
        if group_name:
            query = query.where(WatchlistItem.group_name == group_name)
        query = query.order_by(WatchlistItem.sort_order, WatchlistItem.created_at)
        return list(self.db.scalars(query).all())

    def count(self) -> int:
        return self.db.scalar(select(func.count()).select_from(WatchlistItem)) or 0

    def get_by_id(self, item_id: int) -> WatchlistItem | None:
        return self.db.get(WatchlistItem, item_id)

    def get_by_code_group(self, code: str, group_name: str) -> WatchlistItem | None:
        query = select(WatchlistItem).where(
            WatchlistItem.code == code,
            WatchlistItem.group_name == group_name,
        )
        return self.db.scalar(query)

    def add(self, code: str, group_name: str = "默认", note: str | None = None) -> WatchlistItem:
        existing = self.get_by_code_group(code, group_name)
        if existing:
            if note is not None:
                existing.note = note
                self.db.commit()
                self.db.refresh(existing)
            return existing

        sort_order = self._next_sort_order(group_name)
        item = WatchlistItem(
            code=code,
            group_name=group_name,
            sort_order=sort_order,
            note=note,
        )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def delete(self, item_id: int) -> bool:
        result = self.db.execute(delete(WatchlistItem).where(WatchlistItem.id == item_id))
        self.db.commit()
        return result.rowcount > 0

    def _next_sort_order(self, group_name: str) -> int:
        current_max = self.db.scalar(
            select(func.max(WatchlistItem.sort_order)).where(
                WatchlistItem.group_name == group_name
            )
        )
        return (current_max or 0) + 1
