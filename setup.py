#!/usr/bin/env python2.6

import os
import setuptools


def find_files(path):
    return [os.path.join(path, f) for f in os.listdir(path)]


setuptools.setup(
  name='workspace-tools',
  version='3.0.3',

  author='Max Zheng',
  author_email='maxzheng.os @t gmail.com',

  description='Convenience wrapper for git/tox to simplify local development',
  long_description=open('README.rst').read(),

  changelog_url='https://raw.githubusercontent.com/maxzheng/workspace-tools/master/docs/CHANGELOG.rst',
  url='https://github.com/maxzheng/workspace-tools',

  entry_points={
    'console_scripts': [
      'wst = workspace.controller:Commander.main',
    ],
  },

  install_requires=open('requirements.txt').read(),

  license='MIT',

  packages=setuptools.find_packages(),
  include_package_data=True,

  setup_requires=['setuptools-git'],

  classifiers=[
    'Development Status :: 5 - Production/Stable',

    'Intended Audience :: Developers',
    'Topic :: Software Development',

    'License :: OSI Approved :: MIT License',

    'Programming Language :: Python :: 2',
    'Programming Language :: Python :: 2.6',
    'Programming Language :: Python :: 2.7',
  ],

  keywords='workspace multiple repositories git scm abstraction development tools',
)
