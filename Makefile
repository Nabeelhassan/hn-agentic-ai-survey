SHELL := /bin/bash
PY := cd pipeline && uv run python -m hn_agents.cli

.PHONY: fetch normalize taxonomy extract aggregate eval snapshot dashboard-data dev build test clean

fetch:
	$(PY) fetch

normalize:
	$(PY) normalize

taxonomy:
	$(PY) taxonomy-harvest

extract:
	$(PY) extract

aggregate:
	$(PY) aggregate

eval:
	$(PY) eval

snapshot: fetch normalize aggregate

dashboard-data:
	$(PY) dashboard-data

dev: dashboard-data
	cd dashboard && npm run dev

build: dashboard-data
	cd dashboard && npm run build

test:
	cd pipeline && uv run pytest -q

clean:
	rm -rf dashboard/dist dashboard/public/data
