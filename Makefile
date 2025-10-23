.PHONY: up down app
DC = docker-compose -f docker-compose.yaml

app:
	${DC} up app -d --build

up:
	${DC} up -d --build

down:
	${DC} down