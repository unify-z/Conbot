from typing import Callable, List, Dict
from .events import MessageEvent as event #
from .common import * 




class Command:
    _handlers: List[Dict] = []  

    def __init__(self):
        pass 

    @staticmethod

    def on(command: str):
        pass

    @classmethod
    def register_command(cls, command: str, func: Callable, help_text: str = "", priority: int = 0):
        pass
    @classmethod
    def get_all_commands(cls) :
        pass