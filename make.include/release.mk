# publish - build package and publish

# create distributable files if sources have changed
.PHONY: dist 
dist: .dist requirements.txt
.dist:	gitclean tox
	@echo Building $(project)
	flit build
	@touch $@

release_args = '{\
  "tag_name": "v$(version)",\
  "target_commitish": "$(branch)",\
  "name": "v$(version)",\
  "body": "Release of version $(version)",\
  "draft": false,\
  "prerelease": false\
}'
release_url = https://api.github.com/repos/$(organization)/$(repo)/releases
release_header = -H 'Authorization: token ${GITHUB_DEPLOY_TOKEN}'

dist/$(project)-$(version)-*.whl: dist

dist/$(project)-$(version)-release.json: dist/$(project)-$(version)-*.whl
	@echo pushing Release $(project) v$(version) to github...
	release --force  --organization $(organization) --repository $(repo) --token $(GITHUB_DEPLOY_TOKEN) \
	  --module-dir $(MODULE_DIR) --wheel-dir ./dist
	  create --version $(version) --branch $(branch) $< | tee $@
	release --force upload | tee -a $*

## create a github release from the current version
release: dist/$(project)-$(version)-release.json

# clean up the publish temp files
release-clean:
	rm -f .dist
	rm -rf .tox
	rm -f requirements*.txt
