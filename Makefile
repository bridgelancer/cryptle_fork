# Generate documentation
doc:
	@$(MAKE) -C docs html


# Unit test configuration
# defeats the purpose of using pytest for test discovery, consider refactoring test layout
CORE_TESTS += test/test_cryptle.py
CORE_TESTS += test/test_event.py
CORE_TESTS += test/test_metric.py
CORE_TESTS += test/test_registry.py
CORE_TESTS += test/test_timeseries.py

PLUGIN_TESTS += test/test_clock.py
PLUGIN_TESTS += test/test_paper.py

IO_TESTS += test_feed.py

UNIT_TESTS = $(CORE_TESTS) $(PLUGIN_TESTS)
ALL_TESTS  = $(CORE_TESTS) $(PLUGIN_TESTS) $(IO_TESTS)

test:
	@pytest $(UNIT_TESTS)

testplugin:
	@pytest $(PLUGIN_TESTS)

testio:
	@pytest $(IO_TESTS)

testall:
	@pytest $(ALL_TESTS)

test_%:
	@pytest test/$@.py --rootdir=./


# Linting configuration
PYLINT_DISABLES := C  # Ignore convention warnings

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


.PHONY: doc test testall testio clean lint uml
