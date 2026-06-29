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

async def save_duty_user(chat_id: int):
    async with async_session() as session:
        from backend.database import DutyUser
        existing = await session.execute(
            select(DutyUser).where(DutyUser.chat_id == chat_id)
        )
        if not existing.scalar_one_or_none():
            session.add(DutyUser(chat_id=chat_id))
            await session.commit()

async def get_duty_users() -> list:
    async with async_session() as session:
        from backend.database import DutyUser
        result = await session.execute(select(DutyUser))
        return [row.chat_id for row in result.scalars().all()]

