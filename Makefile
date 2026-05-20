.PHONY: dev prod down clean rebuild
help:
	@echo "Available commands:"
	@echo "  make dev                  - Start development environment"
	@echo "  make prod                 - Start production environment"
	@echo "  make down                 - Stop and remove all containers"
	@echo "  make clean                - Remove all containers, networks, and volumes"
	@echo "  make rebuild              - Rebuild and restart all containers"


dev:
	docker compose -f docker-compose.dev.yml up -d

prod:
	docker compose -f docker-compose.yml up -d

down:
	docker compose down

clean:
	docker compose down -v --rmi all --remove-orphans

rebuild:
	docker compose down
	docker compose build --no-cache
	docker compose up -d
