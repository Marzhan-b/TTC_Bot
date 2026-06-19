import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from backend.database import init_db

asyncio.run(init_db())