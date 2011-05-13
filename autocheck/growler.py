# -*- coding:utf-8 -*-
# Created by Hans-Thomas on 2011-05-13.
#=============================================================================
#   growler.py --- Growl notifier
#=============================================================================
from os.path import abspath, dirname, join, exists

from Growl import GrowlNotifier, GROWL_NOTIFICATIONS_DEFAULT


class Notifier(object):
    
    def __init__(self, app_name='autocheck'):
        self.growl = GrowlNotifier(
            applicationName = app_name,
            notifications = [GROWL_NOTIFICATIONS_DEFAULT],
        )
        self.growl.register()

    def notify(self, title, description, kind='pass', sticky=False):
        icon = open(abspath(join(dirname(__file__), 'images', kind + '.png'))).read()
        self.growl.notify(
            noteType = GROWL_NOTIFICATIONS_DEFAULT,
            title = title,
            description = description,
            icon = icon,
            sticky = sticky,
        )

#.............................................................................
#   growler.py

# Smilies by Jamie Hill:
# http://thelucid.com/2007/07/30/autotest-growl-fail-pass-smilies/
