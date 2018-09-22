.PHONY: doc awsdoc test

doc:
	@$(MAKE) -C docs html

awsdoc: doc
	@aws s3 sync ./docs/_build/html s3://cryptle-docs

test: test-all

test-all:
	@pytest

test-event:
	@pytest test/test_event.py --rootdir=./

test-feed:
	@pytest test/test_feed.py --rootdir=./
