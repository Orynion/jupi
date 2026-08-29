<<<<<<< HEAD
# Jupi
Jupi by saturnia
=======
# AI or is it? 🤖

An experimental AI assistant project featuring **Saturnia** - a curious, helpful, and occasionally quirky conversational AI with local math computation capabilities.

## Overview

This project explores building an AI assistant that combines the power of Google's Gemini API with local computational engines for precise mathematical operations. Saturnia maintains conversation context, remembers user information, and responds with a distinct personality that's friendly, thoughtful, and occasionally playful.

## Features

### 🧠 Intelligent Conversation
- Natural language processing powered by Gemini 3.1 Flash Lite
- Context-aware responses that reference conversation history
- Multiple greetings and personality-driven interactions

### 🔢 Local Math Engines
Mathematics is computed locally without sending calculations to external APIs:
- **Basic Math**: Arithmetic operations (addition, subtraction, multiplication, division)
- **Algebra**: Linear equation solving
- **Quadratic Equations**: Quadratic formula solutions
- **Fraction Algebra**: Solving equations with fractions
- **Systems of Equations**: Solving simultaneous equations
- **Powers and Roots**: Exponents and root calculations

### 💾 Persistent Memory
- Remembers user names and preferences
- Stores conversation history (last 100 messages)
- JSON-based memory storage that persists between sessions

### 🎭 Dynamic Personality
Saturnia features context-aware quirks that respond to:
- Success and excitement
- Confusion and debugging moments
- Programming discussions
- General conversation flow

### 🌐 Multiple Interfaces
- **CLI**: Command-line chat interface
- **Web UI**: Flask-based web interface with clean chat design
- **REST API**: JSON endpoint for integration with other frontends

## Project Structure

```
ai-or-is-it/
├── app/
│   └── core/
│       ├── brain.py                    # Main conversation orchestration
│       ├── personality.py              # Saturnia's personality definition
│       ├── quirks.py                   # Context-aware personality quirks
│       ├── memory.py                   # Persistent memory system
│       ├── router.py                   # Intent routing
│       ├── math_engine.py              # Basic arithmetic
│       ├── algebra_engine.py           # Linear algebra solver
│       ├── quadratic_engine.py         # Quadratic equation solver
│       ├── fraction_algebra_engine.py  # Fraction equation solver
│       ├── system_algebra_engine.py    # System of equations solver
│       ├── power_root_engine.py        # Powers and roots
│       └── web.py                      # Flask web interface
├── docs/
│   └── personality.md                  # Detailed personality documentation
├── main.py                             # CLI entry point
├── requirements.txt                    # Python dependencies
└── .env                                # Environment configuration (GEMINI_API_KEY)
```

## Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/ai-or-is-it.git
cd ai-or-is-it
```

2. **Create a virtual environment**
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**

Create a `.env` file in the project root:
```
GEMINI_API_KEY=your_gemini_api_key_here
```

Get your Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey).

## Usage

### Command-Line Interface

Run the CLI chat:
```bash
python main.py
```

Type your messages and press Enter. Type `exit` to quit.

### Web Interface

Start the web server:
```bash
python app/core/web.py
```

Open your browser to `http://localhost:5000`

### API Endpoint

Send POST requests to `/api/chat`:
```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is 2 + 2?"}'
```

Response:
```json
{
  "response": "4"
}
```

## Example Interactions

### Basic Math
```
You: What is 25 * 4?
AI: 100
```

### Algebra
```
You: Solve 2x + 5 = 13
AI: x = 4.0
```

### Memory
```
You: My name is Alex
AI: Nice to meet you, Alex.

You: What's my name?
AI: Your name is Alex.
```

### Conversation
```
You: What do you think about Python?
AI: Python is an excellent language for learning and building practical applications...
```

## Personality

Saturnia is designed to be:

- **Curious**: Actively seeks information and asks follow-up questions
- **Helpful**: Prioritizes usefulness in every response
- **Honest**: Admits uncertainty rather than guessing
- **Playful**: Adds appropriate humor without being distracting
- **Transparent**: Openly identifies as an AI without pretending to be human

See `docs/personality.md` for detailed personality guidelines.

## Dependencies

- **Flask**: Web framework for the web interface
- **python-dotenv**: Environment variable management
- **google-generativeai**: Google Gemini API client
- **Jinja2**: Template engine (Flask dependency)
- **Werkzeug**: WSGI utilities (Flask dependency)

## Development

### Running Tests
```bash
python app/core/test_math.py
```

### Memory Management

Memory is stored in `saturnia_memory.json` in the project root. To clear memory, delete this file or use the memory management functions in the code.

### Adding New Math Engines

1. Create a new engine file in `app/core/`
2. Implement a `solve(message)` function that returns a dict with `{"answer": result}` or `None`
3. Import and call it in `brain.py` before the Gemini API call

## Contributing

This is an experimental project. Contributions, ideas, and feedback are welcome.

## License

This project is open source. Feel free to use and modify as needed.

## Acknowledgments

- Powered by Google's Gemini API
- Built with Flask web framework
- Inspired by the question: "AI or is it?" 🪐

---

**Note**: This project requires a valid Gemini API key. Make sure to keep your API key secure and never commit it to version control.
>>>>>>> 3db732d (chore: checkpoint before controlled AI development)
