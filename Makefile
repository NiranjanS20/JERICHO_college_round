.PHONY: dev test demo install lint build-frontend

# Install dependencies for both backend and frontend
install:
	pip install -r requirements.txt
	cd frontend && npm install

# Run the backend API development server
dev:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run the frontend development server
dev-frontend:
	cd frontend && npm run dev

# Run the entire pytest test suite (45 tests)
test:
	cd backend && python3 -m pytest tests/ -v --tb=short

# Load pre-run demo cache and start server (zero Gemini API calls needed)
demo:
	cd backend && python3 run_demo.py

# Build production React frontend
build-frontend:
	cd frontend && npm run build

# Code style check
lint:
	cd backend && python3 -m ruff check app/ tests/ || true
