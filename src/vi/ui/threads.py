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

import itertools
import time
from Queue import Queue

from PyQt4.QtCore import QThread
from PyQt4.QtCore import SIGNAL
from vi import evegate
from vi import koschecker
from vi.cache.cache import Cache
from vi.resources import resourcePath


class AvatarFindThread(QThread):
	def __init__(self):
		QThread.__init__(self)
		self.queue = Queue()

	def addChatEntry(self, chatEntry, clearCache=False):
		try:
			if clearCache:
				cache = Cache()
				cache.removeAvatar(chatEntry.message.user)

			# Enqeue the data to be picked up in run()
			self.queue.put(chatEntry)
		except Exception as e:
			print "An error in the AvatarFindThread: ", str(e)

	def run(self):
		cache = Cache()
		lastCall = 0
		wait = 300  # time between 2 requests in ms
		while True:
			try:
				# Block waiting for addChatEntry() to enqueue something
				chatEntry = self.queue.get()
				charname = chatEntry.message.user
				avatar = None
				if not avatar:
					avatar = cache.getAvatar(charname)
				if not avatar:
					diffLastCall = time.time() - lastCall
					if diffLastCall < wait:
						time.sleep((wait - diffLastCall) / 1000.0)
					avatar = evegate.getAvatarForPlayer(charname)
					lastCall = time.time()
					if avatar:
						cache.putAvatar(charname, avatar)
				if avatar:
					self.emit(SIGNAL("avatar_update"), chatEntry, avatar)
			except Exception as e:
				print "An error in the AvatarFindThread : {0}".format(str(e))


class KOSCheckerThread(QThread):
	def __init__(self):
		QThread.__init__(self)
		self.queue = Queue()
		self.recentRequestNamesAndTimes = {}

	def addRequest(self, names, requestType, onlyKos=False):
		try:
			# Spam control for multi-client users
			now = time.time()
			if self.recentRequestNamesAndTimes.has_key(names):
				lastRequestTime = self.recentRequestNamesAndTimes[names]
				if now - lastRequestTime < 10:
					return
			self.recentRequestNamesAndTimes[names] = now

			# Enqeue the data to be picked up in run()
			self.queue.put((names, requestType, onlyKos))
		except Exception as e:
			print "An error in the KOSCheckerThread: {0}".format(str(e))


	def run(self):
		while True:
			# Block waiting for addRequest() to enqueue something
			names, requestType, onlyKos = self.queue.get()
			try:
				hasKos = False
				if not names:
					continue
				checkResult = koschecker.check(names)
				if not checkResult:
					continue
				text = koschecker.resultToText(checkResult, onlyKos)
				for name, data in checkResult.items():
					if data["kos"] in (koschecker.KOS, koschecker.RED_BY_LAST):
						hasKos = True
						break
			except Exception as e:
				print "An error in the KOSCheckerThread : {0}".format(str(e))
				continue

			print "KOSCheckerThread emitting kos_result for: state = {0}, text = {1}, requestType = {2}, hasKos = {3}".format("ok", text, requestType, hasKos)
			self.emit(SIGNAL("kos_result"), "ok", text, requestType, hasKos)


class MapStatisticsThread(QThread):
	def __init__(self):
		QThread.__init__(self)

	def run(self):
		try:
			statistics = evegate.getSystemStatistics()
			time.sleep(20)  # sleeping to prevent a "need 2 arguments"-error
			result = {"result": "ok", "statistics": statistics}
		except Exception as e:
			print "An error in the MapStatisticsThread: {0}".format(str(e))
			result = {"result": "error", "text": unicode(e)}
		self.emit(SIGNAL("statistic_data_update"), result)
