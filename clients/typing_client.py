import asyncio
from typing import Dict
from clients.http_client import HTTPClient
from utils.logging_setup import logger


class TypingClient:
    def __init__(self, signal_service: str, phone_number: str, refresh_interval: int = 10):
        self.signal_service = signal_service
        self.phone_number = phone_number
        self._uri = f"http://{self.signal_service}/v1/typing-indicator/{self.phone_number}"
        self.refresh_interval = refresh_interval
        self._typing_tasks: Dict[str, asyncio.Task] = {}
    
    async def start_typing(self, recipient: str) -> None:
        # Stop previous tasks
        await self.stop_typing(recipient)
        # Create task to periodically send typing indicator
        self._typing_tasks[recipient] = asyncio.create_task(
            self._maintain_typing_indicator(recipient)
        )

    async def stop_typing(self, recipient: str) -> None:
        if recipient in self._typing_tasks:
            self._typing_tasks[recipient].cancel()
            try:
                await self._typing_tasks[recipient]
            except asyncio.CancelledError:
                pass
            del self._typing_tasks[recipient]
        
        await self._send_stop_typing(recipient)

    async def _maintain_typing_indicator(self, recipient: str) -> None:
        try:
            while True:
                await self._send_start_typing(recipient)
                await asyncio.sleep(self.refresh_interval)
        except asyncio.CancelledError:
            await self._send_stop_typing(recipient)
            raise
    
    async def _send_start_typing(self, recipient: str) -> None:
        payload = {"recipient": recipient}
        result = await HTTPClient.put(self._uri, payload)
        if not result:
            logger.error(f"Failed to send typing indicator to {recipient}")
    
    async def _send_stop_typing(self, recipient: str) -> None:
        payload = {"recipient": recipient}
        result = await HTTPClient.delete(self._uri, payload)
        if not result:
            logger.error(f"Failed to stop typing indicator for {recipient}")
    
    # Force cancel
    def cancel_all_typing(self) -> None:
        for task in self._typing_tasks.values():
            if not task.done():
                task.cancel()
        self._typing_tasks.clear()
    
    # Ask to cancel
    async def close(self) -> None:
        recipients = list(self._typing_tasks.keys())
        for recipient in recipients:
            await self.stop_typing(recipient)
