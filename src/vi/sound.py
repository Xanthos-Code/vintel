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

import sys
import argparse
import re
import urllib, urllib2
import time
from collections import namedtuple

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
	useGoogleTTS = False
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

			if self.useSpokenNotifications and message != "":
				if self.useGoogleTTS:
					mp3Filename = self.audioExtractToMp3(inputText=message)
					self.playAudioFile(mp3Filename)
				elif self.isDarwin:
					volume = float(self.soundVolume) / 100.0
					os.system("say [[volm {0}]] {1}".format(volume, message))
				else:
					self.playAudioFile(audioFile)
					print "SoundThread: sorry, speech not yet implemented on this platform"
			elif audioFile is not None:
				self.playAudioFile(audioFile)


	def playAudioFile(self, filename):
		volume = float(self.soundVolume) / 100.0
		if gPygletAvailable:
			src = media.load(filename, streaming=False)
			player = media.Player()
			player.queue(src)
			player.volume = volume
			player.play()
		elif self.isDarwin:
			subprocess.call(["afplay -v {0} {1}".format(volume, filename)], shell=True)


	def audioExtractToMp3(self, inputText='', args=None):
		# This accepts :
		#   a dict,
		#   an audio_args named tuple
		#   or arg parse object
		audioArgs = namedtuple('audio_args', ['language', 'output'])
		if args is None:
			args = audioArgs(language='en', output=open('output.mp3', 'w'))
		if type(args) is dict:
			args = audioArgs(language=args.get('language', 'en'), output=open(args.get('output', 'output.mp3'), 'w'))
		# Process inputText into chunks
		# Google TTS only accepts up to (and including) 100 characters long texts.
		# Split the text in segments of maximum 100 characters long.
		combinedText = self.splitText(inputText)

		# Download chunks and write them to the output file
		for idx, val in enumerate(combinedText):
			mp3url = "http://translate.google.com/translate_tts?tl=%s&q=%s&total=%s&idx=%s&ie=UTF-8&client=t" % (args.language, urllib.quote(val), len(combinedText), idx)
			headers = {"Host": "translate.google.com", "Referer": "http://www.gstatic.com/translate/sound_player2.swf",
					   "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_1)"}
			req = urllib2.Request(mp3url, '', headers)
			sys.stdout.write('.')
			sys.stdout.flush()
			if len(val) > 0:
				try:
					response = urllib2.urlopen(req)
					args.output.write(response.read())
					time.sleep(.5)
				except urllib2.URLError as e:
					print ('audioExtract error: %s' % e)
		args.output.close()
		return args.output.name


	def splitText(self, inputText, maxLength=100):
		"""
		Try to split between sentences to avoid interruptions mid-sentence.
		Failing that, split between words.
		See splitText_rec
		"""

		def splitTextRecursive(inputText, regexps, maxLength=maxLength):
			"""
			Split a string into substrings which are at most maxLength.
			Tries to make each substring as big as possible without exceeding
			maxLength.
			Will use the first regexp in regexps to split the input into
			substrings.
			If it it impossible to make all the segments less or equal than
			maxLength with a regexp then the next regexp in regexps will be used
			to split those into subsegments.
			If there are still substrings who are too big after all regexps have
			been used then the substrings, those will be split at maxLength.

			Args:
				inputText: The text to split.
				regexps: A list of regexps.
					If you want the separator to be included in the substrings you
					can add parenthesis around the regular expression to create a
					group. Eg.: '[ab]' -> '([ab])'

			Returns:
				a list of strings of maximum maxLength length.
			"""
			if (len(inputText) <= maxLength):
				return [inputText]

			# Mistakenly passed a string instead of a list
			if isinstance(regexps, basestring):
				regexps = [regexps]
			regexp = regexps.pop(0) if regexps else '(.{%d})' % maxLength

			textList = re.split(regexp, inputText)
			combinedText = []
			# First segment could be >max_length
			combinedText.extend(splitTextRecursive(textList.pop(0), regexps, maxLength))
			for val in textList:
				current = combinedText.pop()
				concat = current + val
				if (len(concat) <= maxLength):
					combinedText.append(concat)
				else:
					combinedText.append(current)
					# val could be > maxLength
					combinedText.extend(splitTextRecursive(val, regexps, maxLength))
			return combinedText
		return splitTextRecursive(inputText.replace('\n', ''), ['([\,|\.|;]+)', '( )'])
