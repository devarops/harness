.PHONY: \
		clean \
		init \
		install \
		tests

module = harness

clean:
	rm --force --recursive .*_cache
	rm --force --recursive *.egg-info
	rm --force --recursive ${module}/__pycache__
	rm --force --recursive tests/__pycache__

init: install tests

install:
	pipx install --editable . --force

tests:
	pytest --verbose
