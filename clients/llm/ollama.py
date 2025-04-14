from typing import Dict, Any, List, Optional
from clients.llm.base import LLMServiceAdapter
from utils.logging_setup import logger


class OllamaAdapter(LLMServiceAdapter):
    def __init__(self, uri: str, llm_model_options: Dict[str, Any]):
        self.endpoint = f"{uri}/v1/chat/completions"
        self.model = llm_model_options.get("model", "")
        self.keep_alive = llm_model_options.get("keep_alive", 5)  # Ollama default is currently 5 min
        self.system_prompt = llm_model_options.get("system_prompt", "")
    
    def prepare_payload(self, memory: List[Dict[str, Any]], attachments: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        messages = []
        for message in memory:
            for k, v in message.items():
                if k == "user" and attachments and message is memory[-1]:  # Current message
                    message_obj = {"role": k, "content": [{"type": "text", "text": v}]}
                    # Atm only support images.
                    for attachment in attachments:
                        message_obj["content"].append({
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{attachment.get('content_type', 'image/jpeg')};base64,{attachment.get('data', '')}"
                            }
                        })
                    
                    messages.append(message_obj)
                else:
                    messages.append({"role": k, "content": v})
        
        return {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "keep_alive": self.keep_alive
        }
    
    def handle_attachments(self, attachments:Dict[str, Any]) -> List[Dict[str, Any]]:
        # only images and not gifs for now.
        return [
                attachment for attachment in attachments 
                if attachment.get("content_type", "").startswith("image/") and not attachment.get("content_type", "") == "image/gif"
            ]
    
    def prepare_headers(self, api_key: Optional[str]) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if not api_key:
            api_key = "no-key"
        headers["Authorization"] = f"Bearer {api_key}"

        return headers
    
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

    def format_user_message(self, text: str) -> Dict[str, Any]:
        return {"user": "" if not text else text.rstrip()}
    
    def format_model_response(self, text: str) -> Dict[str, Any]:
        return {"assistant": text.rstrip()}

    def get_system_prompt(self) -> Dict[str, Any]:
        return {"system": self.system_prompt} if self.system_prompt else None

    def is_output_limited(self, response: Dict[str, Any]) -> bool:
        return response.get("finish_reason") == "length"
