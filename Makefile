# Unit test configuration (pytest)
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


# Generate documentation
doc:
	@$(MAKE) -C docs html

servedoc: doc
	@cd docs/_build/html && \
	    python3 -m webbrowser http://localhost:5000 && \
	    python3 -m http.server 5000


# Linting configuration (pylint)
PYLINT_DISABLES := C      # Ignore convention linting
PYLINT_DISABLES += W0221  # Ignore warnings of function signature overloading
# support for str.format() log message format will be in the next release of pylint
PYLINT_DISABLES += E1205  # Ignore errors of logging args since we're using custom log formatting

comma := ,
empty :=
space := $(empty) $(empty)
PYLINT_DISABLES_FINAL = $(subst $(space),$(comma),$(strip $(PYLINT_DISABLES)))

lint:
	@pylint cryptle \
	    --output-format=colorized \
	    --disable=$(PYLINT_DISABLES_FINAL) \
	    --exit-zero


# Use black to auto-format python code
format:
	@black -S cryptle

checkformat:
	@black --diff -S cryptle


# Utililies
# (pyreverse comes with pylint, dot needs to separately installed)
PROJECT := cryptle
CLASS_DIAG := classes_$(PROJECT)
PACK_DIAG  := packages_$(PROJECT)

uml:
	@pyreverse -k cryptle -p $(PROJECT)
	@dot -Tpng $(CLASS_DIAG).dot > $(CLASS_DIAG).png
	@dot -Tpng $(PACK_DIAG).dot > $(PACK_DIAG).png
	@rm $(CLASS_DIAG).dot $(PACK_DIAG).dot

clean:
	rm -rf **/__pycache__
	rm -f $(CLASS_DIAG).png $(PACK_DIAG).png
	$(MAKE) -C docs clean


.PHONY: install doc test testall testslow testpluging clean lint uml format
