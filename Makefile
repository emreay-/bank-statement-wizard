.PHONY: build
build:
	docker build . -t bank_statement_wizard.dev

.PHONY: run
run: build
	docker run -it \
		-t bank_statement_wizard.dev bswiz
