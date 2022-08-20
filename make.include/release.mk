# publish - build package and publish

# create distributable files if sources have changed

.PHONY: dist 
dist: tox .dist

.dist:	$(src)
	$(call gitclean)
	@echo Building $(project)
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
release: dist .release

.release: dist/*.whl
	@echo pushing Release $(project) v$(version) to github...
	$(call gitclean)
	$(RELEASE) create --force >dist/$(project)-$(version)-release.json
	$(RELEASE) upload --force >dist/$(project)-$(version)-asset.json
	@touch $@


# clean up the publish temp files
release-clean:
	rm -f .dist
	rm -f .release
	rm -rf .tox
	rm -f requirements*.txt
