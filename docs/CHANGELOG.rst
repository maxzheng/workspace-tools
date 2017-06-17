Version 3.0.6
================================================================================

* Change option name to merge --downstreams and add more validation

Version 3.0.5
--------------------------------------------------------------------------------

* Switch to use click.echo instead of log.info
* Revert "Split config lists early"
  
  This reverts commit 1b2867dc2c5c33ecdc2c5c6e70e8a8f874e6ced1.
* Fix indent for dependency script

Version 3.0.4
--------------------------------------------------------------------------------

* Split config lists early
* Add more info on merge.branch config

Version 3.0.3
--------------------------------------------------------------------------------

* Add merge doc

Version 3.0.2
--------------------------------------------------------------------------------

* Set upstream or remote but not both when pushing
* Add merge command with option to merge to a list of user configured branches
* Add push --all-remotes option
* Reindent to use 4 spaces
* Some minor changes

Version 3.0.1
--------------------------------------------------------------------------------

* Add follow link

Version 3.0.0
--------------------------------------------------------------------------------

* Fix tests and bugs
* Remove review and wait commands.
  
  They are not easy to implement and does not provide that much value. Maybe later.
* Only delete child branches
* Many improvements for working with multiple branches
* Use autostash when doing update (git pull)
* Migrate to Python 3.x and add support for multiple projects per repo.
  
  And remove support for svn, git-svn.
* Add .eggs to .gitignore
* Sync / update

Version 1.0.11
================================================================================

* Log wait command output and allow them to be viewed with --log option

Version 1.0.10
--------------------------------------------------------------------------------

* Add --install-editable option to "ws test" and remove config.test.editable_products
* Sync changes from downstream
* Remove use of --download-cache option
* Set testpaths to "test"
* Add --name-only option and fix some bugs

Version 1.0.9
--------------------------------------------------------------------------------

* Add --rb to bump to be consistent with other commands and various test fixes
* Do sys.exit(1) if any repo failed to update instead of existing silently.
  
  Also check if package exists before including it in version display.

Version 1.0.8
--------------------------------------------------------------------------------

* Scope not implemented exception to base Wait class for review/publish event

Version 1.0.7
--------------------------------------------------------------------------------

* Run wait chaining actions in background
* Sort task view by repo/task

Version 1.0.6
--------------------------------------------------------------------------------

* Prompt user for commit msg if not given
* Ensure branch is assigned before use

Version 1.0.5
--------------------------------------------------------------------------------

* Add --push/--bump-in chaining options to wait command

Version 1.0.4
--------------------------------------------------------------------------------

* Support running tasks in background
* Detect if .pypirc has necessary info and prompt as needed. require=localconfig

Version 1.0.3
--------------------------------------------------------------------------------

* Fall back to use build results if there is no test result
* Skip style check if there is no style env
* Suppress stacktrace when getting ^C

Version 1.0.2
--------------------------------------------------------------------------------

* Display chaining options separately in help
* Run style check when running tests for commit
* Quote args to tv alias

Version 1.0.1
--------------------------------------------------------------------------------

* Centralize test result summary / evaluation logic

Version 1.0.0
--------------------------------------------------------------------------------

* Switch to class-based command architecture to simplify downstream customization

Version 0.8.19
================================================================================

* Check for branches before removing repo when cleaning
* Create config dir if not exists

Version 0.8.18
--------------------------------------------------------------------------------

* Check another directory for setup.cfg

Version 0.8.17
--------------------------------------------------------------------------------

* Add repo_url method to get remote repo url
* Redirect STDERR to STDOUT when running command with silent/return_output option

Version 0.8.16
--------------------------------------------------------------------------------

* Amend commit before running tests as tests might run long

Version 0.8.15
--------------------------------------------------------------------------------

* Exit early if test failed before commit
* Update doc

Version 0.8.14
--------------------------------------------------------------------------------

* Add install-only modifier for redevelop/recreate
* Update activate alias to work in different situations

Version 0.8.13
--------------------------------------------------------------------------------

