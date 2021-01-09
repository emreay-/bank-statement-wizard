.PHONY: build
build:
	docker build -t eay/bank_statement_wizard .


.PHONY: buildDev
buildDev: build
	docker build -f Dockerfile.dev --build-arg BSWIZ_IMAGE=eay/bank_statement_wizard -t eay/bank_statement_wizard.dev .


.PHONY: run
run: build
	docker run -it \
		-t eay/bank_statement_wizard bswiz


.PHONY: runUnitTestsDocker
runUnitTestsDocker: buildDev
	docker run -it -t eay/bank_statement_wizard.dev coverage run --rcfile=./rcfile -m pytest -s ./test/ && coverage report


.PHONY: devInstall
devInstall:
	pip3 install -e .


.PHONY: runUnitTests
runUnitTests: devInstall
	coverage run --rcfile=./rcfile -m pytest -s ./test/ && coverage report
