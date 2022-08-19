# version - automatic version management
 
# - Prevent version changes with uncommited changes
# - tag and commit version changes
# - Use 'lightweight tags'


bumpversion = bumpversion --allow-dirty $(1)

## bump patch level
bump-patch: requirements.txt timestamp
	$(call bumpversion,patch)
	git add requirements*.txt
	git push

## bump minor version, reset patch to zero
bump-minor: requirements.txt timestamp
	$(call bumpversion,minor)
	git add requirements*.txt
	git push
	
## bump version, reset minor and patch to zero
bump-major: requirements.txt timestamp
	$(call bumpversion,major)
	git add requirements*.txt
	git push

# update timestamp if sources have changed and rewrite requirements.txt
timestamp: .timestamp
.timestamp: $(src)
	$(call gitclean)
	sed -E -i $(project)/version.py -e "s/(.*__timestamp__.*=).*/\1 \"$$(date --rfc-3339=seconds)\"/"
	git add $(project)/version.py
	@touch $@
	@echo "Updated version.py timestamp and requirements.txt"

# clean up version tempfiles
version-clean:
	rm -f .timestamp
