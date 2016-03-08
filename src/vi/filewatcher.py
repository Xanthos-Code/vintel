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

import os
import time
import logging

from PyQt4 import QtCore
from PyQt4.QtCore import SIGNAL

"""
There is a problem with the QFIleWatcher on Windows and the log
files from EVE.
The first implementation (now FileWatcher_orig) works fine on Linux, but
on Windows it seems ther is something buffered. Only a file-operation on
the watched directory another event there, which tirggers the OS to
reread the files informations, trigger the QFileWatcher.
So here is a workaround implementation.
We use here also a QFileWatcher, only to the directory. It will notify it
if a new file was created. We watch only the newest (last 24h), not all!
"""


class FileWatcher(QtCore.QThread):
    def __init__(self, path, maxAge):
        QtCore.QThread.__init__(self)
        self.path = path
        self.maxAge = maxAge
        self.files = {}
        self.qtfw = QtCore.QFileSystemWatcher()
        self.qtfw.directoryChanged.connect(self.directoryChanged)
        self.qtfw.addPath(path)
        self.updateWatchedFiles()
        self.paused = True

    def directoryChanged(self):
        self.updateWatchedFiles()

    def run(self):
        while True:
            if self.paused:
                continue
            for path, modified in self.files.items():
                newModified = 0
                try:
                    newModified = os.path.getsize(path)
                except Exception as e:
                    logging.error("filewatcher-thread error: %s | %s", path, str(e))
                if newModified > modified:
                    self.emit(SIGNAL("file_change"), path)
                    self.files[path] = newModified
            time.sleep(1)

    def updateWatchedFiles(self):
        # Reading all files from the directory
        fullPath = None
        now = time.time()
        path = self.path
        filesInDir = set()
        for f in os.listdir(path):
            if not os.path.isdir(f):
                try:
                    add = True
                    fullPath = os.path.join(path, f)
                    if (self.maxAge and now - os.path.getmtime(fullPath) > self.maxAge):
                        add = False
                    if add:
                        filesInDir.add(fullPath)
                except Exception as e:
                    logging.error("Add file to filewatcher failed: %s | %s", fullPath, str(e))

        # Are there old files that not longer exists?
        filesToRemove = set()
        for knownFile in self.files:
            if knownFile not in filesInDir:
                filesToRemove.add(knownFile)
        for fileToRemove in filesToRemove:
            del self.files[fileToRemove]

        # Are there new files we must watch now?
        for newFile in filesInDir:
            if newFile not in self.files:
                self.files[newFile] = os.path.getsize(newFile)
