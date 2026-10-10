from sqlalchemy import String, JSON, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db import Base
class Receipt(Base):
    __tablename__='event_receipt'
    id: Mapped[str]=mapped_column(String(64),primary_key=True)
    group_id: Mapped[int]=mapped_column(ForeignKey('group.id',ondelete='CASCADE'))
    response: Mapped[dict]=mapped_column(JSON,nullable=False)
    created_at: Mapped[object]=mapped_column(DateTime(timezone=True),server_default=func.now())
