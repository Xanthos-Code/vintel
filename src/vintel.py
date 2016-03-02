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

import cStringIO
import sys
import os
import time
import traceback

from PyQt4 import QtGui
from vi import version
from vi.ui import viui, systemtray
from vi.cache import cache
from vi.resources import resourcePath

global gErrorFile
global gDebugging


def exceptHook(exceptionType, exceptionValue, tracebackObject):
    """ Global function to catch unhandled exceptions.
    """
    separator = '-' * 80
    notice = "An unhandled exception occurred, please report the problem using via email to <{0}>.\nA log has been written to \"{1}\".\n\nError information: \n".format(
        "xanthosx@gmail.com", gErrorFile)
    versionInfo = version.VERSION
    timeString = time.strftime("%Y-%m-%d, %H:%M:%S")
    tracebackInfoFile = cStringIO.StringIO()
    traceback.print_tb(tracebackObject, None, tracebackInfoFile)
    tracebackInfoFile.seek(0)
    tracebackInfo = tracebackInfoFile.read()
    errorMsg = '{0}: \n{1}'.format(str(exceptionType), str(exceptionValue))
    sections = [separator, timeString, separator, errorMsg, separator, tracebackInfo]
    msg = '\n'.join(sections)

    try:
        file = open(gErrorFile, "w")
        file.write(msg)
        file.write(versionInfo)
        file.close()
    except IOError:
        pass

    if not gDebugging:
        errorBox = QtGui.QMessageBox()
        errorBox.setText(str(notice) + str(msg) + str(versionInfo))
        errorBox.exec_()
    else:
        print "Unhandled error caught by exceptHook: " + str(msg)


sys.excepthook = exceptHook

if __name__ == "__main__":

    gErrorFile = None
    gDebugging = True

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
    gErrorFile = os.path.join(outputDir, "error.log")

    # print "Vintel expects to find logs at: ", pathToLogs
    # print "Vintel writes data to: ", outputDir

    trayIcon = systemtray.TrayIcon(app)
    trayIcon.setContextMenu(systemtray.TrayContextMenu(trayIcon))
    trayIcon.show()

    mw = viui.MainWindow(pathToLogs, trayIcon)
    mw.show()
    splash.finish(mw)

    sys.exit(app.exec_())
