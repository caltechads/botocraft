clean:
	rm -rf *.tar.gz dist build *.egg-info *.rpm
	find . -name "*.pyc" | xargs rm
	find . -name "__pycache__" | xargs rm -rf

compile: uv.lock
	@uv pip compile --group docs pyproject.toml -o requirements.txt

release: clean
	@bin/release.sh

tox:
	# create a tox pyenv virtualenv based on 3.7.x
	# install tox and tox-pyenv in that ve
	# activate that ve before running this
	@tox

napoleon-gate:
	@python bin/check_napoleon_gate.py

napoleon-gate-strict:
	@python bin/check_napoleon_gate.py --strict

napoleon-gate-baseline:
	@python bin/check_napoleon_gate.py --write-baseline
