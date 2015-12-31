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
import subprocess
import sys

from PyQt4.QtCore import QThread
from vi.resources import resourcePath
from Queue import Queue

global gPygletAvailable

try:
	import pyglet
	from pyglet import media

	gPygletAvailable = True
except ImportError:
	gPygletAvailable = False


class SoundThread(QThread):
	SOUNDS = {"alarm": "178032__zimbot__redalert-klaxon-sttos-recreated.wav",
			  "kos": "178031__zimbot__transporterstartbeep0-sttos-recreated.wav",
			  "request": "178028__zimbot__bosun-whistle-sttos-recreated.wav"}

	soundVolume = 25  # Must be an integer beween 0 and 100
	soundActive = False
	soundAvailable = False
	useDarwinSound = False
	useSpokenNotifications = True
	sharedInstance = None

	def __init__(self):
		QThread.__init__(self)
		self.q = Queue()
		self.sharedInstance = self
		self.isDarwin = sys.platform.startswith("darwin")
		self.soundAvailable = True


	def platformSupportsSpeech(self):
		if sys.platform.startswith("darwin"):
			return True
		return False

	def setUseSpokenNotifications(self, newValue):
		if newValue is not None:
			self.useSpokenNotifications = newValue

	def setSoundVolume(self, newValue):
		""" Accepts and stores a number between 0 and 100.
		"""
		self.soundVolume = max(0, min(100, newValue))

	def playSound(self, name="alarm", message=""):
		if self.useSpokenNotifications:
			audioFile = None
		else:
			audioFile = resourcePath("vi/ui/res/{0}".format(self.SOUNDS[name]))
		self.q.put((audioFile, message))

	def run(self):
		while True:
			audioFile, message = self.q.get()
			volume = float(self.soundVolume) / 100.0

			if self.useSpokenNotifications and message != "":
				if self.isDarwin:
					os.system("say [[volm {0}]] {1}".format(volume, message))
				else:
					print "SoundThread: sorry, speech not yet implemented on this platform"
			elif audioFile is not None:
				if gPygletAvailable:
					src = media.load(audioFile, streaming=False)
					player = media.Player()
					player.queue(src)
					player.volume = volume
					player.play()
				elif self.isDarwin:
					subprocess.call(["afplay -v {0} {1}".format(volume, audioFile)], shell=True)
