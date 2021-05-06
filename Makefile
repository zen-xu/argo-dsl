.PHONY: generate-api test

OPENAPI_SPEC_URL := https://raw.githubusercontent.com/argoproj/argo-workflows/stable/api/openapi-spec/swagger.json

generate-api:
	rm -rf argo_dsl/api
	datamodel-codegen --disable-timestamp --validation --url $(OPENAPI_SPEC_URL) --output argo_dsl/api
	black -q argo_dsl/api

test:
	poetry run pytest --cov=argo_dsl tests/ -sq