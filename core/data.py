from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class BotStatus:
    good: bool
    online: bool

@dataclass
class MessageSender:
    user_id: int
    nickname: Optional[str]
    sex: Optional[str]
    age: Optional[int]
    area: Optional[str]
    level: Optional[str]
    role: Optional[str]
    title: Optional[str]
    card: Optional[str]

@dataclass
class MessageAnonymous:
    id: int
    name: str
    flag: str

@dataclass
class GroupUploadFile:
    id: str
    name: str
    size: int
    busid: int