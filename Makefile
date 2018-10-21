doc:
	@$(MAKE) -C docs html

test:
	@pytest --ignore test/test_feed.py

test-all:
	@pytest

test-event:
	@pytest test/test_event.py --rootdir=./

test-feed:
	@pytest test/test_feed.py --rootdir=./


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

clean:
	rm -rf **/__pycache__
	$(MAKE) -C docs clean

.PHONY: doc test clean lint
