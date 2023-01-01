# publish - build package and publish

# create distributable files if sources have changed

.PHONY: dist 
dist: $(if $(DISABLE_TOX),,tox) .dist

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

release_status=dist/$(project)-$(version)-release.json
asset_status=dist/$(project)-$(version)-asset.json

.release: dist/*.whl
	@echo pushing Release $(project) v$(version) to github...
	$(call gitclean)
	$(RELEASE) create --force >$(release_status)
	cat $(release_status)
	$(RELEASE) upload --force >$(asset_status)
	cat $(asset_status)
	@touch $@


# clean up the publish temp files
release-clean:
	rm -f .dist
	rm -f .release
	rm -rf .tox
	rm -f requirements*.txt
