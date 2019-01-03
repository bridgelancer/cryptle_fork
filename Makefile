# Unit test configuration (pytest)
#   config goes to pytest.ini (pyproject.toml to be supported)
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


# Pylint used for linting
#   configs goes to .pylintrc
lint:
	@pylint cryptle


# Black keeps consistent style with enforced formatting
#   configs goes to pyproject.toml
format:
	@black cryptle


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
