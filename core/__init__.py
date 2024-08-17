import asyncio
from .events import *
from .common import *
from main import *
import logging as logger
from config.config import Config
c = Config()
bot = get_bot(id=c.self_id)
logging.basicConfig(level=logger.INFO, format='[%(asctime)s][%(levelname)s][%(name)s]: %(message)s')

async def init():
    logger.info("初始化中")
    @bot.on("message")
    async def _(event: MessageEvent):
        if isinstance(event, PrivateMessageEvent):
            logger.info(f"收到私聊消息({event.message_id}):发送者:{event.sender.user_id}({event.sender.nickname}), 内容:{event.raw_message}")
        if isinstance(event, GroupMessageEvent):
            logger.info(f"收到群聊消息({event.message_id}):群:{event.group_id}, 发送者:{event.sender.nickname}({event.sender.user_id}), 内容:{event.raw_message}")
    @bot.on("meta_event")
    async def _(Event: BotHeartBeatMetaEvent,event: BotLifeCycleMetaEvent):
        if isinstance(Event, BotHeartBeatMetaEvent):
            logger.info(f"保活成功 [time:{Event.time},self_id:{Event.self_id},status:{Event.status.online}]")
        if isinstance(event, BotConnectLifeCycleMetaEvent):
            logger.info(f"Bot已连接 [time:{event.time},self_id:{event.self_id}]")
        if isinstance(event, BotDisconnectLifeCycleMetaEvent):
            logger.info(f"Bot断开连接 [time:{event.time},self_id:{event.self_id}]")