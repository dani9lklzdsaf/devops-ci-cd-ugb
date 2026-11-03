.PHONY: up down logs build test deploy

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f

build:
	docker compose build

test:
	curl -f http://localhost/health
	curl -f http://localhost/

deploy:
	docker compose pull
	docker compose up -d
