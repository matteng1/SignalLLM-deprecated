# SignalLLM
One "simple" python file for texting with a large language model over the Signal messaging app.<br>
Supports sending images to ollama and multimodal language models. <br><br>
Really long conversations with memory enabled will cause OOMs or slowdowns.<br>
Just delete, edit or move conversation_history.json or use the magic word.<br>

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
    "llm_model_options": {"model": "gemma3:12b", "keep_alive": 30}, // See below
    "reset_memory_word": "Magicword"             // Word or phrase to clear memory
}
```
### llamacpp
"llm_model_options" is ignored<br>
### ollama
"model" selects which model to interact with.<br>
"keep_alive" is how long (in minutes) the model should be loaded in memory. For speedier answers the default is set to 30 minutes.<br><br>
* Run it
```shell
python3 main.py
```
* Text it from Signal.

<br><br><br>
Signal code inspired by René Filips' signalbot (https://github.com/filipre/signalbot).
