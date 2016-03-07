#!/usr/bin/env python
###########################################################################
#  Vintel - Visual Intel Chat Analyzer									  #
#  Copyright (C) 2014-15 Sebastian Meyer (sparrow.242.de+eve@gmail.com )  #
#																		  #
#  This program is free software: you can redistribute it and/or modify	  #
#  it under the terms of the GNU General Public License as published by	  #
#  the Free Software Foundation, either version 3 of the License, or	  #
#  (at your option) any later version.									  #
#																		  #
#  This program is distributed in the hope that it will be useful,		  #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of		  #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	 See the		  #
#  GNU General Public License for more details.							  #
#																		  #
#																		  #
#  You should have received a copy of the GNU General Public License	  #
#  along with this program.	 If not, see <http://www.gnu.org/licenses/>.  #
###########################################################################

import sys
import os

from PyQt4 import QtGui
from vi import version
from vi.ui import viui, systemtray
from vi.cache import cache
from vi.resources import resourcePath
from vi.logger import Logger


def exceptHook(exceptionType, exceptionValue, tracebackObject):
    """
        Global function to catch unhandled exceptions.
    """
    try:
        errorMsg = '{0}: \n{1}'.format(str(exceptionType), str(exceptionValue))
        msg = '\n'.join(errorMsg)
        logger.exception(msg)
    except Exception:
        pass


sys.excepthook = exceptHook

if __name__ == "__main__":

    app = QtGui.QApplication(sys.argv)
    splash = QtGui.QSplashScreen(QtGui.QPixmap(resourcePath("vi/ui/res/logo.png")))

    splash.show()
    app.processEvents()

    pathToLogs = ""
    if len(sys.argv) > 1:
        pathToLogs = sys.argv[1]

    if not os.path.exists(pathToLogs):
        if sys.platform.startswith("darwin"):
            pathToLogs = os.path.join(os.path.expanduser("~"), "Library", "Application Support", "Eve Online",
                                      "p_drive", "User", "My Documents", "EVE", "logs", "Chatlogs")
        elif sys.platform.startswith("linux"):
            pathToLogs = os.path.join(os.path.expanduser("~"), "EVE", "logs", "Chatlogs")
        elif sys.platform.startswith("win32") or sys.platform.startswith("cygwin"):
            import ctypes.wintypes

            buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
            ctypes.windll.shell32.SHGetFolderPathW(0, 5, 0, 0, buf)
            documentsPath = buf.value
            pathToLogs = os.path.join(documentsPath, "EVE", "logs", "Chatlogs")
    if not os.path.exists(pathToLogs):
        # None of the paths for logs exist, bailing out
        QtGui.QMessageBox.critical(None, "No path to Logs", "No logs found at: " + pathToLogs, "Quit")
        sys.exit(1)

    # Setting local working directory for cache, etc.
    outputDir = os.path.join(os.path.dirname(os.path.dirname(pathToLogs)), "vintel")

    if not os.path.exists(outputDir):
        os.mkdir(outputDir)

    cache.Cache.PATH_TO_CACHE = os.path.join(outputDir, "cache-2.sqlite3")

    logger = Logger(outputDir)
    logger.critical("Vintel %s starting up." % version.VERSION)
    logger.critical("Looking for chat logs at: %s" % pathToLogs)
    logger.critical("Writing logs to: %s" % outputDir)

    trayIcon = systemtray.TrayIcon(app)
    trayIcon.setContextMenu(systemtray.TrayContextMenu(trayIcon))
    trayIcon.show()

    mainWindow = viui.MainWindow(pathToLogs, trayIcon)
    mainWindow.show()
    splash.finish(mainWindow)

    sys.exit(app.exec_())
