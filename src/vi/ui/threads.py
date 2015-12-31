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
		self.q = Queue()

	def addChatEntry(self, chatEntry, clearCache=False):
		try:
			if clearCache:
				cache = Cache()
				cache.removeAvatar(chatEntry.message.user)
			self.q.put(chatEntry)
		except Exception as e:
			print "An error in the AvatarFindThread: ", str(e)

	def run(self):
		cache = Cache()
		lastCall = 0
		wait = 300  # time between 2 requests in ms
		while True:
			try:
				chatEntry = self.q.get()
				charname = chatEntry.message.user
				avatar = None
				if charname == "VINTEL":
					with open(resourcePath("vi/ui/res/logo_small.png"), "rb") as f:
						avatar = f.read()
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
		self.q = Queue()
		self.recentRequestNames = {}

	def addRequest(self, names, requestType, onlyKos=False):
		try:
			self.q.put((names, requestType, onlyKos))
		except Exception as e:
			print "An error in the KOSCheckerThread: {0}".format(str(e))


	def run(self):
		while True:
			names, requestType, onlyKos = self.q.get()
			namesCopy, names = itertools.tee(names, 2)

			# Prevent the same request from multiple clients on the same machine
			namesString = ', '.join(map(str, [name.strip() for name in namesCopy]))
			if self.recentRequestNames.has_key(namesString):
				requestTime = self.recentRequestNames[namesString]
				timeTime = time.time()
				print str(timeTime - requestTime)
				if time.time() - requestTime < 10:
					continue

			try:
				hasKos = False
				state = "ok"
				checkResult = koschecker.check(names)
				text = koschecker.resultToText(checkResult, onlyKos)
				for name, data in checkResult.items():
					if data["kos"] in (koschecker.KOS, koschecker.RED_BY_LAST):
						hasKos = True
						break
			except Exception as e:
				state = "error"
				text = unicode(e)
				print "An error in the KOSCheckerThread : {0}".format(str(e))
			print "KOSCheckerThread emitting kos_result for: state = {0}, text = {1}, requestType = {2}, hasKos = {3}".format(state, text, requestType, hasKos)
			self.recentRequestNames[namesString] = time.time()
			self.emit(SIGNAL("kos_result"), state, text, requestType, hasKos)


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
		time.sleep(20)
