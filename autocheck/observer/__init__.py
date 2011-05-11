# -*- coding:utf-8 -*-
# Copyright 2010 Hans-Thomas Mueller
# Distributed under the terms of the GNU General Public License v2
#=============================================================================
#   __init__.py --- Observe creation of directories and files
#=============================================================================

try:
    from observer_linux import Observer
except ImportError:
    try:
        from observer_macosx import Observer
    except ImportError:
        from observer import Observer

#.............................................................................
#   __init__.py
