Version 0.5.0
================================================================================

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
