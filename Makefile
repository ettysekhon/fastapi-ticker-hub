.PHONY: format lint test ci clean start

format:
	uv run black .
	uv run ruff check . --fix

lint:
	uv run ruff check .

test:
	./test.sh $(ARGS)

ci: format lint test

clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	rm -rf .pytest_cache .coverage coverage.xml dist

start:
	docker compose up --build
