'''
# Python code for interacting with bbernhards signal-cli-rest-api (https://github.com/bbernhard/signal-cli-rest-api)
# and ggerganovs llama.cpp-server (https://github.com/ggml-org/llama.cpp) or ollama (https://ollama.com/)

# Tabs for indentation (Better for primitive editors).
# One file (Similar reasons but mostly for nostalgia.).

# Follow the installation instructions on the github page for signal-cli-api and (ollama or llamacpp-server)

# Debian-like linux prerequisites:

sudo apt-get install python3-aiohttp
sudo apt-get install python3-websockets
sudo apt-get install python3-aiofiles
'''
import base64
import json
import logging
import os
import traceback
from typing import List, Optional, Dict, Any, Union
from enum import Enum
from abc import ABC, abstractmethod

import asyncio # install
import aiohttp  # install
import websockets  # install
import aiofiles  # install

logging.basicConfig(
	level=logging.INFO,
	format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ConfigManager:	
	def __init__(self, config_path: str = "config.json"):
		self.config = self._load_config(config_path)
		
	def _load_config(self, config_path: str) -> Dict[str, Any]:
		try:
			with open(config_path, "r") as f:
				return json.load(f)
		except FileNotFoundError as e:
			logger.critical(f"Config file not found: {config_path}")
			raise
		except json.JSONDecodeError as e:
			logger.critical(f"Invalid JSON in config file: {e}")
			raise
		except Exception as e:
			logger.critical(f"Unexpected error loading config: {e}")
			raise

class MemoryManager:	
	def __init__(self, has_memory: bool, save_memory: bool, memory_file: str = "conversation_history.json"):
		self.has_memory = has_memory
		self.save_memory = save_memory
		self._conversation_memory_file = memory_file
		self._conversation_memory = []
		
		if self.has_memory and self.save_memory:
			logger.info(f"The conversation will be saved in {self._conversation_memory_file}.")
			self._conversation_memory = self._load_conversation_memory(self._conversation_memory_file)
	
	def _load_conversation_memory(self, fp: str) -> List[Dict[str, str]]:
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
	
	def get_current_memory(self) -> str:
		return self._conversation_memory
	
	def set_memory(self, memory: List) -> None:
		self._conversation_memory = memory
	

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
		payload = {
			"recipient": recipient,
		}
		
		try:
			async with aiohttp.ClientSession() as session:
				async with session.put(self._uri, json=payload) as resp:
					if resp.status not in [200, 201, 204]:
						error_text = await resp.text()
						logger.error(f"Signal typing indicator error: HTTP {resp.status} - {error_text}")
		except Exception as e:
			logger.error(f"Error sending typing indicator: {e}")
	
	async def _send_stop_typing(self, recipient: str) -> None:
		payload = {
			"recipient": recipient,
		}
		
		try:
			async with aiohttp.ClientSession() as session:
				async with session.delete(self._uri, json=payload) as resp:
					if resp.status not in [200, 202, 204]:
						error_text = await resp.text()
						logger.error(f"Signal stop typing error: HTTP {resp.status} - {error_text}")
		except Exception as e:
			logger.error(f"Error stopping typing indicator: {e}")
	
	def cancel_all_typing(self) -> None:
		# Forecfully cancel all typing tasks
		for task in self._typing_tasks.values():
			if not task.done():
				task.cancel()
		self._typing_tasks.clear()
	
	async def close(self) -> None:
		# Gracefully cancel all typing tasks
		recipients = list(self._typing_tasks.keys())
		for recipient in recipients:
			await self.stop_typing(recipient)


class LLMServiceAdapter(ABC):
	@abstractmethod
	def prepare_payload(self, memory: List[Dict[str, Any]], images: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
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

class LlamacppServerAdapter(LLMServiceAdapter):
	def __init__(self, url: str, llm_model_options: Dict[str, Any]):
		self.endpoint = f"{url}/v1/chat/completions"
		self.system_prompt = llm_model_options.get("system_prompt", "")
	
	def prepare_payload(self, memory: List[Dict[str, Any]], images: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
		messages = []
		for message in memory:
			# TODO: Add multimodal when/if it is implemented
			for k, v in message.items():
				messages.append({"role":k, "content":v})
		
		return {"messages":messages}
	
	def prepare_headers(self, api_key: Optional[str]) -> Dict[str, str]:
		headers = {"Content-Type": "application/json"}
		if not api_key:
			api_key = "no-key"
		headers["Authorization"] = f"Bearer {api_key}"

		return headers

	def format_user_message(self, text: str) -> Dict[str, Any]:
		return {"user": "" if not text else text.rstrip()}
	
	def format_model_response(self, text: str) -> Dict[str, Any]:
		return {"assistant":text.rstrip()}

	def parse_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
		try:
			# Sure. Some error checking should take place.
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
		return {"system":self.system_prompt} if self.system_prompt else None

	def is_output_limited(self, response: Dict[str, Any]) -> bool:
		return response.get("finish_reason") == "length"


class OllamaAdapter(LLMServiceAdapter):
	def __init__(self, uri: str, llm_model_options: Dict[str, Any]):
		self.endpoint = f"{uri}/v1/chat/completions"
		self.model = llm_model_options.get("model", "")
		self.keep_alive = llm_model_options.get("keep_alive", 5) # Ollama default is currently 5 min
		self.system_prompt = llm_model_options.get("system_prompt", "")
	
	def prepare_payload(self, memory: List[Dict[str, Any]], images: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
		messages = []
		for message in memory:
			for k, v in message.items():
				if k == "user" and images and message is memory[-1]: # Current message
					message_obj = {"role": k, "content": [{"type": "text", "text": v}]}
					for image in images:
						message_obj["content"].append({
							"type": "image_url",
							"image_url": {
								"url": f"data:{image.get('content_type', 'image/jpeg')};base64,{image.get('data', '')}"
							}
						})
					
					messages.append(message_obj)
				else:
					messages.append({"role": k, "content": v})
		
		return {"model": self.model, "messages":messages, "stream": False, "keep_alive": self.keep_alive}
	
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
		return {"assistant":text.rstrip()}

	def get_system_prompt(self) -> Dict[str, Any]:
		return {"system":self.system_prompt} if self.system_prompt else None

	def is_output_limited(self, response: Dict[str, Any]) -> bool:
		return response.get("finish_reason") == "length"

class LLMServiceFactory:
	@staticmethod
	def get_adapter(llm_service_provider: str, llm_service_url: str, llm_model_options: Dict[str, Any]) -> LLMServiceAdapter:
		adapters = {
			"llamacpp": LlamacppServerAdapter(llm_service_url, llm_model_options),
			"ollama": OllamaAdapter(llm_service_url, llm_model_options)
		}
		
		if llm_service_provider not in adapters:
			logger.warning(f"Unknown LLM service type: {llm_service_provider}.")
			return None
		
		return adapters[llm_service_provider]


class LLMClient:
	
	def __init__(self, llm_service_url: str, llm_api_key: str, llm_model_options: Dict[str, Any], 
				 memory_manager, typing_client, llm_service_provider: str):
		self.llm_service_url = llm_service_url
		self.llm_api_key = llm_api_key
		self.llm_model_options = llm_model_options
		self.memory_manager = memory_manager
		self.typing_client = typing_client
		self.service_adapter = LLMServiceFactory.get_adapter(llm_service_provider, llm_service_url, llm_model_options)
		if self.service_adapter:
			logger.info(f"Configured service provider: {llm_service_provider}.")
		# If no memory: set system prompt.
		if not self.memory_manager.get_current_memory() and self.service_adapter.system_prompt:
			self.memory_manager.set_memory([self.service_adapter.get_system_prompt()])
		# TODO: Check if configured system prompt is different from memory (the saved one will be used?)
	
	async def process_message(self, message: Dict[str, Any], recipient: str) -> Optional[Dict[str, Any]]:
		try:
			text = message.get("text", "")
			attachments = message.get("attachments", [])
			
			image_attachments = [
				attachment for attachment in attachments 
				if attachment.get("content_type", "").startswith("image/")
			]

			# Only save text (for context size/now)
			if self.memory_manager.has_memory:
				self.memory_manager.add_user_message(self.service_adapter.format_user_message(text))
			else:
				user_message = self.service_adapter.format_user_message(text) if not self.service_adapter.system_prompt else {self.service_adapter.get_system_prompt(), self.service_adapter.format_user_message(text)}
				self.memory_manager.set_memory([user_message])

			memory = self.memory_manager.get_current_memory()

			payload = self.service_adapter.prepare_payload(memory, image_attachments if image_attachments else None)
			headers = self.service_adapter.prepare_headers(self.llm_api_key)
			uri = self.service_adapter.endpoint

			raw_response = await self._make_api_request(uri, payload, headers)
			if not raw_response:
				return {"content": "Failed to get response from LLM service", "attachments": []}

			response = self.service_adapter.parse_response(raw_response)

			if response and self.memory_manager.has_memory:
				self.memory_manager.add_model_response(self.service_adapter.format_model_response(response.get("content", "")))
				if self.memory_manager.save_memory:
					await self.memory_manager.save_conversation()
			return response
			
		except Exception as e:
			logger.error(f"Error processing message with LLM: {e}")
			logger.debug(traceback.format_exc())
			return {"content": f"Sorry, I encountered an error: {str(e)}", "attachments": []}

	
	async def _make_api_request(self, uri: str, payload: dict, headers: dict) -> Optional[dict]:
		try:
			async with aiohttp.ClientSession() as session:
				async with session.post(uri, json=payload, headers=headers) as resp:
					if resp.status == 200:
						return await resp.json()
					else:
						error_text = await resp.text()
						logger.error(f"LLM API error: HTTP {resp.status} - {error_text}")
						return None
		except aiohttp.ClientError as e:
			logger.error(f"HTTP client error in LLM request: {e}")
			return None
		except asyncio.TimeoutError:
			logger.error("Timeout while waiting for LLM response")
			return None
		except Exception as e:
			logger.error(f"Unexpected error in LLM request: {e}")
			logger.debug(traceback.format_exc())
			return None



class SignalClient:
	def __init__(self, signal_service: str, phone_number: str, reset_memory_word: Optional[str],
				 memory_manager: MemoryManager, llm_client: LLMClient, typing_client: TypingClient):
		self.signal_service = signal_service
		self.phone_number = phone_number
		self.reset_memory_word = reset_memory_word
		self.memory_manager = memory_manager
		self.llm_client = llm_client
		self.typing_client = typing_client
	
	async def start(self) -> None:
		logger.info("Starting Signal API Relay service...")
		retry_count = 0
		max_retries = 5
		
		while True:
			try:
				await self._receive_and_process_messages()
				retry_count = 0
			except websockets.exceptions.ConnectionClosed as e:
				logger.error(f"WebSocket connection closed: {e}")
				retry_count += 1
			except Exception as e:
				logger.error(f"Connection error: {e}")
				logger.debug(traceback.format_exc())
				retry_count += 1
			
			# Reconnection with "exponential backoff"
			wait_time = min(30, 2 ** retry_count)
			logger.info(f"Reconnecting in {wait_time} seconds... (Attempt {retry_count}/{max_retries})")
			await asyncio.sleep(wait_time)
			
			if retry_count >= max_retries:
				logger.error(f"Max retries ({max_retries}) exceeded. Waiting 60 seconds before trying again.")
				retry_count = 0
				await asyncio.sleep(60)
	
	async def _receive_and_process_messages(self) -> None:
		ws_uri = f"ws://{self.signal_service}/v1/receive/{self.phone_number}"
		
		async with websockets.connect(ws_uri, ping_interval=None) as websocket:
			logger.info("Connected to Signal websocket")
			
			async for raw_message in websocket:
				try:
					await self._handle_message(raw_message)
				except Exception as e:
					logger.error(f"Error handling message: {e}")
					logger.debug(traceback.format_exc())
	
	async def _handle_message(self, raw_message: str) -> None:
		try:
			message = await self._parse_message(raw_message)
			if not message:
				return
			
			if not message.get("text") and not message.get("attachments"):
				return
			
			if await self._handle_command(message.get("text", "")):
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
	
	# TODO: Command_Manager
	async def _handle_command(self, text: str) -> bool:
		try:
			if self.reset_memory_word and text == self.reset_memory_word:
				self.memory_manager.reset_memory()
				if self.llm_client.service_adapter.system_prompt:
					self.memory_manager.set_memory([self.llm_client.service_adapter.get_system_prompt()])
				await self.memory_manager.save_conversation()
				return True
			else:
				return False
		except Exception as e:
			logger.error(f"Error handling command: {e}")
			logger.debug(traceback.format_exc())
			return False
	
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
					attachment_id = attachment.get("id")
					if attachment_id:
						attachment_data = await self._get_attachment(attachment_id)
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
	
	async def _get_attachment(self, attachment_id: str) -> Optional[str]:
		uri = f"http://{self.signal_service}/v1/attachments/{attachment_id}"
		
		try:
			async with aiohttp.ClientSession() as session:
				async with session.get(uri) as resp:
					if resp.status == 200:
						content = await resp.read()
						return base64.b64encode(content).decode("utf-8")
					else:
						logger.error(f"Failed to get attachment: HTTP {resp.status}")
						return None
		except aiohttp.ClientError as e:
			logger.error(f"HTTP client error retrieving attachment: {e}")
			return None
		except Exception as e:
			logger.error(f"Error retrieving attachment: {e}")
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
				attachment_id = await self._upload_attachment(attachment)
				if attachment_id:
					attachment_ids.append(attachment_id)
			
			if attachment_ids:
				payload["attachments"] = attachment_ids

		try:
			async with aiohttp.ClientSession() as session:
				async with session.post(uri, json=payload) as resp:
					if resp.status not in [200, 201]:
						error_text = await resp.text()
						logger.error(f"Error sending Signal message: HTTP {resp.status} - {error_text}")
		except aiohttp.ClientError as e:
			logger.error(f"HTTP client error sending Signal message: {e}")
		except Exception as e:
			logger.error(f"Error sending Signal message: {e}")
			logger.debug(traceback.format_exc())

	async def _upload_attachment(self, attachment: Dict[str, Any]) -> Optional[str]:
		uri = f"http://{self.signal_service}/v1/attachments"
		
		try:
			binary_data = base64.b64decode(attachment["data"])
			
			form_data = aiohttp.FormData()
			form_data.add_field(
				"attachment",
				binary_data,
				filename=attachment.get("filename", "image.jpg"),
				content_type=attachment.get("content_type", "image/jpeg")
			)
			
			async with aiohttp.ClientSession() as session:
				async with session.post(uri, data=form_data) as resp:
					if resp.status == 200:
						response_data = await resp.json()
						return response_data.get("id")
					else:
						error_text = await resp.text()
						logger.error(f"Error uploading attachment: HTTP {resp.status} - {error_text}")
						return None
		except Exception as e:
			logger.error(f"Error uploading attachment: {e}")
			logger.debug(traceback.format_exc())
			return None


class Application:
	def __init__(self, config_path: str = "config.json"):
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
			llm_api_key=config["llm_api_key"],
			llm_service_provider=config["llm_service_provider"],
			llm_model_options=config["llm_model_options"],
			memory_manager=self.memory_manager,
			typing_client=self.typing_client
		)
		
		self.signal_client = SignalClient(
			signal_service=config["signal_service"],
			phone_number=config["phone_number"],
			reset_memory_word=config["reset_memory_word"],
			memory_manager=self.memory_manager,
			llm_client=self.llm_client,
			typing_client=self.typing_client
		)
	
	async def run(self):
		await self.signal_client.start()


async def main():
	try:
		app = Application()
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
