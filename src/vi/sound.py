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

import subprocess, sys, os, singleton

from vi.resources import resourcePath
from vi.singleton import Singleton

global gPygameAvailable

try:
	import pygame
	gPygameAvailable = True
except ImportError:
	gPygameAvailable = False


class Sound(Singleton):

	SOUNDS = {"alarm": "178032__zimbot__redalert-klaxon-sttos-recreated.wav",
			  "kos": "178031__zimbot__transporterstartbeep0-sttos-recreated.wav",
			  "request": "178028__zimbot__bosun-whistle-sttos-recreated.wav"}

	soundCache = {}
	soundVolume = 25   # Must be an integer beween 0 and 100
	soundActive = False
	soundAvailable = False
	useDarwinSound = False
	useSpokenNotifications = False
	
	def __init__(self):
		Singleton.__init__(self)
		
		if gPygameAvailable:
			pygame.mixer.init()
			self.soundAvailable = True
		elif sys.platform.startswith("darwin"):
			self.useDarwinSound = True;
			self.soundAvailable = True


	def setUseSpokenNotifications(self, newValue=None):
		if newValue is not None:
			self.useSpokenNotifications = newValue
		print newValue


	def setSoundVolume(self, newValue):
		""" Accepts and stores a number between 0 and 100.
		"""
		self.soundVolume = max(0, min(100, newValue))
		for sound in self.soundCache.values():
			# Convert to a value between 0 and 1 when passing to the underlying subsystem
			sound.setVolume(float(self.soundVolume)	 / 100.0)
	

	def playSound(self, name="alarm", message=None):
		if self.soundAvailable and self.soundActive:
			if name not in self.SOUNDS:
				raise ValueError("Sound '{0}' is not available".format(name))
		else:
			return

		path = resourcePath("vi/ui/res/{0}".format(self.SOUNDS[name]))
	
		if self.useDarwinSound:
			if self.useSpokenNotifications and message:
				os.system("say [[volm {0}]] {1}".format(float(self.soundVolume) / 100.0, message))
			else:
				subprocess.call(["afplay -v {0} {1}".format(float(self.soundVolume) / 100.0, path)], shell=True)
		else:
			if name not in self.soundCache:
				self.soundCache[name] = pygame.mixer.Sound(path)
			self.soundCache[name].play()
