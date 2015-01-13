Command Reference
=================

SCM Support
-----------

Git and git-svn are fully supported with limited support for svn.

When running a command, a message will be displayed when it is not supported.

The author recommends developers to should use git-svn for svn if possible.
You will thank me later. :)

Setting Up Your Workspace
-------------------------

It is optional to run 'wst setup', however it is recommended as you can type less to do what you want.

After running setup, bash functions and aliases are created for all wst commands. I.e. It creates "ci"
alias for "wst commit" if the -a option is used (--commands-with-aliases). And for some commands (such
as push), it also adds auto complete for branch name.

To setup, simply go to your workspace directory, and then run 'wst setup' with the apporpriate options
(-a is recommended).

For the sake of readability for the first time user, the remaining reference will use the full wst command
instead of aliases from setup. But reference to the short version may be provided as a comment.

::

    usage: wst setup [-h] [-c | -a | --uninstall]

      Sets up workspace environment.

      While "wst" will work for multiple workspaces, this should only be run in your primary workspace directory.

      It sets up a "ws" bash function that goes to your workspace directory when no argument is passed in, otherwise
      runs wst command. And also additional functions / aliases for some commands if --commands/--commands-with-aliases
      is passed in. --commands-with-aliases (-a) is recommended. :)

      This can be re-run multiple times to change setup.

    optional arguments:
      -h, --help            show this help message and exit
      -c, --commands        Add convenience bash function for certain commands,
                            such as checkout to run "workspace checkout"
      -a, --commands-with-aliases
                            Same as --commands plus add shortcut aliases, like
                            "co" for checkout. This is for those developers that
                            want to get as much done with the least key strokes -
                            true efficienist! ;)
      --uninstall           Uninstall all functions/aliases


Checkout a Repository
---------------------

The type of repository is detected based on the repository URL provided when checking out.
If it ends with .git, then it is a git, otherwise it is svn. SVN repository is checked out
using git-svn by default - see `Configuration`_ to change this.

For svn, the checkout folder will be the basename of the URL after stripping out _trunk or /trunk.
Otherwise branch suffix isn't supported and will probably be used as the checkout folder.

To checkout a product, there are two ways:

1. Use an URL::

    wst checkout https://github.com/maxzheng/workspace-tools.git

    # Or after "wst setup -a": co https://github.com/maxzheng/workspace-tools.git

2. Use a product group (see `Configuration`_ for more info)::

    wst checkout mzheng-repos

Customize Commands
------------------

As simple as two steps:

1. Create your own controller by copying workspace/controller.py:main and add entrypoint to setup.py
2. Add your own commands or change existing in controller. See `workspace.commands` package for examples.

TBD for better docs.

Want More Docs?
---------------

Most commands have help info, so run the command with '-h'.

TBD for more docs as I am not sure if anyone actually read this since there probably
aren't that many users of workspace-tools. So If you would like to read the rest of the docs,
let me know (maxzheng.os @t gmail.com), and I will take the time to finish this.

.. _Configuration: http://workspace-tools.readthedocs.org/en/latest/api/config.html