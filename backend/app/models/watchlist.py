from datetime import datetime

from sqlalchemy import DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class WatchlistItem(Base):
    __tablename__ = "watchlist"
    __table_args__ = (UniqueConstraint("code", "group_name", name="uq_watchlist_code_group"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(10), index=True, nullable=False)
    group_name: Mapped[str] = mapped_column(String(32), default="默认")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
