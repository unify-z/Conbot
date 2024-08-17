import asyncio
import psutil
from core import bot
from core.events import *
from core.common import Matcher
from core.messages import Message,MessageSegment
import platform
from core.command import *


async def init():
    
    @bot.on("message")
    async def status(event: MessageEvent, matcher: Matcher):
        raw_msg = event.raw_message
        msg = Message()
        if raw_msg.startswith("/status"):
            cpu_percent = psutil.cpu_percent()
            mem_percent = psutil.virtual_memory().percent
            disk_percent = psutil.disk_usage('/').percent
            msg.append(MessageSegment.text(f"当前Bot运行状态\nCPU使用率：{cpu_percent}% 内存使用率：{mem_percent}%硬盘使用率：{disk_percent}% \nPython版本：{platform.python_version()},Conbot版本:0.0.1"))
        await matcher.finish(msg)
    