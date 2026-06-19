from apscheduler.schedulers.asyncio import AsyncIOScheduler
from monitor.checker import ping_host
from monitor.hosts import REGIONS
from backend.database import async_session, PingLog
import asyncio

DUTY_CHAT_ID = None
bot_instance = None

# запоминаем какие узлы уже офлайн чтобы не спамить
offline_nodes = set()

async def check_all_hosts():
    global offline_nodes
    print("🔍 Автопроверка запущена...")
    
    for region_key, region in REGIONS.items():
        for city_name, nodes in region["cities"].items():
            for node_name, ip in nodes.items():
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, ping_host, ip)
                
                print(f"  {node_name} ({ip}) — {'Online' if result['alive'] else 'Offline'}")

                # сохраняем в БД
                async with async_session() as session:
                    log = PingLog(
                        region=region["name"],
                        city=city_name,
                        node_name=node_name,
                        ip=ip,
                        is_online=result["alive"],
                        response_time=result["avg_time"] if result["alive"] else None
                    )
                    session.add(log)
                    await session.commit()

                if not result["alive"]:
                    # уведомляем только если узел только что упал
                    if ip not in offline_nodes and DUTY_CHAT_ID and bot_instance:
                        print(f"  🚨 Отправляю уведомление про {node_name}...")
                        await bot_instance.send_message(
                            DUTY_CHAT_ID,
                            f"🚨 <b>Внимание!</b>\n\n"
                            f"❌ Узел упал!\n"
                            f"📍 {city_name} — {node_name}\n"
                            f"🌐 IP: {ip}",
                            parse_mode="HTML"
                        )
                    offline_nodes.add(ip)
                else:
                    # узел восстановился — убираем из списка и уведомляем
                    if ip in offline_nodes and DUTY_CHAT_ID and bot_instance:
                        print(f"  ✅ {node_name} восстановился!")
                        await bot_instance.send_message(
                            DUTY_CHAT_ID,
                            f"✅ <b>Узел восстановлен!</b>\n\n"
                            f"📍 {city_name} — {node_name}\n"
                            f"🌐 IP: {ip}",
                            parse_mode="HTML"
                        )
                    offline_nodes.discard(ip)

    print("✅ Автопроверка завершена!")

def start_scheduler(bot):
    global bot_instance
    bot_instance = bot

    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_all_hosts, "interval", minutes=5)
    scheduler.start()
    return scheduler