Version 3.3.11
================================================================================

* Ignore W503

Version 3.3.10
--------------------------------------------------------------------------------

* Remove white space
* Merge pull request #2 from vvcephei/patch-1
  
  Ability to run a validation before pushing merge
* Ability to run a validation before pushing merge
  
  Adds a optional command for Merge to execute before pushing the merge result.
  
  For example, `--validation 'mvn clean test-compile'`, or even more safely `--validation 'mvn clean verify'`
  will make sure that the project still builds (or the tests still pass) after performing the merge and before
  pushing potentially broken code to the remote.

Version 3.3.9
--------------------------------------------------------------------------------

* Strip out tox prefix when doing expand vars
* Merge pull request #1 from dnozay/pr-envdir
  
  fix envdir to substitute {homedir}, {toxworkdir} properly.
* more fixes
* fix envdir to substitute {homedir}, {toxworkdir} properly.
  
  e.g.
  
  ```
  [tox]
  envlist = py27,py3
  toxworkdir = {homedir}/.virtualenvs/my-app
  
  [testenv:py27]
  basepython = python2.7
  
  [testenv:py3]
  basepython = python3
  ```

Version 3.3.8
--------------------------------------------------------------------------------

* Add --merge-branches option to merge command to allow config.merge.branches to be overriden

Version 3.3.7
--------------------------------------------------------------------------------

* Print help when no command is provided

Version 3.3.6
--------------------------------------------------------------------------------

* Support different version of Python as the default

Version 3.3.5
--------------------------------------------------------------------------------

* Pass ssh auth to tox
* Update tox.ini to support multiple Python version
* Support multiple Python in tox template

Version 3.3.4
--------------------------------------------------------------------------------

* Remove unused dependencies

Version 3.3.3
--------------------------------------------------------------------------------

* Reverse order of ff vs tags arg as older git version has a bug

Version 3.3.2
--------------------------------------------------------------------------------

* Use abspath instead of realpath so symlinks are not resolved
* Show where tox.ini is from

Version 3.3.1
--------------------------------------------------------------------------------

* Use autopip and update setup
* Update setup.py to add wheel
* Update gitignore file
* Add publish example

Version 3.3.0
--------------------------------------------------------------------------------

* Fix string concat
* Build and publish wheel
* Skip parallel for targeted test run / works better with pdb

Version 3.2.4
================================================================================

* Push version bump commit and skip style check

Version 3.2.3
--------------------------------------------------------------------------------

* Always generate text cover report and remove --text option
* Use better example for checkout
* Add create or update function for setup

Version 3.2.2
--------------------------------------------------------------------------------

* Display local branch instead of remote branch in status
* Add commit for major/minor version bump

Version 3.2.1
--------------------------------------------------------------------------------

* Exit with code 1 when failed to upload
* Comment out concurrency in pytest as it generally causes more problems than it solves.
  
  It is something that only large projects need, so it should be something added later
* Update README with better examples using new features

Version 3.2.0
--------------------------------------------------------------------------------

* Publish current version and then bump the version instead of the other way around
* Add actual tests for clean
* Remove unused repo_url function
* Remove run_in_bg as it is not used
* Remove unused product group setup and add tests for setup
* Fix test --show-dependencies to work in pip 10
* Default style to cover,test and use test env when pytest args are provided
* Show tox result and prefer test over cover when pytest args are provided

Version 3.1.3
================================================================================

* Switch to use pytest-fixtures
* Add link to standard classifiers
* Remove ansible-hosts as it has been moved to its own repo
* Ignore errors from ssh
* Add --text option for test coverage
* Switch to use utils-core
* Add ah / ansible hostmanager script
* Fix status for rebase conflict and add color
* Switch to pytest
* git clean also removes ignored files

Version 3.1.2
--------------------------------------------------------------------------------

* Support color in diff pager
* Add test for merge
* Add test for publish
* Support detached head in status
* Add -f/--force option to clean to remove untracked files

Version 3.1.1
--------------------------------------------------------------------------------

* Remove pip.req as it is not used
* Fix regex for matching tracking branch name
* Set default max-line-length to 120
* Set min version to Python 3.6
* Set Python version to 3 for readthedocs
* Add readthedocs config
* Update readme

Version 3.1.0
--------------------------------------------------------------------------------

* Use regex to better match update error
* Checkout using upstream remote and add origin remote for user when checkout.origin_user is set
* Indicate tracking remote for branch status
* Always track upstream branch and pull from all remotes
* Better support to checkout remote/branch combo
* Use tox.envdir instead of tox.workdir to check if a product is in editable mode or not
* Remove test venv foo

Version 3.0.28
================================================================================

* Fix envvar expansion
* Use ~/.virtualenvs as the envdir for tox
* Support venv name for activate

Version 3.0.27
--------------------------------------------------------------------------------

* Support activate for ~/.virtualenvs

Version 3.0.26
--------------------------------------------------------------------------------

* Set min code coverage to 80
* Bump min Python to 3.6

Version 3.0.25
--------------------------------------------------------------------------------

* Ignore .eggs in flake8

Version 3.0.24
--------------------------------------------------------------------------------

* Remove commit checking as we only merge when there are stuff to be merged

Version 3.0.23
--------------------------------------------------------------------------------

* Skip style check when pushing a merge

Version 3.0.22
--------------------------------------------------------------------------------

* Add quiet option to merge
* Update source branch before merging

Version 3.0.21
--------------------------------------------------------------------------------

* Add --allow-commits option for merge

Version 3.0.20
--------------------------------------------------------------------------------

* Add strategy option to merge

Version 3.0.19
--------------------------------------------------------------------------------

* Show commits that will be merged
* Include ls for tv
* Show error when updating without remote checking and do --ff-only for update

Version 3.0.18
--------------------------------------------------------------------------------

* Set tracking to upstream remote
* Require origin/upstream remotes when there are more than 1 remote
* Show remotes in status
* Show only child branches at summary view
* Show when there is just 1 child branch
* No need to echo deleted branch as git already does that
* Fix bug to display all branches when there is only 1 repo
* Show status for child branches only when listing all repos

Version 3.0.17
--------------------------------------------------------------------------------

* Add skip update flag for merge

Version 3.0.16
--------------------------------------------------------------------------------

* Add dry run option to merge
* Support checking out remote branches

Version 3.0.15
--------------------------------------------------------------------------------

* Skip style check during publish

Version 3.0.14
--------------------------------------------------------------------------------

* Limit publish to commit setup.py/changelog files only

Version 3.0.13
--------------------------------------------------------------------------------

* Fix repo title
* Support multiple repositories in publish
* Use multiple push flags to indicate pushing to all remotes during commit
* Use git checkout path for git.Repo so it works from child dirs
* Set default max-line-length to 140
* Update keywords

Version 3.0.12
--------------------------------------------------------------------------------

* Merge branch 'master' of github.com:maxzheng/workspace-tools
* Use proper email format for author

Version 3.0.11
--------------------------------------------------------------------------------

* Check code style before pushing
* Change setup.py template to require Python 3.5+
* Remove requirements.txt from tox.ini
* Create example test in "tests" folder
* Move tests to "tests" folder

Version 3.0.10
--------------------------------------------------------------------------------

* Skip printing about merging to downstream branches

Version 3.0.9
--------------------------------------------------------------------------------

* Show parent branch when merging during push
* Show rebase message only if verbose

Version 3.0.8
--------------------------------------------------------------------------------

* Show branch and remotes being pulled from

Version 3.0.7
--------------------------------------------------------------------------------

* Check for any merge changes before pushing

Version 3.0.6
--------------------------------------------------------------------------------

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
