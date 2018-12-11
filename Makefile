# Generate documentation
doc:
	@$(MAKE) -C docs html

servedoc: doc
	@cd docs/_build/html && \
	    python3 -m webbrowser http://localhost:5000 && \
	    python3 -m http.server 5000


# Unit test configuration
test:
	@pytest test/unit

# runs only integration tests
testint:
	@pytest test/integration

# finds all tests with test discovery
testall:
	@pytest test

# run specific unit test
test_%:
	@pytest test/unit/$@.py --rootdir=./


# Linting configuration
PYLINT_DISABLES := C      # Ignore convention linting
PYLINT_DISABLES += W0221  # Ignore warnings of function signature overloading
PYLINT_DISABLES += E1205  # Ignore errors of logging args since we're using custom log formatting
# support for str.format() log message format will be in the next release of pylint

comma := ,
empty :=
space := $(empty) $(empty)
PYLINT_DISABLES_FINAL = $(subst $(space),$(comma),$(strip $(PYLINT_DISABLES)))

lint:
	@pylint cryptle \
	    --output-format=colorized \
	    --disable=$(PYLINT_DISABLES_FINAL) \
	    || true

PROJECT := cryptle
CLASS_DIAG := classes_$(PROJECT)
PACK_DIAG  := packages_$(PROJECT)


# Utililies
uml:
	@pyreverse -k cryptle -p $(PROJECT)
	@dot -Tpng $(CLASS_DIAG).dot > $(CLASS_DIAG).png
	@dot -Tpng $(PACK_DIAG).dot > $(PACK_DIAG).png
	@rm $(CLASS_DIAG).dot $(PACK_DIAG).dot

clean:
	rm -rf **/__pycache__
	rm -f $(CLASS_DIAG).png $(PACK_DIAG).png
	$(MAKE) -C docs clean


.PHONY: install doc test testall testslow testpluging clean lint uml
