workspace-tools
===============

Tools to simplify workspace / scm management when working with multiple repositories.

Feature Summary
===============

* One tool to seamlessly manage / integrate all workspace tools, from develop to publish.
* Trunk based development. One branch represents one change that is merged into master when pushed.
* SCM agnostic (for git/git-svn and svn (commit/push command support later)).
* Simplified command execution for common workflow
* Path aware context commands that runs command across all checkouts
* Extensible by adding your own custom commands or modify existing by wrapping them.
* Cool and sensible shortcut aliases to help you do more by typing less

Quick Start Tutorial
====================

First, install it with::

    pip install workspace-tools

Second, setup environment with all bash functions/aliases (the remaining tutorial assumes this is run)::

    cd ~/workspace

    wst setup -a  # This creates a "ws" bash function that goes to the workspace
                  # directory and act as an alias for wst
    source ~/.wstrc

To go to your workspace directory, run::

    ws

To checkout a repo::

    co https://github.com/maxzheng/workspace-tools.git

    # This would be stuck forever if there is an input prompt as output is hidden.
    # It will be fixed once I figure out how to stream output from subprocess call.
    # For now, ensure that you are able to checkout repos using 'git clone' without prompt.

To update all repos in your workspace::

    up

Make a commit and create a new branch for it::

    cd workspace-tools
    # vi README.rst and make some changes

    ci -b test "Updated README.rst"

See status/diff for all of your repos::

    ws
    st
    di
    # More interesting if you do have changes in your other repos

And finally amend the change and push::

    cd workspace-tools
    # vi README.rst and make more changes

    ci -a -p
    # It will fail at push as you are not a committer, but the change was committed to branch, and then merged into master.

Or simply push the change in your current branch::

    push
    # Again, it will fail at push as you are not a committer, but the change was merged into master.

Now you are ready to try out the other commands yourself::

    usage: wst [-h] [-v] [--debug] <sub-command> ...

    optional arguments:

      -h, --help            show this help message and exit
      -v, --version         show program's version number and exit
      --debug               Turn on debug mode

    sub-commands:
      {checkout,co,clean,commit,ci,develop,de,diff,di,log,publish,push,setup,status,st,update,up}
                            List of sub-commands
        checkout (co)       Checkout products
        clean               Clean workspace by removing build, dist, and .pyc
                            files
        commit (ci)         Commit all changes locally, including new files.
        develop (de)        Manages development environments for product.
        diff (di)           Show diff on current product or all products in
                            workspace
        log                 Show commit logs
        publish             Bumps version in setup.py (defaults to patch), commits
                            all changes, builds a source distribution, and uploads
                            with twine.
        push                Push changes for branch
        setup               Optional (refer to setup --help). Setup workspace
                            environment. Run from primary workspace directory.
        status (st)         Show status on current product or all products in
                            workspace
        update (up)         Update current product or all products in workspace


Customize Commands
==================

As simple as two steps:

1. Create your own controller by copying workspace/controller.py:main and add entrypoint to setup.py
2. Add your own commands or change existing in controller. See `workspace.commands` package for examples.

TBD for better docs here.

More
====

| Documentation: http://workspace-tools.readthedocs.org
|
| PyPI Package: https://pypi.python.org/pypi/workspace-tools
| GitHub Source: https://github.com/maxzheng/workspace-tools
| Report Issues/Bugs: https://github.com/maxzheng/workspace-tools/issues
|
| Connect: https://www.linkedin.com/in/maxzheng
| Contact: maxzheng.os @t gmail.com
