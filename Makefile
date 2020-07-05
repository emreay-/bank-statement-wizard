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


.PHONY: runUnitTests
runUnitTests: buildDev
	docker run -it -t eay/bank_statement_wizard.dev py.test .
