all:
	@python3 setup.py install
	@-rm -rf build dist sshmgr.egg-info
