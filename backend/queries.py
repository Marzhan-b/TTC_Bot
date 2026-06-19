from sqlalchemy import select,desc
from backend.database import async_session,PingLog

async def get_last_checks(limit:int=10):
    async with async_session() as session:
        result = await session.execute(
            select(PingLog)
            .order_by(desc(PingLog.checked_at))
            .limit(limit)
        )
        return result.scalars().all()
    
async def get_offline_hosts(limit:int=10):
    async with async_session() as session:
        result=await session.execute(
            select(PingLog)
            .where(PingLog.is_online==False)
            .order_by(desc(PingLog.checked_at))
            .limit(limit)
        )
        return result.scalars().all()



