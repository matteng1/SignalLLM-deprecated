from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class LLMServiceAdapter(ABC):
    @abstractmethod
    def prepare_payload(self, memory: List[Dict[str, Any]], attachments: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def prepare_headers(self, api_key: Optional[str]) -> Dict[str, str]:
        pass
    
    @abstractmethod
    def parse_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_system_prompt(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def format_user_message(self, text: str) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def format_model_response(self, text: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def is_output_limited(self, response: Dict[str, Any]) -> bool:
        pass

    @abstractmethod
    def handle_attachments(self, attachments:Dict[str, Any]) -> List[Dict[str, Any]]:
        pass


class LLMServiceFactory:
    @staticmethod
    def get_adapter(llm_service_provider: str, llm_service_url: str, llm_model_options: Dict[str, Any]) -> Optional[LLMServiceAdapter]:
        from clients.llm.llamacpp import LlamacppServerAdapter
        from clients.llm.ollama import OllamaAdapter
        from utils.logging_setup import logger
        
        adapters = {
            "llamacpp": LlamacppServerAdapter(llm_service_url, llm_model_options),
            "ollama": OllamaAdapter(llm_service_url, llm_model_options)
        }
        
        if llm_service_provider not in adapters:
            logger.warning(f"Unknown LLM service type: {llm_service_provider}.")
            return None
        
        return adapters[llm_service_provider]
