from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class MoneyflowDaily(Base):
    __tablename__ = "moneyflow_daily"
    __table_args__ = (
        UniqueConstraint("code", "trade_date", name="uq_moneyflow_code_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(10), index=True, nullable=False)
    trade_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    main_net_inflow: Mapped[float] = mapped_column(Float, nullable=False)
    main_net_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    super_large_net_inflow: Mapped[float | None] = mapped_column(Float, nullable=True)
    large_net_inflow: Mapped[float | None] = mapped_column(Float, nullable=True)
    medium_net_inflow: Mapped[float | None] = mapped_column(Float, nullable=True)
    small_net_inflow: Mapped[float | None] = mapped_column(Float, nullable=True)
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="akshare_em")
    update_time: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
