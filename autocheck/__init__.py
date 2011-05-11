# -*- coding:utf-8 -*-
# Created by Hans-Thomas on 2011-05-11.
#=============================================================================
#   __init__.py --- 
#=============================================================================
import logging.config
import os.path

import yaml


logging_yaml = os.path.join(os.path.dirname(__file__), 'logging.yaml')
logging.config.dictConfig(yaml.load(open(logging_yaml)))

#.............................................................................
#   __init__.py
