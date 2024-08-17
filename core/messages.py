from dataclasses import dataclass
import inspect
import json
from typing import Any


CQ_TABLES = {
    "&": "&amp;",
    "[": "&#91;",
    "]": "&#93;",
    ",": "&#44;"
}

@dataclass
class BaseMessage:
    type: str
    data: dict[str, Any]

    def cq(self):
        if self.type == "text":
            return escape_message(self.data["text"])
        else:
            return f'[CQ:{self.type},{",".join((f"{k}={escape_message(v)}" for k, v in self.data))}]'
    def json(self):
        return {
            "type": self.type,
            "data": self.data
        }

class Message(list[BaseMessage]):
    def json(self):
        return [v.json() for v in self]

    def cq(self):
        return ''.join((v.cq() for v in self))
    
    def append(self, object: Any) -> 'Message':
        if isinstance(object, Message):
            self.union(object)
            return self
        super().append(object)
        return self
    
    def append_message(self, type: str, data: dict[str, Any]) -> 'Message':
        return self.append(BaseMessage(type, data))
    
    def union(self, *s: 'Message'):
        for msg in s:
            for base_message in msg:
                self.append(base_message)
        return self

    @staticmethod
    def build():
        return Message()
    

class MessageSegment:

    def __init__(self) -> None:
        self.messages: Message = Message()

    def __getattr__(self, name: str):
        if name in MESSAGESEGMENT_STATICMETHODS:
            segment: Message = getattr(self.__class__, name)
            self.messages.union(segment)
            return self
        return getattr(self, name)
    
    @staticmethod
    def text(text):
        return Message.build().append_message(
            "text", {"text": text}
        )
    
    @staticmethod
    def at(qq: int):
        return Message.build().append_message(
            "at", {"qq": qq}
        )
    
    @staticmethod
    def reply(id: int):
        return Message.build().append_message(
            "reply", {"reply": id}
        )
    
    @staticmethod
    def from_json(msg: list[dict[str, Any]]):
        array = Message.build()
        for message in msg:
            array.append_message(**message)
        return array
    

MESSAGESEGMENT_STATICMETHODS = list(filter(lambda x: x not in ("from_json"), (v[0] for v in inspect.getmembers_static(MessageSegment, lambda obj: isinstance(obj, staticmethod)))))

def escape_message(value: str):
    for k, v in CQ_TABLES.items():
        value = value.replace(k, v)
    return value

def unescape_message(value: str):
    for k, v in CQ_TABLES.items():
        value = value.replace(v, k)
    return value