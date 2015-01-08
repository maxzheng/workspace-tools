"""
# Default config. Change these in your personal ~/.config/workspace.cfg ::

  ###########################################################################################################
  # Define product groups to take action upon (such as ws develop or bump)
  ###########################################################################################################
  [product_groups]
  mzheng-repos =
    git@github.com:maxzheng/workspace-tools.git
    git@github.com:maxzheng/clicast.git
    git@github.com:maxzheng/localconfig.git
    git@github.com:maxzheng/remoteconfig.git
  mzheng = workspace-tools clicast localconfig remoteconfig


  ###########################################################################################################
  # Settings for checkout command
  ###########################################################################################################
  [checkout]

  # Check out SVN repo using git-svn and clone the specified # of commits. Set to 0 to disable git-svn clone.
  # Higher the number, the longer it takes to clone.
  use_gitsvn_to_clone_svn_commits = 10


  ###########################################################################################################
  # Settings for bump command
  ###########################################################################################################
  [bump]

  # List of requirement files to check / bump dependencies in
  requirement_files = requirements.txt pinned.txt
"""

import logging
import os
from StringIO import StringIO
import sys

from remoteconfig import RemoteConfig


CONFIG_FILE = 'workspace.cfg'
USER_CONFIG_FILE = os.path.join('~', '.config', CONFIG_FILE)

log = logging.getLogger()
config = RemoteConfig(USER_CONFIG_FILE)
config.read(__doc__.replace('\n  ', '\n'))


def product_groups():
  """ Returns a dict with product group name mapped to products """
  return dict((group, names.split()) for group, names in config.product_groups)
