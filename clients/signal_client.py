import json
import time
import traceback
from typing import Dict, Any, Optional, List

from clients.http_client import HTTPClient
from clients.websocket_client import WebsocketClient
from clients.attachment_manager import AttachmentManager
from clients.typing_client import TypingClient
from commands.command_manager import CommandManager
from memory.memory_manager import MemoryManager
from utils.logging_setup import logger


class SignalClient:
    def __init__(self, signal_service: str, phone_number: str, save_attachments: bool, llm_client, 
                 memory_manager: MemoryManager, typing_client: TypingClient,
                 command_manager: Optional[CommandManager] = None):
        self.signal_service = signal_service
        self.phone_number = phone_number
        self.llm_client = llm_client
        self.memory_manager = memory_manager
        self.typing_client = typing_client
        self.command_manager = command_manager or CommandManager()
        self.attachment_manager = AttachmentManager(signal_service, save_attachments)
        
        # Create WebSocket client
        ws_uri = f"ws://{self.signal_service}/v1/receive/{self.phone_number}"
        self.websocket_client = WebsocketClient(ws_uri, self._handle_message)
    
    async def start(self) -> None:
        logger.info("Starting Signal API Relay service...")
        await self.websocket_client.connect(ping_interval=None)
    
    async def _handle_message(self, raw_message: str) -> None:
        try:
            message = await self._parse_message(raw_message)
            if not message:
                return
            
            if not message.get("text") and not message.get("attachments"):
                return
            
            text = message.get("text", "")
            if self.command_manager and await self.command_manager.handle_command(text):
                return
            
            recipient = message.get("recipient")


            # Start typing
            await self.typing_client.start_typing(recipient)
            
            try:
                # Forward to LLM
                response = await self.llm_client.process_message(message, recipient)
                
                # Stop typing
                await self.typing_client.stop_typing(recipient)
                
                # Send response back
                if response:
                    await self._send_signal_response(recipient, response)
            except Exception as e:
                await self.typing_client.close()
                logger.error(f"Error processing message with LLM: {e}")
                logger.debug(traceback.format_exc())
                
        except Exception as e:
            logger.error(f"Error in message handling: {e}")
            logger.debug(traceback.format_exc())
    
    async def _parse_message(self, raw_message: str) -> Optional[Dict[str, Any]]:
        try:
            data = json.loads(raw_message)
            envelope = data.get("envelope", {})
            
            result = {
                "source": envelope.get("source"),
                "source_uuid": envelope.get("sourceUuid"),
                "timestamp": envelope.get("timestamp"),
                "attachments": []
            }
            
            # Get recipient for reply
            if "dataMessage" in envelope and "groupInfo" in envelope["dataMessage"]:
                result["recipient"] = envelope["dataMessage"]["groupInfo"]["groupId"]
            else:
                result["recipient"] = envelope.get("source")
            
            message_data = None
            if "dataMessage" in envelope:
                message_data = envelope["dataMessage"]
                result["type"] = "data_message"
            elif "syncMessage" in envelope and "sentMessage" in envelope["syncMessage"]:
                message_data = envelope["syncMessage"]["sentMessage"]
                result["type"] = "sync_message"
            else:
                return None
                
            if "message" in message_data:
                result["text"] = message_data["message"]
            
            if "attachments" in message_data and message_data["attachments"]:
                for attachment in message_data["attachments"]:
                    attachment_id, attachment_data = await self.attachment_manager.handle_attachment(attachment)
                    if attachment_data:
                        result["attachments"].append({
                            "id": attachment_id,
                            "content_type": attachment.get("contentType", ""),
                            "filename": attachment.get("filename", ""),
                            "data": attachment_data
                        })
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in message: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to parse message: {e}")
            logger.debug(traceback.format_exc())
            return None
    
    async def _send_signal_response(self, recipient: str, response: Dict[str, Any]) -> None:
        uri = f"http://{self.signal_service}/v2/send"
        
        text = response.get("content", "")
        attachments = response.get("attachments", [])

        payload = {
            "message": text,
            "number": self.phone_number,
            "recipients": [recipient]
        }

        if attachments:
            attachment_ids = []
            for attachment in attachments:
                attachment_id = await self.attachment_manager.upload_attachment(attachment)
                if attachment_id:
                    attachment_ids.append(attachment_id)
            
            if attachment_ids:
                payload["attachments"] = attachment_ids

        await HTTPClient.post(uri, json_data=payload)
