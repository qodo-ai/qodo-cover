# Makefile
SITE_PACKAGES=$(shell python3 -c "import wandb, os; print(os.path.dirname(wandb.__file__))")
DIFF_COVER_TEMPLATES=$(shell python -c "import site; print(site.getsitepackages()[0])")
TOML_FILES=$(shell find cover_agent/settings -name "*.toml" | sed 's/.*/-\-add-data "&:."/' | tr '\n' ' ')

.PHONY: test build installer

# Run unit tests with Pytest
test:
	poetry run pytest --junitxml=testLog.xml --cov=cover_agent --cov-report=xml:cobertura.xml --cov-report=term --cov-fail-under=65 --log-cli-level=INFO

# Use Python Black to format python files
format:
	black .

# Generate wheel file using poetry build command
build:
	poetry build

# Build an executable using Pyinstaller
installer:
	poetry run pyinstaller \
		--add-data "cover_agent/version.txt:." \
		$(TOML_FILES) \
		--add-data "$(SITE_PACKAGES)/vendor:wandb/vendor" \
		--add-data "build_helpers/anthropic_tokenizer.json:litellm/litellm_core_utils/tokenizers" \
		--add-data "$(DIFF_COVER_TEMPLATES)/diff_cover/templates:diff_cover/templates" \
		--hidden-import=tiktoken_ext.openai_public \
		--hidden-import=tiktoken_ext \
		--hidden-import=wandb \
		--hidden-import=tree_sitter \
		--hidden-import=wandb_gql \
		--onefile \
		--name cover-agent \
		cover_agent/main.py
