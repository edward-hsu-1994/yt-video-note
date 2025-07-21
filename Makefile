.PHONY: restore
restore:
	uv sync

.PHONY: run
run:
	python -m src.main
