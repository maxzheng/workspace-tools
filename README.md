workspace-tools
===============

Tools to simplify workspace / scm management when working with multiple repositories.

Why use workspace-tools
-----------------------
* It is SCM agnostic (for git/git-svn and svn (commit/push command support later)). No need to remember different commands to run.
* Seamless integration of full workspace tooling, from commit to publish.
* Simplified command execution for common workflow (instead of several commands to push, just run 'push' command)
* Path aware context commands that runs command across all products (try diff in workspace directory to see diffs for all products!)
* Extensible by adding your own custom commands or modify existing by wrapping them.
* Checks out svn using git-svn by default (configurable)
* Lastly, it has tons of cool short-cut aliases (see setup command)!!

To get started
---------------
* Optionally setup workspace environment, run "ws setup -h" for options.
    - "ws setup -a" is recommended. :)
* To checkout a product, run: ws checkout <git or svn repository url> [<url2> ...]
    - Product that use svn is checked out with git-svn
* All commands are named appropriately for what they do, but see its --help for additional info.

All of its commands will act differently based on if it is run from a repository (MP) or the workspace that contains repositories.
* When run from a repository, the command applies to that repository only.
* When run from a workspace that contains many repository, the command will recursively run against each repository.
  Some commands won't run in this mode, such as commit or push (but may in the future).
