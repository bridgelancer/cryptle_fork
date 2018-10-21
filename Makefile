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

lint:
	@pylint cryptle

clean:
	rm -rf **/__pycache__
	$(MAKE) -C docs clean

.PHONY: doc test clean lint
