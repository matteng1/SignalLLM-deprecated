# syntax=docker/dockerfile:1
FROM python:3.11.11-slim-bookworm
RUN python3 -m pip install aiohttp websockets aiofiles
WORKDIR /signalllm
COPY main.py .
RUN touch ./config.json
RUN touch ./conversation_history.json
CMD [ "python3", "main.py"]
