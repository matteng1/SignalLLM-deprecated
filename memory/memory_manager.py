import json
import aiofiles
from typing import List, Dict, Any
from utils.logging_setup import logger


class MemoryManager:
    def __init__(self, has_memory=True, save_memory=True, memory_file="conversation_history.json"):
        self.has_memory = has_memory
        self.save_memory = save_memory
        self._conversation_memory_file = f"./files/memory/{memory_file}"
        self._conversation_memory = []
        
        if self.has_memory and self.save_memory:
            logger.info(f"The conversation will be saved in {self._conversation_memory_file}.")
            self._conversation_memory = self._load_conversation_memory(self._conversation_memory_file)
    
    def _load_conversation_memory(self, fp) -> List[Dict[str, str]]:
        try:
            with open(fp, "r") as f:
                logger.info("Conversation memory loaded from file.")
                return json.loads(f.read())["messages"]
        except FileNotFoundError:
            logger.info(f"Conversation memory file not found, starting with empty memory.")
            return []
        except Exception as e:
            logger.error(f"Error loading conversation memory: {e}")
            return []
    
    async def save_conversation(self) -> None:
        if not self.has_memory or not self.save_memory:
            return
            
        try:
            async with aiofiles.open(self._conversation_memory_file, "w") as out:
                escaped_json = json.dumps({"messages": self._conversation_memory})
                await out.write(escaped_json)
                await out.flush()
        except Exception as e:
            logger.error(f"Failed to save conversation memory: {e}")
    
    def reset_memory(self) -> None:
        self._conversation_memory = []
        logger.info("Conversation memory reset")
    
    def add_user_message(self, message: Dict[str, str]) -> None:
        self._conversation_memory.append(message)
    
    def add_model_response(self, message: Dict[str, str]) -> None:
        self._conversation_memory.append(message)
    
    def get_current_memory(self) -> List[Dict[str, str]]:
        return self._conversation_memory
    
    def set_memory(self, memory: List) -> None:
        self._conversation_memory = memory
