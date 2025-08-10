
.PHONY: run dev test fmt lint docker

dev:
	uvicorn app:app --reload

fmt:
	black .

lint:
	flake8 --exclude=.venv --ignore=E501,W503 .

docker:
	docker build -t rtg-app .

run:
	python -m uvicorn app:app --host 0.0.0.0 --port 8000
