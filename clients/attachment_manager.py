import base64
import aiofiles
import aiohttp
from typing import Optional, Dict, Any

from clients.http_client import HTTPClient
from utils.logging_setup import logger


class AttachmentManager:
    def __init__(self, signal_service: str, save_attachments: bool, attachment_path:str="./files/attachments/"):
        self.signal_service = signal_service
        self.attachment_base_url = f"http://{signal_service}/v1/attachments"
        self.save_attachments = save_attachments
        self.attachment_path = attachment_path

    async def handle_attachment(self, attachment):
        attachment_id = attachment.get("id")
        if attachment_id:
            data = await self._get_attachment(attachment_id)
            if self.save_attachments and data:
                await self._save_attachment(attachment, data)
            return attachment_id, data 

    async def _get_attachment(self, attachment_id: str) -> Optional[str]:
        uri = f"{self.attachment_base_url}/{attachment_id}"
        
        try:
            content = await HTTPClient.get(uri)
            if content:
                return base64.b64encode(content).decode("utf-8")
            return None
        except Exception as e:
            logger.error(f"Error retrieving attachment: {e}")
            return None
    
    async def upload_attachment(self, attachment: Dict[str, Any]) -> Optional[str]:
        try:
            binary_data = base64.b64decode(attachment["data"])
            
            form_data = aiohttp.FormData()
            form_data.add_field(
                "attachment",
                binary_data,
                filename=attachment.get("filename", "image.jpg"),
                content_type=attachment.get("content_type", "image/jpeg")
            )
            
            response = await HTTPClient.post(self.attachment_base_url, form_data=form_data)
            if response and "id" in response:
                return response["id"]
            return None
        except Exception as e:
            logger.error(f"Error uploading attachment: {e}")
            return None

    async def _save_attachment(self, attachment:Dict[str, Any], data) -> None:
        if attachment:
            filepath = f"{self.attachment_path}{attachment.get('id')}"
            try:
                binary_data = base64.b64decode(data)
                async with aiofiles.open(filepath, "wb") as out:
                    await out.write(binary_data)
                    await out.flush()
            except Exception as e:
                logger.error(f"Failed to save attachment: {e}")