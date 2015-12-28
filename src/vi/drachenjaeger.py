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

import urllib2
import json

from PyQt4 import Qt
from PyQt4.QtCore import QThread
from bs4 import BeautifulSoup

from vi.cache.cache import Cache
from vi import version
 
def getJumpbridgeData(region):
	try:
		cacheKey = "jb_" + region
		cache = Cache()
		data = cache.getFromCache(cacheKey)
		
		if data:
			data = json.loads(data)
		else:
			data = []
			url = "http://drachenjaeger.eu/vintel/{region}_jb.txt"
			request = urllib2.urlopen(url.format(region=region))
			content = request.read()
			for line in content.split("\n"):
				splits = line.strip().split()
				if len(splits) == 3:
					data.append(splits)
			cache.putIntoCache(cacheKey, json.dumps(data), 60*60*24)
		return data
	except Exception as e:
		print("Getting Jumpbridgedata failed with: {0}".format(str(e)))
		return []
		
		
def getNewestVersion():
	try:
		url = "http://drachenjaeger.eu/vintel/vintel.html"
		request = urllib2.urlopen(url)
		content = request.read()
		soup = BeautifulSoup(content, 'html.parser')
		newestVersion = soup.select("#version")[0].text
		return float(newestVersion)
	except Exception as e:
		print("Failed version-request: {0}".format(str(e)))
		return 0.0


class NotifyNewVersionThread(QThread):
	
	def __init__(self):
		QThread.__init__(self)

	def run(self):
		try:
		# is there a newer version available?
			newestVersion = float(getNewestVersion())
			if newestVersion and newestVersion > float(version.VERSION):
				self.emit(Qt.SIGNAL("newer_version"), newestVersion)
		except Exception as e:
			print("Failed NotifyNewVersionThread: {0}".format(str(e)))
