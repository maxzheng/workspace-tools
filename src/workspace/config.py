"""
# Default config. Change these in your personal ~/.config/workspace.cfg ::

  ###########################################################################################################
  # Define product groups to take action upon (such as wst checkout, develop, or bump)
  ###########################################################################################################
  [product_groups]
  mzheng-repos =
    git@github.com:maxzheng/workspace-tools.git
    git@github.com:maxzheng/clicast.git
    git@github.com:maxzheng/localconfig.git
    git@github.com:maxzheng/remoteconfig.git
  mzheng = workspace-tools clicast localconfig remoteconfig


  ###########################################################################################################
  # Settings for bump command
  ###########################################################################################################
  [bump]

  # List of requirement files to check / bump dependencies in
  requirement_files = requirements.txt pinned.txt


  ###########################################################################################################
  # Settings for checkout command
  ###########################################################################################################
  [checkout]

  # Check out SVN repo using git-svn and clone the specified # of commits. Set to 0 to disable git-svn clone.
  # Higher the number, the longer it takes to clone.
  use_gitsvn_to_clone_svn_commits = 10

  # API used to find git repo for single word checkout (i.e. wst checkout workspace-tools)
  # It should accept a ?q=singleWord param
  search_api_url = https://api.github.com/search/repositories

  # URL to use when checking out a user repo reference (i.e. wst checkout maxzheng/workspace-tools)
  user_repo_url = git@github.com:%s.git


  ###########################################################################################################
  # Settings for clean command
  ###########################################################################################################
  [clean]

  # Remove products that have not been modified since given days ago
  remove_products_older_than_days =

  # Remove all products except for these ones (product or group)
  remove_all_products_except =

  ###########################################################################################################
  # Settings for commit command
  ###########################################################################################################
  [commit]

  # Automatically create branch based on the first number of commit words. Set to 0 to turn off.
  auto_branch_from_commit_words = 2
"""

import logging
import os

from remoteconfig import RemoteConfig


CONFIG_FILE = 'workspace.cfg'
USER_CONFIG_FILE = os.path.join('~', '.config', CONFIG_FILE)

log = logging.getLogger()
config = RemoteConfig(USER_CONFIG_FILE, cache_duration=60)
config.read(__doc__.replace('\n  ', '\n'))


def product_groups():
  """ Returns a dict with product group name mapped to products """
  return dict((group, names.split()) for group, names in config.product_groups)
