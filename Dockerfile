# syntax=docker/dockerfile:1
FROM python:3.11.11-slim-bookworm
WORKDIR /signal-llm
COPY . .
RUN pip install --root-user-action=ignore --upgrade pip
RUN pip install --root-user-action=ignore -r requirements.txt
CMD [ "python3", "main.py"]

