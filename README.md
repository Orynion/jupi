# Jupi

Saturnia is the conversational assistant and local math helper in this repository.

Repository: https://github.com/Orynion/jupi

## Overview

This project contains a Python assistant that combines a Gemini-backed conversational flow with local math solving and persistent memory. The current implementation keeps conversation history in memory for the active session and persists selected conversation events to `saturnia_memory.json` so they can be restored when a new Saturnia process starts.

## Features

### Conversation and personality
- Natural-language conversation via the Gemini API
- Greeting and general conversational routing
- Personality-aware responses and quirks in the Saturnia flow
- Persistent memory for remembered facts and conversation history

### Local math engines
The project includes local solvers for:
- basic arithmetic
- algebraic equations
- quadratic equations
- fraction-based algebra
- systems of equations
- powers and roots

These solvers are checked before falling back to the Gemini-based conversational path.

### Persistent memory
- Remembers user names and preferences
- Stores conversation history in `saturnia_memory.json`
- Keeps the most recent 100 recorded messages in the persisted history

### Interfaces
- CLI chat entry point in `main.py`
- Flask web app in `app/core/web.py`
- JSON API at `/api/chat` for frontend integrations

## Project structure

```text
jupi/
├── app/
│   └── core/
│       ├── algebra_engine.py
│       ├── brain.py
│       ├── console.py
│       ├── fraction_algebra_engine.py
│       ├── intent.py
│       ├── math_engine.py
│       ├── memory.py
│       ├── music_tool.py
│       ├── personality.py
│       ├── power_root_engine.py
│       ├── quadratic_engine.py
│       ├── quirks.py
│       ├── router.py
│       ├── system_algebra_engine.py
│       ├── test_*.py
│       ├── tic_tac_toe_tool.py
│       └── web.py
├── docs/
│   └── personality.md
├── main.py
├── memory.json
├── README.md
├── requirements.txt
├── saturnia_memory.json
└── jupi-home/
    └── src/
```

## Installation

1. Clone the repository:

```bash
git clone https://github.com/Orynion/jupi.git
cd jupi
```

2. Create a virtual environment:

```bash
python -m venv .venv
```

On Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Set up the Gemini API key in a `.env` file at the project root:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

See [Google AI Studio](https://aistudio.google.com/app/apikey) for an API key.

## Usage

### Command-line interface

```bash
python main.py
```

### Web interface

Start the Flask app from the repository root:

```bash
python -m app.core.web
```

Then open `http://localhost:5000` in a browser.

### API endpoint

```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is 2 + 2?"}'
```

Example response:

```json
{
  "response": "4"
}
```

## Example interactions

### Basic math
```text
You: What is 25 * 4?
AI: 100
```

### Algebra
```text
You: Solve 2x + 5 = 13
AI: x = 4.0
```

### Memory
```text
You: My name is Alex
AI: Nice to meet you, Alex.

You: What's my name?
AI: Your name is Alex.
```

## Personality

Saturnia is designed to be:

- curious
- helpful
- honest about uncertainty
- playful when appropriate
- transparent about being an AI

See `docs/personality.md` for the current personality notes.

## Development

Run the project test suite from the repository root:

```bash
python -m unittest discover -s app/core -p "test*.py" -v
```

The current memory system stores persisted conversation data in `saturnia_memory.json`. To clear history, delete that file or use the memory helpers in `app/core/memory.py`.

## Contributing

This repository is an experimental assistant project. Contributions and feedback are welcome.

## License

This project is provided as-is for local experimentation and development.

## Acknowledgments

- Gemini for the conversational model integration
- Flask for the web interface
- Saturnia's local math and memory systems for the repository's core behavior

