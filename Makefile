# SOLARAEUS developer entry points.
#
# Everything a contributor needs is reachable from here, so CI and humans run
# identical commands. `make help` lists the targets.

PYTHON ?= python
PIP    ?= $(PYTHON) -m pip
CITY   ?= church_street_bengaluru
PIPELINE ?= static

.DEFAULT_GOAL := help
.PHONY: help install install-dev lock lint lint-debt format types types-report test test-fast test-slow golden golden-capture doctor city viewer viewer-install viewer-test docker ci clean

help: ## list available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

install: ## install the package (CPU only) into the active environment
	$(PIP) install --upgrade pip
	$(PIP) install -e .

install-dev: ## install the package with every development and optional extra
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[all]"
	pre-commit install

lock: ## regenerate the pinned lockfile from the current environment
	$(PYTHON) tools/lock.py

lint: ## run the enforced ruff checks (passes on the whole tree)
	$(PYTHON) -m ruff check src tests tools

lint-debt: ## list the deferred modernisation findings (non-blocking)
	$(PYTHON) -m ruff check src tests tools \
		--select UP,PTH,SIM,RET,C4,ARG,W --statistics --exit-zero

format: ## auto-format with ruff
	$(PYTHON) -m ruff format src tests tools
	$(PYTHON) -m ruff check --fix src tests tools

types: ## run mypy (gradual: strict on core contracts, lenient elsewhere)
	$(PYTHON) -m mypy

types-report: ## list every mypy error, including the not-yet-enforced backlog (never fails)
	-$(PYTHON) -m mypy --config-file tools/mypy-report.toml src

test: ## run the full test suite
	$(PYTHON) -m pytest

test-fast: ## run everything except slow tests
	$(PYTHON) -m pytest -m "not slow"

test-slow: ## run only the slow tests
	$(PYTHON) -m pytest -m "slow"

golden-capture: ## re-capture the golden-master baseline (DESTRUCTIVE; only when behaviour intentionally changes)
	@echo '!! overwriting the frozen baseline in tools/golden/baseline'
	$(PYTHON) tools/golden/golden.py capture --force

golden: ## verify physics outputs against the frozen golden master
	$(PYTHON) tools/golden/golden.py capture --out tools/golden/candidate
	$(PYTHON) tools/golden/golden.py compare --baseline tools/golden/baseline --out tools/golden/candidate

doctor: ## check the runtime environment (deps, GPU, data dirs)
	$(PYTHON) -m urban_comfort.cli doctor

city: ## run a pipeline for a city: make city CITY=slug PIPELINE=static
	$(PYTHON) -m urban_comfort.cli run --city $(CITY) --pipeline $(PIPELINE)

viewer-install: ## install the viewer's node dependencies
	cd viewer && npm ci

viewer: ## build and serve the viewer against exported city data
	cd viewer && npm run build
	$(PYTHON) -m urban_comfort.cli viewer serve

viewer-test: ## run viewer unit + end-to-end tests
	cd viewer && npm test

docker: ## build the CPU container image
	docker build -t solaraeus:cpu -f Dockerfile .

ci: lint types test-fast golden ## what continuous integration runs

clean: ## remove caches and generated local artifacts
	$(PYTHON) tools/clean.py
