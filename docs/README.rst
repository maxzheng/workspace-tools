workspace-tools
===============

Tools to simplify workspace / scm management when working with multiple repositories.

It is mostly a wrapper on top of existing tools with the end goal of providing a simple, seamless, and
less repetive experience when working with one or more repositories. Feature support is mostly limited
to what the author uses as, currently, it is foremost a personal tool to enhance the author's own productivity,
but sharing it as others might find it useful.

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
    # So, ensure that you are able to checkout repos using 'git clone' without prompt.

    # Or checkout a group of repos as defined in workspace.cfg
    # co mzheng-repos

For more info about workspace.cfg, refer to Configuration_ doc.

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

If you have pinned your dependency requirements and want to update to latest version::

    bump

    # Or bump a defined group of products as defined in workspace.cfg
    # bump mzheng
    #
    # Or to a specific version (why not just vi? This validates the version for you)
    # bump requests==2.5.1

Now you are ready to try out the other commands yourself::

    usage: wst [-h] [-v] [--debug] <sub-command> ...

    optional arguments:

      -h, --help            show this help message and exit
      -v, --version         show program's version number and exit
      --debug               Turn on debug mode

    sub-commands:
      {bump,checkout,co,clean,commit,ci,diff,di,log,publish,push,setup,status,st,test,update,up}
                            List of sub-commands
        bump                Bump dependency versions in requirements.txt,
                            pinned.txt, or any specified file.
        checkout (co)       Checkout products (repo urls) or revert files.
        clean               Clean workspace by removing build, dist, and .pyc
                            files
        commit (ci)         Commit all changes locally, including new files.
        diff (di)           Show diff on current product or all products in
                            workspace
        log                 Show commit logs
        publish             Bumps version in setup.py (defaults to patch), writes
                            out changelog, builds a source distribution, and
                            uploads with twine.
        push                Push changes for branch
        setup               Optional (refer to setup --help). Setup workspace
                            environment. Run from primary workspace directory.
        test                Runs tests and manages test environments for product.
        status (st)         Show status on current product or all products in
                            workspace
        update (up)         Update current product or all products in workspace

Links & Contact Info
====================

| Documentation: http://workspace-tools.readthedocs.org
|
| PyPI Package: https://pypi.python.org/pypi/workspace-tools
| GitHub Source: https://github.com/maxzheng/workspace-tools
| Report Issues/Bugs: https://github.com/maxzheng/workspace-tools/issues
|
| Connect: https://www.linkedin.com/in/maxzheng
| Contact: maxzheng.os @t gmail.com

.. _Configuration: http://workspace-tools.readthedocs.org/en/latest/api/config.html
