.PHONY: dev down migrate seed test test-web build backup

dev:
	docker compose -f docker-compose.prod.yml up -d --build
down:
	docker compose -f docker-compose.prod.yml down
migrate:
	docker compose -f docker-compose.prod.yml exec api alembic upgrade head
seed:
	docker compose -f docker-compose.prod.yml exec api python -m app.seed.seed_trails
test:
	cd api && python -m pytest -q
test-web:
	cd web && npm test
build:
	cd web && npm run build
backup:
	sh scripts/backup.sh
