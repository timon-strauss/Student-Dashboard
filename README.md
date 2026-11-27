# Student Dashboard

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
cd frontend && npm install
```

## Start

Flashcards backend (port 8000):

```bash
cd flashcards && ../.venv/bin/uvicorn app.main:app --reload --port 8000
```

Grades backend (port 8001):

```bash
cd grades && ../.venv/bin/uvicorn app.main:app --reload --port 8001
```

Frontend (http://localhost:5173):

```bash
cd frontend && npm run dev
```

## Tests

```bash
cd flashcards && ../.venv/bin/python -m pytest
cd grades && ../.venv/bin/python -m pytest
```
