# Workflow Backend

A production-grade workflow engine built with FastAPI and LangGraph.

## Features

- Parse visual node graphs into executable LangGraph workflows
- Run workflows step-by-step with conversation state
- Persist workflows, runs, steps, and variables in Supabase
- Strong OOP design with clean architecture

## Setup

### Prerequisites

1. Python 3.11 or higher
2. [Poetry](https://python-poetry.org/docs/#installation) for dependency management
3. Supabase account for database
4. OpenAI API key for LLM integration

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd workflow-backend
   ```

2. Install dependencies with Poetry:
   ```bash
   poetry install
   ```

   For PostgreSQL support:
   ```bash
   poetry install --extras postgres
   ```

3. Copy `.env.example` to `.env` and fill in your credentials:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

4. Run database migrations:
   ```bash
   poetry run python scripts/init_db.py
   ```

### Running the Server

Start the development server:
```bash
# With auto-reload
poetry run start --reload

# Production mode
poetry run start
```

Or use uvicorn directly:
```bash
poetry run uvicorn app.main:app --reload
```

## Development

### Virtual Environment

Poetry automatically manages a virtual environment. To activate it:
```bash
poetry shell
```

### Dependencies

Add new dependencies:
```bash
poetry add package-name
poetry add --group dev pytest  # dev dependencies
```

Update dependencies:
```bash
poetry update
```

### Testing

Run tests with coverage:
```bash
poetry run pytest
```

### Code Quality

Format code:
```bash
poetry run black app tests
```

Run type checking:
```bash
poetry run mypy app tests
```

Run linting:
```bash
poetry run ruff check app tests
```

## API Usage

### Create a Workflow

```bash
curl -X POST http://localhost:8000/workflows \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Greeting",
    "version": 1,
    "variables": {},
    "nodes": [
      {
        "id": "ask_name",
        "type": "Prompt",
        "config": {
          "text": "Hi! What's your name?"
        },
        "next": "reply"
      },
      {
        "id": "reply",
        "type": "Output",
        "config": {
          "text": "Thanks, {{name}}!"
        }
      }
    ]
  }'
```

### Start a Run

```bash
curl -X POST http://localhost:8000/runs \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": "greeting-workflow",
    "input_text": null
  }'
```

### Step Through a Run

```bash
curl -X POST http://localhost:8000/runs/{run_id}/step \
  -H "Content-Type: application/json" \
  -d '{
    "user_text": "Alice"
  }'
```

## Architecture

The project follows a clean architecture pattern:

- `api/`: FastAPI routes and dependencies
- `core/`: Core workflow engine and LangGraph integration
- `domain/`: Domain models and node implementations
- `infra/`: Infrastructure concerns (database, LLM clients)
- `services/`: Application services
- `utils/`: Shared utilities

## License

MIT

