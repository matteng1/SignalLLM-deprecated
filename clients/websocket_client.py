import asyncio
import traceback
import websockets
from typing import Callable, Awaitable, Optional
from utils.logging_setup import logger


class WebsocketClient:
    def __init__(self, url: str, message_handler: Callable[[str], Awaitable[None]]):
        self.url = url
        self.message_handler = message_handler
        self.websocket = None
        self.connected = False
    
    async def connect(self, max_retries=5, ping_interval=None) -> None:
        retry_count = 0
        
        while True:
            try:
                self.websocket = await websockets.connect(self.url, ping_interval=ping_interval)
                self.connected = True
                logger.info(f"Connected to WebSocket at {self.url}")
                await self._listen_for_messages()
                retry_count = 0
            except websockets.exceptions.ConnectionClosed as e:
                logger.error(f"WebSocket connection closed: {e}")
                self.connected = False
                retry_count += 1
            except Exception as e:
                logger.error(f"WebSocket connection error: {e}")
                logger.debug(traceback.format_exc())
                self.connected = False
                retry_count += 1
            
            # Reconnection with exponential backoff
            wait_time = min(30, 2 ** retry_count)
            logger.info(f"Reconnecting in {wait_time} seconds... (Attempt {retry_count}/{max_retries})")
            await asyncio.sleep(wait_time)
            
            if retry_count >= max_retries:
                logger.error(f"Max retries ({max_retries}) exceeded. Waiting 60 seconds before trying again.")
                retry_count = 0
                await asyncio.sleep(60)
    
    async def _listen_for_messages(self) -> None:
        if not self.websocket:
            logger.error("WebSocket not connected")
            return
        
        async for message in self.websocket:
            try:
                await self.message_handler(message)
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
                logger.debug(traceback.format_exc())
    
    async def send(self, message: str) -> bool:
        if not self.websocket or not self.connected:
            logger.error("Cannot send message: WebSocket not connected")
            return False
        
        try:
            await self.websocket.send(message)
            return True
        except Exception as e:
            logger.error(f"Error sending WebSocket message: {e}")
            logger.debug(traceback.format_exc())
            return False
    
    async def close(self) -> None:
        if self.websocket and self.connected:
            try:
                await self.websocket.close()
                self.connected = False
                logger.info("WebSocket connection closed")
            except Exception as e:
                logger.error(f"Error closing WebSocket connection: {e}")
                logger.debug(traceback.format_exc())
