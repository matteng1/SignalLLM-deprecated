from typing import Dict, Callable, Awaitable, Optional
from utils.logging_setup import logger


class CommandManager:
    def __init__(self):
        self.commands: Dict[str, Callable[[], Awaitable[None]]] = {}
    
    def register_command(self, command: str, handler: Callable[[], Awaitable[None]]) -> None:
        self.commands[command] = handler
        logger.info(f"Registered command: {command}")
    
    async def handle_command(self, text: str) -> bool:
        try:
            for command, handler in self.commands.items():
                if text == command:
                    await handler()
                    return True
            return False
        except Exception as e:
            logger.error(f"Error handling command: {e}")
            return False
