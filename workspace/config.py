"""
# Default config. Change these in your personal ~/.config/workspace.cfg ::

  ###########################################################################################################
  # Define product groups to take action upon (such as wst checkout, develop, or bump)
  ###########################################################################################################
  [product_groups]
  mzheng-repos =
    https://github.com/maxzheng/workspace-tools.git
    https://github.com/maxzheng/clicast.git
    https://github.com/maxzheng/localconfig.git
    https://github.com/maxzheng/remoteconfig.git
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

  # API used to find git repo for single word checkout (e.g. wst checkout workspace-tools)
  # It should accept a ?q=singleWord param
  search_api_url = https://api.github.com/search/repositories

  # URL to use when checking out a user repo reference (e.g. wst checkout maxzheng/workspace-tools)
  user_repo_url = git@github.com:%s.git

  # User mapped to the origin remote. When set, checking out a repo that does not belong to the user
  # will use upstream remote. e.g. maxzheng
  origin_user =

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

  # When auto branching from commit words, this is the indicator that will be used to
  # separate the commit branch from the parent branch, like commit_branch@parent_branch.
  commit_branch_indicator = @


  ###########################################################################################################
  # Settings for merge command
  ###########################################################################################################
  [merge]

  # Branches to merge separated by space (e.g. 3.2.x 3.3.x master)
  branches =
"""
from __future__ import absolute_import

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
