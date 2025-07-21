.PHONY: restore
restore:
	uv sync

.PHONY: run
run:
	./.venv/bin/python -m src.main
