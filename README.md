# SignalLLM
Python app for texting a large language model using the Signal messaging app.<br>
Uses **signal-cli-rest-api** and an OpenAI chat compatible endpoint. Tested with **Ollama** and **llama.cpp-server**. <br>
**May** work with other OpenAI-compatible apis with some configuration. Use "ollama" as llm_service_provider if the endpoint can parse images. <br><br>
Supports **system prompt**. You can describe a character you'd like to be chatting with.<br>
Supports sending **images** if using ollama and a multimodal language model. <br><br>
**Really long conversations with memory enabled may cause OOMs or slowdowns.** <br>
To fix it just delete, edit or move conversation_history.json. Or use the magic word.<br><br>
Memory file is saved in ./files/memory/ and attachments are saved in ./files/attachments/<br><br>
The LLM API key can be set as an environment variable.<br>
```shell
API_KEY="abcdef12345" python3 main.py
```
Docker instructions in [README-docker.md](README-docker.md).<br><br>

## Prerequisites
* Follow the instructions in [SERVERS-install.md](SERVERS-install.md) to install signal-cli-rest-api and **one of** ollama **or** llamacpp-server.<br><br>
* Install prerequisites (Debian or similar distributions):
```shell
sudo apt-get install python3-aiohttp python3-websockets python3-aiofiles
```
* ***Clone this repository and enter directory.***
```shell
git clone --depth 1 https://github.com/matteng1/SignalLLM.git
cd SignalLLM
```
<br><br>
## Configuration
* Configure your settings in config.conf (see below for more information):
```javascript
{
    "signal_service": "127.0.0.1:9922",          // signal-cli-rest-api
    "phone_number": "+12345678910",              // Number of the linked Signal account
    "has_memory": true,                          // Remember previous messages
    "save_memory": true,                         // Continue at a later run
    "save_attachments": true,                    // Save received attachments
    "memory_file": "conversation_history.json",  // Memory file
    "llm_service_provider": "ollama",            // "ollama" or "llamacpp"
    "llm_service_url": "http://localhost:11434", // Port 11434 for ollama. 8080 for llamacpp
    "llm_api_key": "",                           // api key. Leave empty for local servers.
    "llm_model_options": {"system_prompt": "","model":"gemma3:12b","keep_alive": 30}, // See below
    "reset_memory_word": "Magicword"             // Word or phrase to clear memory
}
```
### llamacpp
* llm_model_options:<br>
**"system_prompt"**: System instructions. Can be a description of the chat companion.<br>
The rest is ignored when using llama.cpp-server for now. Select model and model parameters when starting llama.cpp-server.
### ollama
* llm_model_options:<br>
**"system_prompt"**: System instructions. Can be a description of the chat companion. If running a multi-language model the language used in the system prompt will be used in the chat.<br>
**"model"**:         Which model to interact with.<br>
**"keep_alive"**:    How long (in minutes) the model should be loaded in memory. For speedier answers the default is set to 30 minutes.<br><br><br>
## Run it
```shell
python3 main.py
```
* Text it from Signal.

<br><br><br>
Signal code inspired by René Filips' signalbot (https://github.com/filipre/signalbot).
