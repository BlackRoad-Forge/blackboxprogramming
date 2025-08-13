.PHONY: setup lint test serve coverage frontend

# Create a Python virtual environment, install backend and frontend dependencies and set up pre commit hooks.
setup:
    python -m venv venv && \
    source venv/bin/activate && \
    pip install -r requirements.txt && \
    pip install pre-commit && \
    cd src/frontend && npm install --no-audit --no-fund && cd -

# Run code quality checks via pre commit.
lint:
    pre-commit run --all-files --show-diff-on-failure

# Execute the Python test suite.
test:
    pytest -q

# Launch the development server for the backend. The uvicorn reload flag enables hot reload on file changes.
serve:
    uvicorn src.backend.app:app --reload

# Generate a test coverage report.
coverage:
    pytest --cov=src --cov-report=term-missing

# Build the frontend assets using npm. The resulting files will be placed in src/frontend/dist.
frontend:
    cd src/frontend && npm run build
