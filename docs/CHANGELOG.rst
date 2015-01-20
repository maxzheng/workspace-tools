Version 0.5.7
================================================================================

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
