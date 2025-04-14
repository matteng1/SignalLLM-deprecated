# Docker
Follow instructions in [SERVERS-install](SERVERS-install.md) to install signal-cli-rest-api and one of ollama or llamacpp-server. <br><br>

* Clone this repository and enter it
```shell
git clone --depth 1 https://github.com/matteng1/SignalLLM.git
cd SignalLLM
```
* Build docker image
```shell
docker build -t signal-llm:latest .
```
* Edit config.json according to [README](README.md) <br><br>
* Run image<br>
  *(Note:* "${PWD}/" *is probably* "%cd%\\" *in windows)*
```shell
docker run --rm -d --name signal-llm --network host -v ${PWD}/files/:/signal-llm/files/ -v ${PWD}/config.json:/signal-llm/config.json signal-llm:latest
```
* Text it from Signal <br><br>
#### After editing config
* Changing anything (config, conversation history) requires a restart (clearing history can be done with the magic word).
```shell
docker stop signal-llm
# Edit file(s) and use the "Run image" command again.
```
<br>

#### Troubleshooting
* Run the container in interactive mode for error messages (stop first)
```shell
docker stop signal-llm
docker run --rm --name signal-llm --network host -v ${PWD}/files/:/signal-llm/files/ -v ${PWD}/config.json:/signal-llm/config.json signal-llm:latest
```
