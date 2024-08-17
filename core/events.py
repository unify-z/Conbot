from collections import defaultdict
import enum
import inspect
from typing import Any, Type, Union, get_args, get_type_hints
from dataclasses import is_dataclass

from .data import MessageAnonymous, MessageSender
from .messages import Message, MessageSegment

from .data import *

class Event:
    def __init__(self, time: int, self_id: int) -> None:
        self.time = time
        self.self_id = self_id
        from .common import get_bot
        self.get_bot = get_bot
    
    def __repr__(self) -> str:
        return "%s(%s)" % (self.__class__.__name__, ", ".join(f"{k}={repr(getattr(self, k))}" for k in EVENTS_PARAMS[type(self)].keys()))
    
class MessageEvent(Event):
    def __init__(self, time: int, self_id: int, message_id: int, message: Message, raw_message: str, sender: MessageSender) -> None:
        super().__init__(time, self_id)
        self.message_id = message_id
        self.message = message
        self.raw_message = raw_message
        self.sender = sender

class NoticeEvent(Event):
    ...

class RequestEvent(Event):
    ...

class MetaEvent(Event):
    ...


class EventType(enum.Enum):
    MESSAGE = MessageEvent
    NOTICE = NoticeEvent
    REQUEST = RequestEvent
    META_EVENT = MetaEvent

class BotLifeCycleMetaEvent(MetaEvent):
    meta_event_type = "lifecycle"
    def __init__(self, time: int, self_id: int) -> None:
        super().__init__(time, self_id)

class BotConnectLifeCycleMetaEvent(BotLifeCycleMetaEvent):
    sub_type = "connect"
    def __init__(self, time: int, self_id: int) -> None:
        super().__init__(time, self_id)

class BotDisconnectLifeCycleMetaEvent(BotLifeCycleMetaEvent):
    sub_type = "disconnect"
    def __init__(self, time: int, self_id: int) -> None:
        super().__init__(time, self_id)

class BotHeartBeatMetaEvent(MetaEvent):
    meta_event_type = "heartbeat"
    def __init__(self, time: int, self_id: int, status: BotStatus) -> None:
        super().__init__(time, self_id)
        self.status = status

class FriendRequestEvent(RequestEvent):
    request_type = "friend"
    def __init__(self, time: int, self_id: int, user_id: int, comment: str, flag: str) -> None:
        super().__init__(time, self_id)
        self.user_id = user_id
        self.comment = comment
        self.flag = flag
    
    async def approve(self, remark: str = ""):
        await self.get_bot(self.self_id).approve_friend(self.flag, remark)

    async def reject(self):
        await self.get_bot(self.self_id).reject_friend(self.flag)

class GroupRequestEvent(RequestEvent):
    request_type = "group"
    def __init__(self, time: int, self_id: int, group_id: int, user_id: int, flag: str) -> None:
        super().__init__(time, self_id)
        self.group_id = group_id
        self.user_id = user_id
        self.flag = flag

    async def approve(self):
        sub_type = getattr(type(self), "sub_type", None)
        if not sub_type:
            return
        await self.get_bot(self.self_id).approve_group(self.flag, sub_type)

    async def reject(self, reason: str = ""):
        sub_type = getattr(type(self), "sub_type", None)
        if not sub_type:
            return
        await self.get_bot(self.self_id).reject_group(self.flag, sub_type, reason)

class GroupAddRequestEvent(GroupRequestEvent):
    sub_type = "add"
    def __init__(self, time: int, self_id: int, group_id: int, user_id: int, flag: str, comment: str) -> None:
        super().__init__(time, self_id, group_id, user_id, flag)
        self.comment = comment
    
class GroupInviteRequestEvent(GroupRequestEvent):
    sub_type = "invite"
    
class PrivateMessageEvent(MessageEvent):
    message_type = "private"
    def __init__(self, time: int, self_id: int, message_id: int, message: Message, raw_message: str, sender: MessageSender, user_id: int) -> None:
        super().__init__(time, self_id, message_id, message, raw_message, sender)
        self.user_id = user_id

class PrivateFriendMessageEvent(PrivateMessageEvent):
    sub_type = "friend"
    
class PrivateGroupMessageEvent(PrivateMessageEvent):
    sub_type = "group"
    
class PrivateOtherMessageEvent(PrivateMessageEvent):
    sub_type = "other"
    
class GroupMessageEvent(MessageEvent):
    message_type = "group"
    sub_type = "normal"
    def __init__(self, time: int, self_id: int, message_id: int, message: Message, raw_message: str, sender: MessageSender, group_id: int, user_id: int) -> None:
        super().__init__(time, self_id, message_id, message, raw_message, sender)
        self.group_id = group_id
        self.user_id = user_id
        

class GroupNoticeMessageEvent(GroupMessageEvent):
    sub_type = "notice"
class GroupAnonymousMessageEvent(GroupMessageEvent):
    sub_type = "anonymous"
    def __init__(self, time: int, self_id: int, message_id: int, message: Message, raw_message: str, sender: MessageSender, group_id: int, user_id: int, anonymous: MessageAnonymous) -> None:
        super().__init__(time, self_id, message_id, message, raw_message, sender, group_id, user_id)
        self.anonymous = anonymous

class GroupNoticeEvent(NoticeEvent):
    def __init__(self, time: int, self_id: int, group_id: int, user_id: int) -> None:
        super().__init__(time, self_id)
        self.group_id = group_id
        self.user_id = user_id

class GroupUploadNoticeEvent(GroupNoticeEvent):
    notice_type = "group_upload"
    def __init__(self, time: int, self_id: int, group_id: int, user_id: int, file: GroupUploadFile) -> None:
        super().__init__(time, self_id, group_id, user_id)
        self.file = file

