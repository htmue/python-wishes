# -*- coding:utf-8 -*-
# Created by Hans-Thomas on 2011-12-11.
#=============================================================================
#   setup.py --- Install script
#=============================================================================
import setuptools
from distutils.core import setup


setup(
    name='wishes',
    version='0.1.0',
    description='Run Cucumber-style features as standard unittests',
    author='Hans-Thomas Mueller',
    author_email='htmue@mac.com',
    url='https://github.com/htmue/python-wishes',
    packages=['wishes'],
    package_data=dict(wishes=['*.yaml']),
    install_requires=['PyYAML', 'six'],
)

#.............................................................................
#   setup.py
