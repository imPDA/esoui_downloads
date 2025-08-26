.PHONY: up down
DC = docker-compose -f docker-compose.yaml

up:
	${DC} up -d --build

down:
	${DC} down