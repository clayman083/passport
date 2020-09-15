.PHONY: build clean clean-test clean-pyc clean-build
NAME	:= ghcr.io/clayman-micro/passport
VERSION ?= latest


clean: clean-build clean-image clean-pyc clean-test

clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

clean-image:
	docker images -qf dangling=true | xargs docker rmi

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test:
	rm -fr .tox/
	rm -f .coverage
	rm -fr tests/coverage
	rm -f tests/coverage.xml

install: clean
	poetry install

lint:
	poetry run flake8 passport tests
	poetry run mypy passport tests

run:
	poetry run python3 -m passport --conf-dir=./conf server run -t develop -t 'traefik.enable=true' -t 'traefik.http.routers.passport.rule=Host(`passport.dev.clayman.pro`)' -t 'traefik.http.routers.passport.entrypoints=web' -t 'traefik.http.routers.passport.service=passport' -t 'traefik.http.routers.passport.middlewares=passport-redirect@consulcatalog' -t 'traefik.http.routers.passport-secure.rule=Host(`passport.dev.clayman.pro`)' -t 'traefik.http.routers.passport-secure.entrypoints=websecure' -t 'traefik.http.routers.passport-secure.service=passport' -t 'traefik.http.routers.passport-secure.tls=true' -t 'traefik.http.middlewares.passport-redirect.redirectscheme.scheme=https' -t 'traefik.http.middlewares.passport-redirect.redirectscheme.permanent=true' -t 'traefik.http.middlewares.passport-cors.headers.accesscontrolallowcredentials=true' -t 'traefik.http.middlewares.passport-cors.headers.accesscontrolallowheaders=Content-Type,X-Access-Token,X-Refresh-Token' -t 'traefik.http.middlewares.passport-cors.headers.accesscontrolexposeheaders=Content-Type,X-Access-Token,X-Refresh-Token' -t 'traefik.http.middlewares.passport-cors.headers.accesscontrolallowmethods=GET,OPTIONS,PUT,POST,DELETE' -t 'traefik.http.middlewares.passport-cors.headers.accesscontrolalloworiginlist=https://passport.dev.clayman.pro,http://localhost:3000' -t 'traefik.http.middlewares.passport-cors.headers.accesscontrolmaxage=100' -t 'traefik.http.middlewares.passport-cors.headers.addvaryheader=true' -t 'traefik.http.routers.passport-secure.middlewares=passport-cors@consulcatalog'

test:
	py.test

test-all:
	tox -- --pg-image=postgres:12-alpine

build:
	docker build -t ${NAME} .
	docker tag ${NAME} ${NAME}:$(VERSION)

publish:
	docker login -u $(DOCKER_USER) -p $(DOCKER_PASS)
	docker push ${NAME}
