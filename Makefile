APP?=server
PI?=medhi@marland
WORKER?=medhi@worker
IMAGE?=ghcr.io/your-username/loumina-$(APP)

.PHONY: dev lint test build push deploy-pi deploy-worker backup-qdrant restore-qdrant

dev:  ## lancer l'app server en dev
	python apps/server/main.py

lint:
	pre-commit run -a

test:
	pytest -q

build:
	docker build -t $(IMAGE):$(shell cat VERSION) -f apps/$(APP)/Dockerfile .

push: build
	docker push $(IMAGE):$(shell cat VERSION)

deploy-pi:
	ssh $(PI) 'cd ~/loumina-marland && docker compose -f infra/compose/compose.pi.yml pull && docker compose -f infra/compose/compose.pi.yml up -d'

deploy-worker:
	ssh $(WORKER) 'cd ~/loumina-marland && docker compose -f infra/compose/compose.worker.yml pull && docker compose -f infra/compose/compose.worker.yml up -d'

backup-qdrant:
	bash infra/scripts/qdrant_snapshot.sh backup

restore-qdrant:
	bash infra/scripts/qdrant_snapshot.sh restore $(SNAP)
