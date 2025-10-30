from __future__ import annotations

from sqlalchemy import Column, BigInteger, Integer, Text, ForeignKey

from ..db.base import Base


class TopicRow(Base):
    __tablename__ = "topics"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)
    parent_topic_id = Column(BigInteger, ForeignKey("topics.id", onupdate="CASCADE", ondelete="SET NULL"), nullable=True)
    org_id = Column(Integer, nullable=True)  # NULL means global topic
