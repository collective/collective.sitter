from Products.ZODBMountPoint.MountedObject import manage_addMounts
from plone import api
from Products.Transience.Transience import TransientObjectContainer
from Products.Sessions import install_session_data_manager

import logging


log = logging.getLogger(__name__)


def post_install(context=None):
    portal = api.portal.get()
    create_session_stuff(portal)


def create_session_stuff(portal):
    if api.env.test_mode():
        return
    app = portal.__parent__
    if "temp_folder" in app:
        return
    manage_addMounts(app, ["/temp_folder"])
    temp_folder = app.temp_folder
    default_sdc_settings = {
        "addNotification": "",
        "delNotification": "",
        "limit": 1000,
        "period_secs": 20,
        "timeout_mins": 20,
        "title": "Session Data Container",
    }
    sdc = TransientObjectContainer("session_data", **default_sdc_settings)
    temp_folder._setObject("session_data", sdc)
    install_session_data_manager(app)