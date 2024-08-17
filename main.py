import asyncio
import core
import importlib
from core.common import *
from core.events import *
import asyncio
import json
import uvicorn
import logging
from config.config import Config
c = Config()
from fastapi import FastAPI, WebSocket , HTTPException
pluginList = ["obastatus","botstatus"]

async def load_plugins():
    for plugin in pluginList:
        plugin_name = importlib.import_module(f"plugins.{plugin}")
        logging.info(f"加载插件{plugin}中")
        await plugin_name.init()


async def main():
    await core.init()
    await load_plugins()


app = FastAPI()
@app.websocket("/ws/onebot")
async def _(ws: WebSocket):
        await ws.accept()
        while True:
            raw_data = await ws.receive_text()
            data = json.loads(raw_data)
            if "echo" in data:
                MESSAGES[data["echo"]].set_result(True)
                continue
            events: list[Event] = parse_event(data)
            if not events:
                logger.debug(data)
                continue
            bot = get_bot(events[0].self_id)
            bot.ws = ws
            asyncio.create_task(bot.matchers.handle(*events))
           
if __name__ == "__main__":
    asyncio.run(main())
    uvicorn.run(app=app, host=c.ws_host, port=c.ws_port,log_config=None)
