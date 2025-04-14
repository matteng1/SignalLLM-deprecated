#!/usr/bin/env python3
"""
Python code for interacting with bbernhards signal-cli-rest-api (https://github.com/bbernhard/signal-cli-rest-api)
and ollama (https://ollama.com/) or ggerganovs llama.cpp-server (https://github.com/ggml-org/llama.cpp).

Debian-like linux prerequisites:
    sudo apt-get install python3-aiohttp
    sudo apt-get install python3-websockets
    sudo apt-get install python3-aiofiles
"""
import asyncio
import json
import os
import traceback

from config.config_manager import ConfigManager
from memory.memory_manager import MemoryManager
from clients.typing_client import TypingClient
from clients.llm_client import LLMClient
from clients.signal_client import SignalClient
from commands.command_manager import CommandManager
from utils.logging_setup import logger


class Application:
    def __init__(self, api_key:str, config_path="config.json"):
        self.config_manager = ConfigManager(config_path)
        config = self.config_manager.config
        
        self.memory_manager = MemoryManager(
            has_memory=config["has_memory"],
            save_memory=config["save_memory"],
            memory_file=config["memory_file"]
        )

        self.typing_client = TypingClient(
            signal_service=config["signal_service"],
            phone_number=config["phone_number"],
            refresh_interval=10
        )
        
        self.llm_client = LLMClient(
            llm_service_url=config["llm_service_url"],
            llm_api_key=config["llm_api_key"] if not api_key else api_key,
            llm_service_provider=config["llm_service_provider"],
            llm_model_options=config["llm_model_options"],
            memory_manager=self.memory_manager,
            typing_client=self.typing_client
        )
        
        # Set up command manager
        self.command_manager = CommandManager()
        
        # Register command(s)
        if config.get("reset_memory_word"):
            self.command_manager.register_command(
                config["reset_memory_word"],
                self._reset_memory_command
            )
        
        self.signal_client = SignalClient(
            signal_service=config["signal_service"],
            phone_number=config["phone_number"],
            save_attachments=config["save_attachments"],
            memory_manager=self.memory_manager,
            llm_client=self.llm_client,
            typing_client=self.typing_client,
            command_manager=self.command_manager
        )
    
    async def _reset_memory_command(self) -> None:
        self.memory_manager.reset_memory()
        if self.llm_client.service_adapter.system_prompt:
            system_prompt = self.llm_client.service_adapter.get_system_prompt()
            if system_prompt:
                self.memory_manager.set_memory([system_prompt])
        await self.memory_manager.save_conversation()
        logger.info("Memory reset command executed")
    
    async def run(self):
        await self.signal_client.start()


async def main():
    try:
        api_key = os.getenv("API_KEY", "")
        app = Application(api_key=api_key)
        await app.run()
    except FileNotFoundError as e:
        logger.critical(f"Configuration file not found: {e}")
        exit(1)
    except json.JSONDecodeError as e:
        logger.critical(f"Invalid configuration JSON: {e}")
        exit(1)
    except Exception as e:
        logger.critical(f"Fatal error during initialization: {e}")
        logger.debug(traceback.format_exc())
        exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Service stopped by user")
    except Exception as e:
        logger.critical(f"Fatal error: {e}")
        logger.debug(traceback.format_exc())
        exit(1)
