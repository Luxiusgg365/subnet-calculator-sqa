DC = env UID=$$(id -u) GID=$$(id -g) docker compose

.PHONY: dev up stop logs test cov rebuild prod-build prod-run prod-stop smoke

dev:        ## jalankan dev, log di terminal (Ctrl+C untuk berhenti)
	$(DC) up --build
up:         ## jalankan dev di latar belakang
	$(DC) up -d --build
stop:
	$(DC) down
logs:
	$(DC) logs -f dev
test:       ## jalankan pytest di dalam container
	$(DC) run --rm -e APP_ENV="" dev pytest -v
cov:
	$(DC) run --rm -e APP_ENV="" dev pytest test_main.py -v --cov=main --cov-report=term-missing
rebuild:    ## setelah pyproject.toml / uv.lock berubah
	$(DC) build --no-cache dev
prod-build:
	docker build -t subnet-calculator .
prod-run:   ## image produksi di http://localhost:8180
	docker run -d --name subnet-prod -p 8180:8000 subnet-calculator
prod-stop:
	docker rm -f subnet-prod
smoke:      ## smoke test ke dev (port 8100)
	uv run python scripts/smoke_test.py http://127.0.0.1:8100
