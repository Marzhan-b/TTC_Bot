import subprocess
import platform

def ping_host(host:str)->dict:
    system=platform.system().lower()

    if system=="windows":
        command=["ping","-n","3",host]
    else:
        command=["ping","-c","3",host]

    try:
        result=subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=10
        )

        is_alive=result.returncode==0

        output=result.stdout
        avg_time=parse_ping_time(output,system)
        return{
            "host":host,
            "alive":is_alive,
            "avg_time":avg_time,
            "output":output,
        }
    except subprocess.TimeoutExpired:
        return{
            "host": host,
            "alive": False,
            "avg_time": None,
            "output": "Timeout — the host is not responding"
        }
    except Exception as e:
        return{
            "host":host,
            "alive":is_alive,
            "avg_time":avg_time,
            "output":str(e),
        }
def parse_ping_time(output:str,system:str)->str:
    try:
        if system == "windows":
            for line in output.split("\n"):
                if "Average" in line or "Среднее" in line:
                    return line.strip().split("=")[-1].strip()
        else:
            for line in output.split("\n"):
                if "min/avg/max" in line or "rtt" in line:
                    return line.split("/")[1] + "ms"
    except:
        pass
    return "N/A"    


async def check_and_log(node_name: str, ip: str, city: str, region_name: str) -> dict:
    """Пингует один узел и сохраняет результат в базу данных"""
    import asyncio
    from backend.database import async_session, PingLog

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, ping_host, ip)

    async with async_session() as session:
        log = PingLog(
            region=region_name,
            city=city,
            node_name=node_name,
            ip=ip,
            is_online=result["alive"],
            response_time=result["avg_time"] if result["alive"] else None
        )
        session.add(log)
        await session.commit()

    return result