* Revert removing */*/build dir during clean
* Add --test option to run tests before committing
* Use auto branch when bumping to support multiple bumps
* Add remove_all_products_except option for clean command
* Ensure dummy commit msg starts with "Empty commit"

Version 0.8.12
--------------------------------------------------------------------------------

* Use pip to list installed dependencies instead of pkg_resources

Version 0.8.11
--------------------------------------------------------------------------------

* Use existing msg field for dummy msg

Version 0.8.10
--------------------------------------------------------------------------------

* Allow dummy commit msg to be changed

Version 0.8.9
--------------------------------------------------------------------------------

* Add filter option for showing installed dependencies

Version 0.8.8
--------------------------------------------------------------------------------

* Use setup.cfg instead of setup.ws

Version 0.8.7
--------------------------------------------------------------------------------

* Remove test code

Version 0.8.6
--------------------------------------------------------------------------------

* Support custom product setup with setup.ws

Version 0.8.5
--------------------------------------------------------------------------------

* Simplify product group bootstrap with setup command

Version 0.8.4
--------------------------------------------------------------------------------

* Show progress for dependent tests

Version 0.8.3
--------------------------------------------------------------------------------

* Run dependent tests in parallel

Version 0.8.2
--------------------------------------------------------------------------------

* When bumping, only add/commit files updated by bump
* Only run transitive tests if current product is in editable_products list

Version 0.8.1
--------------------------------------------------------------------------------

* Update README

Version 0.8.0
--------------------------------------------------------------------------------

* Add skip_editable_install internal arg for test command
* Deprecate [test] scope_transitive_test_products with editable_products
* Deprecate [test] editable_product_dependencies with editable_products that is also used for scoping products that will install editables

Version 0.7.24
================================================================================

* Fix "-n 0" option for test command

Version 0.7.23
--------------------------------------------------------------------------------

* Fix repo detection in nested repos
* Skip auto branch for commit when already on a branch

Version 0.7.22
--------------------------------------------------------------------------------

* Better checking for clean repo that works for older git

Version 0.7.21
--------------------------------------------------------------------------------

* Perform product update in parallel
* Add remove_products_older_than_days option for clean command
* Add scope_transitive_test_products config option to scope transitive products to test

Version 0.7.20
--------------------------------------------------------------------------------

* Flush streamed test output

Version 0.7.19
--------------------------------------------------------------------------------

* Do not count one/two letter words when creating branch from commit msg

Version 0.7.18
--------------------------------------------------------------------------------

* Append error from subprocess to output

Version 0.7.17
--------------------------------------------------------------------------------

* Stream test output when returning output

Version 0.7.16
--------------------------------------------------------------------------------

* Return bumps made for bump()

Version 0.7.15
--------------------------------------------------------------------------------

* Update usage for commit
* Add --test-dependent option to run tests in dependent products
* Add option to return test output

Version 0.7.14
--------------------------------------------------------------------------------

* Ignore DRAFT: prefix when creating branch from commit msg

Version 0.7.13
--------------------------------------------------------------------------------

* Add links to bumper

Version 0.7.12
--------------------------------------------------------------------------------

* Change auto branch commit words to 2 and add more ignored words
* Change --discard to count to allow deleting of multiple commits
* Add skip auto branch option for commit
* Automatically create a branch from commit msg
* Redevelop if tox.ini has been modified
* Fix tests

Version 0.7.11
--------------------------------------------------------------------------------

* Better composed commit message / revert on failed commit

* Remove extra line between changes when generating changelog


Version 0.7.10
--------------------------------------------------------------------------------

* Ignore "Update changelog" commits when publishing
* Update setup.py template
* Add url and summary info

Version 0.7.1
--------------------------------------------------------------------------------

* Add -D alias for --discard in commit


Version 0.7.0
--------------------------------------------------------------------------------

* Refactor to use bumper-lib


Version 0.6.10
================================================================================

* Add re constant for user repo reference

Version 0.6.9
--------------------------------------------------------------------------------

* Make -1, -2, etc limit work for svn log
* Pass unknown args for log to underlying SCM / better args


Version 0.6.8
--------------------------------------------------------------------------------

* Allow arbitrary boolean optional args to be passed to py.test from test command

Version 0.6.7
--------------------------------------------------------------------------------

* Support which command in tv alias


Version 0.6.6
--------------------------------------------------------------------------------

* Add -n pass thru option for py.test

* Only install editable dependencies in [tox] envlist environments


Version 0.6.5
--------------------------------------------------------------------------------

* Support checking out from github using product name or user/name format


Version 0.6.4
--------------------------------------------------------------------------------

* Remove checking of setup.py for test as that is affected by version bumps.
  Add pinned.txt to be checked


Version 0.6.3
--------------------------------------------------------------------------------

* Faster clean for *.pyc files


Version 0.6.2
--------------------------------------------------------------------------------

* Only use first line when showing what changed for svn during bump


Version 0.6.1
--------------------------------------------------------------------------------

* Update checkout usage


Version 0.6.0
--------------------------------------------------------------------------------

* Commit multiple file bumps as a single commit and use --msg as the summary (prepended)
* Improved tv alias


Version 0.5.11
================================================================================

* Skip editable mode change if there are no dependencies


Version 0.5.10
--------------------------------------------------------------------------------

* Support silent run that outputs on error and use on test command


Version 0.5.9
--------------------------------------------------------------------------------

* Return commands ran per env for test command


Version 0.5.8
--------------------------------------------------------------------------------

* Add tv alias to open files from ag in vim.
  Add env auto complete for test command

* Add doc link to usage


Version 0.5.7
--------------------------------------------------------------------------------

* Add install_command with -U to ensure latest versions are installed and without {opts} to always install dependencies


Version 0.5.6
--------------------------------------------------------------------------------

* Better exception handling/output for test


Version 0.5.5
--------------------------------------------------------------------------------

* Better support for customizing test command


Version 0.5.4
--------------------------------------------------------------------------------

* Rename dependencies to show_dependencies for test arg and update test usage

* Add example to setup tox and run style/coverage


Version 0.5.3
--------------------------------------------------------------------------------

* Skip install dependencies in editable mode if already in editable mode
* Add test for status

* Add test.editable_product_dependencies option to auto install dependencies in editable mode

* Support multiple environments when showing product dependencies

* Refactor tox ini code into ToxIni class

* Auto-detect requirement files change to re-develop environment


Version 0.5.2
--------------------------------------------------------------------------------

* Activate environment before running py.test

* Use spaces instead of tabs in tox template


Version 0.5.1
--------------------------------------------------------------------------------

* Add tests and support -k / -s options from py.test in test command


Version 0.5.0
--------------------------------------------------------------------------------

* Support multiple test environments and use optimized test run

* Update tox template

* Skip creating requirements.txt if setup.py already exists

* Fix import issues with setup --product

* Deprecate/break develop into test and setup command

* Update usage in README

* Remove remote doc config as that was checked in accidentally


Version 0.4.11
================================================================================

* Skip bump branch check when doing dry run


Version 0.4.7
--------------------------------------------------------------------------------

* Fix bump doc

* Update doc

* Update doc


Version 0.4.6
--------------------------------------------------------------------------------

* Add doc for bump / start but not finish Command Reference

* Add tests for bump and remove use of memozie

* Remove ln whitelist from tox


Version 0.4.5
--------------------------------------------------------------------------------

* Strip version spec from entry scripts in dev env


Version 0.4.4
--------------------------------------------------------------------------------

* Allow downstream package to show its version with -v


Version 0.4.3
--------------------------------------------------------------------------------

* Support custom file processing for bump and do not use squash merge for push


Version 0.4.2
--------------------------------------------------------------------------------

* Add bump bash shortcut


Version 0.4.1
--------------------------------------------------------------------------------

* Fix product name computation for url ends with /trunk

* Update changelog


Version 0.4.0
--------------------------------------------------------------------------------

* Add example on setting up / using product group

* Add bump command to bump dependency versions


Version 0.3.1
================================================================================

* Skip checking for user config file existence as that is done in RemoteConfig now

* Add -U to pip install


Version 0.3.0
--------------------------------------------------------------------------------

* Refactor to use remoteconfig

* Remove activate soft linking in --init


Version 0.2.40
================================================================================

* Retain latest major/minor release title in changelog


Version 0.2.39
--------------------------------------------------------------------------------

* Use bullet list for changes in CHANGELOG


Version 0.2.38
--------------------------------------------------------------------------------

* Add changelog to index by listing the latest version only


Version 0.2.37
--------------------------------------------------------------------------------

* Exit early / without changing version when there are no changes when publishing.
  Better 'a' alias to avoid having to do symlink in tox.
