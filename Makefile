clean:
	rm -rf *.tar.gz dist build *.egg-info *.rpm
	find . -name "*.pyc" | xargs rm
	find . -name "__pycache__" | xargs rm -rf

dist: clean
	@python -m build --sdist --wheel

pypi: dist
	@twine upload dist/*

release: pypi

tox:
	# create a tox pyenv virtualenv based on 3.7.x
	# install tox and tox-pyenv in that ve
	# activate that ve before running this
	@tox

