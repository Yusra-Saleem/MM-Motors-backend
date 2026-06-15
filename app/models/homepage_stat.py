from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class HomepageStat(Base):
    __tablename__ = "homepage_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    value: Mapped[str] = mapped_column(String(50), nullable=False)
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    icon: Mapped[str] = mapped_column(String(50), nullable=False, default="Car")
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
