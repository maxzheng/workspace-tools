"""
#######################################################################################
# Define product groups to take action upon (such as ws develop)
#######################################################################################
[product_groups]
#group_name = product_checkout1 lib_checkout2


#######################################################################################
# Setting for checkout command
#######################################################################################
[checkout]

# Check out SVN repo using git-svn and clone the specified # of commits. Set to 0 to disable git-svn clone.
# Higher the number, the longer it takes to clone.
use_gitsvn_to_clone_svn_commits = 10

#######################################################################################
# Setting for bump command
#######################################################################################
[bump]

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
config.read(__doc__)


def product_groups():
  """ Returns a dict with product group name mapped to products """
  return dict((group, names.split()) for group, names in config.product_groups)
