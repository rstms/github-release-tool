# publish - build package and publish

# create distributable files if sources have changed

.PHONY: dist 
dist: .dist 

.dist: gitclean
	@echo Building $(project)
	$(MAKE) tox
	flit build
	@touch $@

RELEASE = release\
  --organization $(organization)\
  --repository $(repo)\
  --token $(GITHUB_TOKEN)\
  --module-dir $(MODULE_DIR)\
  --wheel-dir ./dist\
  --version $(version) 


## create a github release from the current version
.PHONY: release
release: .release

.release: dist
	@echo pushing Release $(project) v$(version) to github...
	$(RELEASE) create --force | tee dist/$(project)-$(version)-release.json
	$(RELEASE) upload --force | tee dist/$(project)-$(version)-asset.json
	@touch $@


# clean up the publish temp files
release-clean:
	rm -f .dist
	rm -f .release
	rm -rf .tox
	rm -f requirements*.txt
