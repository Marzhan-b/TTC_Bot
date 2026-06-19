import os
from sqlalchemy.ext.asyncio import create_async_engine,AsyncSession
from sqlalchemy.orm import declarative_base,sessionmaker
from sqlalchemy import Column,Integer,String,Boolean,DateTime
from datetime import datetime


DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:1234@localhost:5432/network_monitor")
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
engine = create_async_engine(DATABASE_URL,echo=False)

async_session=sessionmaker(
    engine,class_=AsyncSession,expire_on_commit=False
)

Base=declarative_base()

class PingLog(Base):
    __tablename__="ping_logs"

    id = Column(Integer,primary_key=True)
    region=Column(String)
    city=Column(String)
    node_name=Column(String)
    ip=Column(String)
    is_online=Column(Boolean)
    response_time=Column(String)
    checked_at=Column(DateTime,default=datetime.now)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database is done!")
