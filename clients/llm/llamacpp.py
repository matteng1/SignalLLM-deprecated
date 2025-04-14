from typing import Dict, Any, List, Optional
from clients.llm.base import LLMServiceAdapter
from utils.logging_setup import logger


class LlamacppServerAdapter(LLMServiceAdapter):
    def __init__(self, url: str, llm_model_options: Dict[str, Any]):
        self.endpoint = f"{url}/v1/chat/completions"
        self.system_prompt = llm_model_options.get("system_prompt", "")
    
    def prepare_payload(self, memory: List[Dict[str, Any]], attachments: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        # No multimodal.
        messages = []
        for message in memory:
            for k, v in message.items():
                messages.append({"role": k, "content": v})
        
        return {"messages": messages}
    
    def handle_attachments(self, attachments:Dict[str, Any]) -> List[Dict[str, Any]]:
        # No multimodal support for now.
        return []
    
    def prepare_headers(self, api_key: Optional[str]) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if not api_key:
            api_key = "no-key"
        headers["Authorization"] = f"Bearer {api_key}"

        return headers

    def format_user_message(self, text: str) -> Dict[str, Any]:
        return {"user": "" if not text else text.rstrip()}
    
    def format_model_response(self, text: str) -> Dict[str, Any]:
        return {"assistant": text.rstrip()}

    def parse_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            content = response_data["choices"][0]["message"]["content"]
            finish_reason = response_data["choices"][0]["finish_reason"]
        except Exception as e:
            errormsg = f"Error parsing response from LLM: {e}"
            logger.error(errormsg)
            return {
                "content": errormsg,
                "finish_reason": "stop"
            }

        return {
            "content": content,
            "finish_reason": finish_reason
        }

    def get_system_prompt(self) -> Dict[str, Any]:
        return {"system": self.system_prompt} if self.system_prompt else None

    def is_output_limited(self, response: Dict[str, Any]) -> bool:
        return response.get("finish_reason") == "length"
