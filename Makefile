.PHONY: setup lint test serve coverage

setup:
	python -m venv venv && source venv/bin/activate && pip install -r requirements.txt && pip install pre-commit
	npm --prefix src/frontend install

lint:
	pre-commit run --all-files --show-diff-on-failure

test:
	pytest -q

serve:
	uvicorn src.backend.app:app --reload

coverage:
	pytest --cov=src --cov-report=term-missing
