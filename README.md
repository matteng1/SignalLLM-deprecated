# SignalLLM
One "simple" python file for texting with a large language model with the Signal messaging app.<br>
Uses **signal-cli-rest-api** and **Ollama** (x)or **llama.cpp-server**. <br>
**May** work with other OpenAI-compatible apis with some configuration. <br><br>
Supports **system prompt**. You can describe a character you'd like to be chatting with.<br>
Supports sending **images** if using ollama and multimodal language model. <br><br>
**Really long conversations with memory enabled will cause OOMs or slowdowns.** <br>
To fix it just delete, edit or move conversation_history.json or use the magic word.<br><br>
Docker instructions in [README-docker.md](README-docker.md).

## Prerequisites
* Follow instructions in [SERVERS-install.md](SERVERS-install.md) to install signal-cli-rest-api and **one of** ollama **or** llamacpp-server.<br><br>
* Install prerequisites (Debian or similar distributions):
```shell
sudo apt-get install python3-aiohttp python3-websockets python3-aiofiles
```
* ***Download [main.py](main.py) and [config.json](config.json) from this repository.***<br><br>
* Configure your settings in config.conf (see below for more information):
```javascript
{
    "signal_service": "127.0.0.1:9922",          // signal-cli-rest-api
    "phone_number": "+12345678910",              // The number of the linked Signal account
    "has_memory": true,                          // If the app should remember previous messages
    "save_memory": true,                         // To continue at a later run
    "memory_file": "conversation_history.json",  // Filename for above
    "llm_service_provider": "ollama",            // "ollama" or "llamacpp"
    "llm_service_url": "http://localhost:11434", // Port 11434 for ollama. 8080 for llamacpp
    "llm_api_key": "",                           // api key. Leave empty for local servers.
    "llm_model_options": {"system_prompt": "","model":"gemma3:12b","keep_alive": 30}, // See below
    "reset_memory_word": "Magicword"             // Word or phrase to clear memory
}
```
### llamacpp
* llm_model_options:
"system_prompt": System instructions. Can be a description of the chat companion.
The rest is ignored for now. Select model and model parameters at start of llama.cpp-server.
### ollama
* llm_model_options:
"system_prompt": System instructions. Can be a description of the chat companion. If running multi-language model the language used in the system prompt will be used in the chat.
"model":         selects which model to interact with.<br>
"keep_alive":    how long (in minutes) the model should be loaded in memory. For speedier answers the default is set to 30 minutes.<br><br><br>
* Run it
```shell
python3 main.py
```
* Text it from Signal.

<br><br><br>
Signal code inspired by René Filips' signalbot (https://github.com/filipre/signalbot).