class GroupAdminNoticeEvent(GroupNoticeEvent):
    notice_type = "group_admin"
    def __init__(self, time: int, self_id: int, group_id: int, user_id: int) -> None:
        super().__init__(time, self_id, group_id, user_id)

class GroupAdminSetNoticeEvent(GroupAdminNoticeEvent):
    sub_type = "set"

class GroupAdminUnsetNoticeEvent(GroupAdminNoticeEvent):
    sub_type = "unset"

class GroupMemberNoticeEvent(GroupNoticeEvent):
    def __init__(self, time: int, self_id: int, group_id: int, user_id: int, operator_id: int) -> None:
        super().__init__(time, self_id, group_id, user_id)
        self.operator_id = operator_id

class GroupDecreaseNoticeEvent(GroupMemberNoticeEvent):
    notice_type = "group_decrease"

class GroupDecreaseLeaveNoticeEvent(GroupDecreaseNoticeEvent):
    sub_type = "leave"

class GroupDecreaseKickNoticeEvent(GroupDecreaseNoticeEvent):
    sub_type = "kick"

class GroupDecreaseKickMeNoticeEvent(GroupDecreaseNoticeEvent):
    sub_type = "kick_me"

class GroupIncreaseNoticeEvent(GroupMemberNoticeEvent):
    notice_type = "group_increase"

class GroupIncreaseApproveNoticeEvent(GroupMemberNoticeEvent):
    sub_type = "approve"

class GroupIncreaseInviteNoticeEvent(GroupMemberNoticeEvent):
    sub_type = "invite"

class GroupBanNoticeEvent(GroupMemberNoticeEvent):
    notice_type = "group_ban"
    def __init__(self, time: int, self_id: int, group_id: int, user_id: int, operator_id: int, duration: int) -> None:
        super().__init__(time, self_id, group_id, user_id, operator_id)
        self.duration = duration
class GroupBanMemberNoticeEvent(GroupBanNoticeEvent):
    sub_type = "ban"

class GroupiftBanLiftMemberNoticeEvent(GroupBanNoticeEvent):
    sub_type = "lift_ban"

class MessageRecallNoticeEvent(NoticeEvent):
    def __init__(self, time: int, self_id: int, user_id: int, message_id: int) -> None:
        super().__init__(time, self_id)
        self.user_id = user_id
        self.message_id = message_id

class GroupMessageRecallNoticeEvent(MessageRecallNoticeEvent):
    notice_type = "group_recall"
    def __init__(self, time: int, self_id: int, user_id: int, message_id: int, group_id: int, operator_id: int) -> None:
        super().__init__(time, self_id, user_id, message_id)
        self.operator_id = operator_id
        self.group_id = group_id

class FriendMessageRecallNoticeEvent(MessageRecallNoticeEvent):
    notice_type = "friend-recall"
    def __init__(self, time: int, self_id: int, user_id: int, message_id: int, target_id: int) -> None:
        super().__init__(time, self_id, user_id, message_id)
        self.target_id = target_id

RAW_EVENTS: dict[str, Type[Event]] = {
    "message": MessageEvent,
    "notice": NoticeEvent,
    "request": RequestEvent,
    "meta_event": MetaEvent
}
EVENTS: defaultdict[Type[Event], dict[Type[Event], tuple[Type[Event], ...]]] = defaultdict(defaultdict)
EVENTS_TYPES: defaultdict[Type[Event], dict[str, Any]] = defaultdict(dict)
EVENTS_PARAMS: defaultdict[Type[Event], dict[str, Type]] = defaultdict(dict)
EVENTS_RAW: defaultdict[Type[Event], Type[Event]] = defaultdict()
def parse_event(data: dict):
    post_type = data["post_type"]
    if post_type == "message_sent":
        post_type = "message"
    base_event = RAW_EVENTS.get(post_type, None)
    events = EVENTS.get(base_event, None) # type: ignore
    instance_events: list[Event] = []
    if base_event is None or events is None:
        return instance_events
    for event in events:
        if not all((data[k] == v for k, v in EVENTS_TYPES[event].items() if k in data)):
            continue
        event_params = EVENTS_PARAMS[event]
        params: dict[str, Any] = {}
        for name, annotation in event_params.items():
            if name not in data:
                continue
            params[name] = parse_params(data[name], annotation)
        if len(params) != len(event_params):
            continue
        instance = event(**params)
        instance_events.append(instance)
    return instance_events

def parse_params(params: Any, annotation: Type):
    if annotation is Message:
        return MessageSegment.from_json(params)
    if is_dataclass(annotation):
        for k, v in inspect.signature(annotation).parameters.items():
            if k not in params and type(None) in _get_annotations(v.annotation):
                params[k] = None
        return annotation(**params)
    return params
    
def _get_annotations(value: Any):
    if hasattr(value, "__origin__") and value.__origin__ is Union:
        return list(get_args(value))
    return [value]

frame = inspect.currentframe()
module = inspect.getmodule(frame)
classes = inspect.getmembers(module, inspect.isclass)
cls: Type[Event]
for name, cls in classes:
    if not name.endswith("Event"):
        continue
    supers = inspect.getmro(cls)[1:-2]
    if not supers:
        continue
    if supers[-1] in list(RAW_EVENTS.values()):
        EVENTS[supers[-1]][cls] = supers[:-1]
        EVENTS_RAW[cls] = supers[-1]
    EVENTS_TYPES[cls] = dict(filter(lambda x: (not (x[0].lower().startswith("__") and x[0].lower().endswith("__"))), inspect.getmembers(cls, lambda x: not inspect.isroutine(x))))
    EVENTS_PARAMS[cls] = {k: v.annotation for k, v in inspect.signature(cls).parameters.items()}