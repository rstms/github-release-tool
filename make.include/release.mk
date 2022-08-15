# publish - build package and publish

# create distributable files if sources have changed
.PHONY: dist 
dist: .dist requirements.txt
.dist:	gitclean tox
	@echo Building $(project)
	flit build
	@touch $@

RELEASE := release\
  --organization $(organization)\
  --repository $(repo)\
  --token $(GITHUB_DEPLOY_TOKEN)\
  --module-dir $(MODULE_DIR)\
  --wheel-dir ./dist\
  --version $(version) 

dist/$(project)-$(version)-*.whl: dist

dist/$(project)-$(version)-release.json: dist/$(project)-$(version)-*.whl
	@echo pushing Release $(project) v$(version) to github...
	$(RELEASE) create --force | tee $@
	$(RELEASE) upload --force | tee -a $*

## create a github release from the current version
release: dist/$(project)-$(version)-release.json

# clean up the publish temp files
release-clean:
	rm -f .dist
	rm -rf .tox
	rm -f requirements*.txt
