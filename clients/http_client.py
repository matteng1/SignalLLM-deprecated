import json
import traceback
import aiohttp
from typing import Dict, Any, Optional
from utils.logging_setup import logger


class HTTPClient:
    @staticmethod
    async def post(url: str, json_data: Dict[str, Any] = None, headers: Dict[str, str] = None,
                  form_data: aiohttp.FormData = None) -> Optional[Dict[str, Any]]:
        try:
            async with aiohttp.ClientSession() as session:
                data = form_data if form_data else json_data
                method = session.post
                kwargs = {'data': data} if form_data else {'json': data}
                if headers:
                    kwargs['headers'] = headers
                
                async with method(url, **kwargs) as resp:
                    if resp.status in [200, 201, 204]:
                        if resp.content_type == 'application/json':
                            return await resp.json()
                        else:
                            return {'status': resp.status, 'text': await resp.text()}
                    else:
                        error_text = await resp.text()
                        logger.error(f"HTTP error: {resp.status} - {error_text}")
                        return None
        except aiohttp.ClientError as e:
            logger.error(f"HTTP client error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in HTTP request: {e}")
            logger.debug(traceback.format_exc())
            return None
    
    @staticmethod
    async def get(url: str, headers: Dict[str, str] = None) -> Optional[Any]:
        try:
            async with aiohttp.ClientSession() as session:
                kwargs = {}
                if headers:
                    kwargs['headers'] = headers
                
                async with session.get(url, **kwargs) as resp:
                    if resp.status == 200:
                        return await resp.read()
                    else:
                        logger.error(f"HTTP GET error: {resp.status}")
                        return None
        except aiohttp.ClientError as e:
            logger.error(f"HTTP client error in GET request: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in GET request: {e}")
            logger.debug(traceback.format_exc())
            return None
    
    @staticmethod
    async def put(url: str, json_data: Dict[str, Any], headers: Dict[str, str] = None) -> bool:
        try:
            async with aiohttp.ClientSession() as session:
                kwargs = {'json': json_data}
                if headers:
                    kwargs['headers'] = headers
                
                async with session.put(url, **kwargs) as resp:
                    if resp.status in [200, 201, 204]:
                        return True
                    else:
                        error_text = await resp.text()
                        logger.error(f"HTTP PUT error: {resp.status} - {error_text}")
                        return False
        except aiohttp.ClientError as e:
            logger.error(f"HTTP client error in PUT request: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error in PUT request: {e}")
            logger.debug(traceback.format_exc())
            return False
    
    @staticmethod
    async def delete(url: str, json_data: Dict[str, Any] = None, headers: Dict[str, str] = None) -> bool:
        try:
            async with aiohttp.ClientSession() as session:
                kwargs = {}
                if json_data:
                    kwargs['json'] = json_data
                if headers:
                    kwargs['headers'] = headers
                
                async with session.delete(url, **kwargs) as resp:
                    if resp.status in [200, 202, 204]:
                        return True
                    else:
                        error_text = await resp.text()
                        logger.error(f"HTTP DELETE error: {resp.status} - {error_text}")
                        return False
        except aiohttp.ClientError as e:
            logger.error(f"HTTP client error in DELETE request: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error in DELETE request: {e}")
            logger.debug(traceback.format_exc())
            return False
