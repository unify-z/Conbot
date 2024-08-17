import asyncio
from collections import defaultdict
from dataclasses import dataclass
import inspect
import json
import traceback
from typing import Any, Callable, Coroutine, List, Optional, Type, Union, get_args, get_type_hints
import uuid
from fastapi import WebSocket
from .messages import Message
from .events import *
from loguru import logger
import logging

MESSAGES: dict[str, asyncio.Future] = {}

class Bot:
    def __init__(self, id: int) -> None:
        self.id = id
        self.matchers = MatcherManager(self)
        self.ws: Optional[WebSocket] = None

    def on(self, event_name: str):
        return self.matchers.on(event_name)
    
    def send_group_msg(self, group_id: int, message: Message):
        frames = inspect.stack()
        return self.action(frames[0].function, {
            "group_id": group_id,
            "message": message.json()
        })
    
    def send_private_msg(self, user_id: int, message: Message):
        frames = inspect.stack()
        return self.action(frames[0].function, {
            "user_id": user_id,
            "message": message.json()
        })

    def approve_friend(self, flag: str, remark: str = ""):
        return self.action("set_friend_add_request", {
            "flag": flag,
            "approve": True,
            "remark": remark
        })
    
    def reject_friend(self, flag: str):
        return self.action("set_friend_add_request", {
            "flag": flag,
            "approve": True,
        })

    def approve_group(self, flag: str, sub_type: str):
        return self.action("set_group_add_request", {
            "flag": flag,
            "type": sub_type,
            "approve": True,
        })
    
    def reject_group(self, flag: str, sub_type: str, reason: str = ""):
        return self.action("set_group_add_request", {
            "flag": flag,
            "type": sub_type,
            "approve": False,
            "reason": reason
        })
    
    async def action(self, action: str, params: dict[str, Any]) -> Optional[Any]:
        if not self.ws:
            raise ValueError("WebSocket not connected")
        echo = str(uuid.uuid4())
        data = {
        "action": action,
        "params": params,
        "echo": echo
    }
        text_data: str = json.dumps(data)
        websocket_message: dict[str, str] = {
        "type": "websocket.send",
        "text": text_data
    }
        await self.ws.send(websocket_message)  
        if data["params"].get("message") == []:
            pass
        else:
            logging.info(f"发送数据:类型:{action},参数:{params},echo:{echo}")
        MESSAGES[echo] = asyncio.get_event_loop().create_future()
        try:
            await MESSAGES[echo]
        except:
            ...
        result = None
        if MESSAGES[echo].done():
            result = MESSAGES[echo].result()
            MESSAGES.pop(echo)
        return result

class StopMatcher(Exception):
    ...

class Matcher:
    def __init__(self, event: Event, bot: Bot) -> None:
        self.event = event
        self.bot = bot
        self._finished = False
        if isinstance(self.event, MessageEvent):
            if isinstance(self.event, GroupMessageEvent):
                self._send_target = self.event.group_id
                self._send = self.bot.send_group_msg
            elif isinstance(self.event, PrivateMessageEvent):
                self._send_target = self.event.user_id
                self._send = self.bot.send_private_msg
        elif isinstance(self.event, (GroupAddRequestEvent, GroupInviteRequestEvent, FriendRequestEvent)):
            self.approve = self.event.approve
            self.reject = self.event.reject
    async def send(self, msg: Message):
        frame = inspect.stack()[0]
        if hasattr(self, f"_{frame.function}"):
            return await self._send(self._send_target, msg)

    async def finish(self, msg: Optional[Message] = None):
        self._finished = True
        if msg is not None:
            await self.send(msg)
        raise StopMatcher


@dataclass  
class MessageHandlerArg:  
    name: str  
    type_annotation: list[Any]  # 使用type_annotation代替type，以避免混淆  
    default: Any = inspect._empty 

class MessageHandlerArgs:  
    def __init__(self, handler) -> None:  
        self.handler = handler
        self.handler_args = inspect.getfullargspec(handler)  
        annotations_params = get_type_hints(handler)  
        defaults = self.handler_args.defaults or ()
        offset = len(self.handler_args.args) - len(defaults)
        self.route_handler_args = [  
            MessageHandlerArg(name=param, type_annotation=self._get_annotations(annotations_params.get(param, Any)), default=defaults[i - offset] if i - offset >= 0 else inspect._empty)  
            for i, param in enumerate(self.handler_args.args)  
        ]  
        self.return_annotation = self.handler_args.annotations.get("return", Any)

    def _get_annotations(self, value: Any):
        if hasattr(value, "__origin__") and value.__origin__ is Union:
            return list(get_args(value))
        return [value]

    def __str__(self) -> str:
        return f"<{self.handler}: {self.route_handler_args}>"

@dataclass
class MessageHandler:
    func: Callable[..., Any | Coroutine[Any, Any, Any]]
    params: MessageHandlerArgs
    priority: int = 0

class MatcherManager:
    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.handlers: defaultdict[Type[Event], list[MessageHandler]] = defaultdict(list)

    def on(self, event_name: str, priority: int = 0):
        def wrapper(func):
            event = RAW_EVENTS[event_name.lower()]
            if event is None:
                raise KeyError(f"Unknown event {event_name}")
            self.handlers[event].append(MessageHandler(
                func,
                params=MessageHandlerArgs(func),
                priority=priority
            ))
            self.handlers[event].sort(key=lambda x: x.priority, reverse=True)
            return func
        return wrapper
    
    async def handle(self, *data: Event):
        for event in data:
            matcher = Matcher(event, self.bot)
            event_type = EVENTS_RAW.get(type(event))
            if event_type is None:
                continue
            handlers = self.handlers.get(event_type)
            if not handlers:
                continue
            for handler in handlers:
                func_args = {}
                for params in handler.params.route_handler_args:
                    if Bot in params.type_annotation:
                        func_args[params.name] = self.bot
                    if Matcher in params.type_annotation:
                        func_args[params.name] = matcher
                    if Event in params.type_annotation:
                        func_args[params.name] = event
                    if type(event) in params.type_annotation:
                        func_args[params.name] = event
                    if params.name not in func_args and isinstance(event, tuple(set(EVENTS[event_type].items()))):
                        func_args[params.name] = event
                if len(func_args.keys()) != len(handler.params.route_handler_args):
                    continue
                try:
                    if asyncio.iscoroutinefunction(handler.func):
                        await handler.func(**func_args)
                    else:
                        handler.func(**func_args)
                except StopMatcher:
                    continue
                except:
                    logger.debug(traceback.format_exc())
                if matcher._finished:
                    break
            if matcher._finished:
                break

        


BOTS: dict[int, Bot] = {}

def get_bot(id: int):
    if id not in BOTS:
        BOTS[id] = Bot(id)
    return BOTS[id]