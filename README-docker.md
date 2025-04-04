# Docker
Follow instructions in [SERVERS-install](SERVERS-install.md) to install signal-cli-rest-api and one of ollama or llamacpp-server. <br><br>

* Clone this repository:
```shell
git clone https://github.com/matteng1/SignalLLM.git
```
* Enter directory, build docker image and create conversation_history-file:
```shell
cd SignalLLM
docker build -t signalllm:latest .
touch conversation_history.json # On windows: type nul > conversation_history.json
```
* Edit config.json according to [README](README.md) <br><br>
* Run image:<br>
  *(Note:* "${PWD}/" *is probably* "%cd%\\" *in windows)*
```shell
docker run --rm -d --name signalllm --network host -v ${PWD}/config.json:/signalllm/config.json -v ${PWD}/conversation_history.json:/signalllm/conversation_history.json signalllm:latest
```
* Text it from Signal <br><br>
#### Editing config
* Changing anything (config, conversation history) requires a restart (clearing history can be done with the magic word).
```shell
docker stop signalllm
# Edit file(s) and use the "Run image" command again.
```
<br>

#### Troubleshooting
* Run the container in interactive mode for error messages (stop running ones first):
```shell
docker stop signalllm
docker run --rm -it --name signalllm --network host -v ${PWD}/config.json:/signalllm/config.json -v ${PWD}/conversation_history.json:/signalllm/conversation_history.json signalllm:latest
```
