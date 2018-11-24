# Generate documentation
doc:
	@$(MAKE) -C docs html

serve-doc:
	@cd docs/_build/html && python3 -m http.server 5000


# Unit test configuration
# defeats the purpose of using pytest for test discovery, consider refactoring test layout
CORE_TESTS += test/test_cryptle.py
CORE_TESTS += test/test_event.py
CORE_TESTS += test/test_metric.py

PLUGIN_TESTS += test/test_paper.py

# tests that takes a long time e.g. IO intensive
SLOW_TESTS += test/test_feed.py
SLOW_TESTS += test/test_timeseries.py
SLOW_TESTS += test/test_clock.py

UNIT_TESTS = $(CORE_TESTS) $(PLUGIN_TESTS)
ALL_TESTS  = $(CORE_TESTS) $(PLUGIN_TESTS) $(SLOW_TESTS)

test:
	@pytest $(UNIT_TESTS)

testplugin:
	@pytest $(PLUGIN_TESTS)

testslow:
	@pytest $(SLOW_TESTS)

testall:
	@pytest $(ALL_TESTS)

test_%:
	@pytest test/$@.py --rootdir=./


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


.PHONY: doc test testall testslow testpluging clean lint uml
