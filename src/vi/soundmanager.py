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
import sys
import six
import logging

from PyQt5.QtCore import QThread, QUrl
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from six.moves.queue import Queue
from vi.resources import resourcePath
from vi.singleton import Singleton

global festivalAvailable

try:
    import festival
    festivalAvailable = True
except:
    festivalAvailable = False

class SoundManager(six.with_metaclass(Singleton)):
    SOUNDS = {"alarm": "178032__zimbot__redalert-klaxon-sttos-recreated.wav",
              "kos": "178031__zimbot__transporterstartbeep0-sttos-recreated.wav",
              "request": "178028__zimbot__bosun-whistle-sttos-recreated.wav"}

    soundVolume = 25  # Must be an integer between 0 and 100
    soundActive = False
    soundAvailable = False
    useDarwinSound = False
    useSpokenNotifications = True
    _soundThread = None

    def __init__(self):
        self._soundThread = self.SoundThread()
        self.soundAvailable = self.platformSupportsAudio()
        if not self.platformSupportsSpeech():
            self.useSpokenNotifications = False
        if self.soundAvailable:
            self._soundThread.start()

    def platformSupportsAudio(self):
        return True

    def platformSupportsSpeech(self):
        if self._soundThread.isDarwin or festivalAvailable:
            return True
        return False

    def setUseSpokenNotifications(self, newValue):
        if newValue is not None:
            self.useSpokenNotifications = newValue

    def setSoundVolume(self, newValue):
        """ Accepts and stores a number between 0 and 100.
        """
        self.soundVolume = max(0, min(100, newValue))
        self._soundThread.setVolume(self.soundVolume)

    def playSound(self, name="alarm", message="", abbreviatedMessage=""):
        """ Schedules the work, which is picked up by SoundThread.run()
        """
        if self.soundAvailable and self.soundActive:
            if self.useSpokenNotifications:
                audioFile = None
            else:
                audioFile = resourcePath("vi/ui/res/{0}".format(self.SOUNDS[name]))
            self._soundThread.queue.put((audioFile, message, abbreviatedMessage))

    def say(self,  message='This is a test!'):
        self._soundThread.speak(message)

    def quit(self):
        if self.soundAvailable:
            self._soundThread.quit()

    #
    #  Inner class handle audio playback without blocking the UI
    #

    class SoundThread(QThread):
        queue = None
        isDarwin = sys.platform.startswith("darwin")
        volume = 25


        def __init__(self):
            QThread.__init__(self)
            self.queue = Queue()
            self.player = QMediaPlayer()
            self.active = True


        def setVolume(self, volume):
            self.volume = volume


        def run(self):
            while True:
                audioFile, message, abbreviatedMessage = self.queue.get()
                if not self.active:
                    return
                if SoundManager().useSpokenNotifications and (message != "" or abbreviatedMessage != ""):
                    if abbreviatedMessage != "":
                        message = abbreviatedMessage
                    if not self.speak(message):
                        if audioFile:
                            self.playAudioFile(audioFile, False)
                        logging.error("SoundThread: sorry, speech not yet implemented on this platform")
                elif audioFile is not None:
                    self.playAudioFile(audioFile, False)

        def quit(self):
            self.active = False
            self.queue.put((None, None, None))
            if self.player:
                self.player.pause()
                self.player.delete()
            QThread.quit(self)


        def speak(self, message):
            if self.isDarwin:
                self.darwinSpeak(message)
            elif festivalAvailable:
                festival.sayText(message)
            else:
                return False
            return True


        #
        #  Audio subsytem access
        #

        def playAudioFile(self, filename, stream=False):
            try:
                content = QMediaContent(QUrl.fromLocalFile(filename))
                self.player.setMedia(content)
                self.player.setVolume(float(self.volume))
                self.player.play()
            except Exception as e:
                logging.error("SoundThread.playAudioFile exception: %s", e)


        def darwinSpeak(self, message):
            try:
                os.system("say [[volm {0}]] '{1}'".format(float(self.volume) / 100.0, message))
            except Exception as e:
                logging.error("SoundThread.darwinSpeak exception: %s", e)
