SHELL := /bin/bash

.PHONY: up down logs build orchestrator-dev

up:
	docker compose up -d --build

down:
	docker compose down -v

logs:
	docker compose logs -f --tail=200

build:
	docker compose build

orchestrator-dev:
	python -m pip install -r services/orchestrator/requirements.txt && \
	uvicorn services.orchestrator.app.main:app --reload --host 0.0.0.0 --port 8080


