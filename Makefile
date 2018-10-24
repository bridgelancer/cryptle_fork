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
	rm $(CLASS_DIAG).png $(PACK_DIAG).png
	$(MAKE) -C docs clean

.PHONY: doc test clean lint uml
