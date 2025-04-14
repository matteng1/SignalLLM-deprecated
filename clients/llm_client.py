import traceback
from typing import Dict, Any, Optional, List

from clients.http_client import HTTPClient
from clients.llm.base import LLMServiceFactory
from memory.memory_manager import MemoryManager
from utils.logging_setup import logger


class LLMClient:
    def __init__(self, llm_service_url: str, llm_api_key: str, llm_model_options: Dict[str, Any],
                 memory_manager: MemoryManager, typing_client, llm_service_provider: str):
        self.llm_service_url = llm_service_url
        self.llm_api_key = llm_api_key
        self.llm_model_options = llm_model_options
        self.memory_manager = memory_manager
        self.typing_client = typing_client
        self.service_adapter = LLMServiceFactory.get_adapter(
            llm_service_provider, llm_service_url, llm_model_options
        )
        
        if self.service_adapter:
            logger.info(f"Configured service provider: {llm_service_provider}.")
        
        # If no memory: set system prompt.
        if not self.memory_manager.get_current_memory() and self.service_adapter.system_prompt:
            system_prompt = self.service_adapter.get_system_prompt()
            if system_prompt:
                self.memory_manager.set_memory([system_prompt])
    
    async def process_message(self, message: Dict[str, Any], recipient: str) -> Optional[Dict[str, Any]]:
        try:
            text = message.get("text", "")
            attachments = message.get("attachments", [])
            
            llm_attachments = self.service_adapter.handle_attachments(attachments)

            # Only remember text (for context size)
            if self.memory_manager.has_memory:
                self.memory_manager.add_user_message(self.service_adapter.format_user_message(text))
            else:
                if self.service_adapter.system_prompt:
                    system_prompt = self.service_adapter.get_system_prompt()
                    user_message = self.service_adapter.format_user_message(text)
                    self.memory_manager.set_memory([system_prompt, user_message])
                else:
                    self.memory_manager.set_memory([self.service_adapter.format_user_message(text)])

            memory = self.memory_manager.get_current_memory()

            payload = self.service_adapter.prepare_payload(
                memory, 
                llm_attachments if llm_attachments else None
            )
            headers = self.service_adapter.prepare_headers(self.llm_api_key)
            uri = self.service_adapter.endpoint

            raw_response = await self._make_api_request(uri, payload, headers)
            if not raw_response:
                return {"content": "Failed to get response from LLM service", "attachments": []}

            response = self.service_adapter.parse_response(raw_response)

            if response and self.memory_manager.has_memory:
                self.memory_manager.add_model_response(
                    self.service_adapter.format_model_response(response.get("content", ""))
                )
                if self.memory_manager.save_memory:
                    await self.memory_manager.save_conversation()
                    
            return response
            
        except Exception as e:
            logger.error(f"Error processing message with LLM: {e}")
            logger.debug(traceback.format_exc())
            return {"content": f"Sorry, I encountered an error: {str(e)}", "attachments": []}
    
    async def _make_api_request(self, uri: str, payload: dict, headers: dict) -> Optional[dict]:
        return await HTTPClient.post(uri, json_data=payload, headers=headers)
