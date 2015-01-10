Version 0.4.4
================================================================================

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
