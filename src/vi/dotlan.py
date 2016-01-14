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

###########################################################################
# Little lib and tool to get the map and information from dotlan		  #
###########################################################################

import math
import time
import urllib2

from bs4 import BeautifulSoup
from vi import states
from vi.cache.cache import Cache

import evegate

JB_COLORS = ("800000", "808000", "008080", "ff00ff", "c83737", "ff6600", "917c6f", "ffcc00", "88aa00")

class DotlanException(Exception):

	def __init__(self, *args, **kwargs):
		Exception.__init__(self, *args, **kwargs)


class Map(object):
	""" The map incl. all informations from dotlan
	"""

	DOTLAN_BASIC_URL = u"http://evemaps.dotlan.net/svg/{0}.svg"

	@property
	def svg(self):
		# Re-render all systems
		for system in self.systems.values():
			system.update()
		# update the marker
		if not self.marker["opacity"] == "0":
			now = time.time()
			newValue = (1 - (now - float(self.marker["activated"]))/10)
			if newValue < 0:
				newValue = "0"
			self.marker["opacity"] = newValue
		content = str(self.soup)
		return content

	def __init__(self, region, svgFile=None):
		self.region = region
		cache = Cache()
		self.outdatedCacheError = None

		if not svgFile:
			# want map from dotlan. Is it in the cache?
			svg = cache.getFromCache("map_" + self.region)
		else:
			svg = svgFile

		if not svg:
			try:
				svg = self._getSvgFromDotlan(self.region)
				cache.putIntoCache("map_" + self.region, svg, evegate.secondsTillDowntime() + 60*60)
			except Exception as e:
				self.outdatedCacheError = e
				svg = cache.getFromCache("map_" + self.region, True)
				if not svg:
					t = "No Map in cache, nothing from dotlan. Must give up "\
						"because this happened:\n{0} {1}\n\nThis could be a "\
						"temporary problem (like dotlan is not reachable), or "\
						"everythig went to hell. Sorry. This makes no sense "\
						"without the map.\n\nRemember the site for possible "\
						"updates: https://github.com/XanthosX/vintel"\
						.format(type(e), unicode(e))
					raise DotlanException(t)
		# and now creating soup from the svg
		self.soup = BeautifulSoup(svg, 'html.parser')
		self.systems = self._extractSystemsFromSoup(self.soup)
		self.systemsById = {}
		for system in self.systems.values():
			self.systemsById[system.systemId] = system
		self._preparingSvg(self.soup, self.systems)
		self._connectNeighbours()
		self._jumpmapsVisible = False
		self._statisticsVisible = False
		self.marker = self.soup.select("#select_marker")[0]

	def changeJumpbrigdeVisibility(self):
		newStatus = False if self._jumpmapsVisible else True
		value = "visible" if newStatus else "hidden"
		for line in self.soup.select(".jumpbridge"):
			line["visibility"] = value
		self._jumpmapsVisible = newStatus

	def changeStatisticsVisibility(self):
		newStatus = False if self._statisticsVisible else True
		value = "visible" if newStatus else "hidden"
		for line in self.soup.select(".statistics"):
			line["visibility"] = value
		self._statisticsVisible = newStatus

	def _extractSystemsFromSoup(self, soup):
		systems = {}
		uses = {}
		for use in soup.select("use"):
			useId = use["xlink:href"][1:]
			uses[useId] = use
		symbols = soup.select("symbol")
		for symbol in symbols:
			symbolId = symbol["id"]
			systemId = symbolId[3:]
			# workaround for sov changes 7/2015
			try:
				systemId = int(systemId)
			except ValueError as e:
				continue
			for element in symbol.select(".sys"):
				name = element.select("text")[0].text.strip().upper()
				mapCoordinates = {}
				for keyname in ("x", "y", "width", "height"):
					mapCoordinates[keyname] = float(uses[symbolId][keyname])
				mapCoordinates["center_x"] = (mapCoordinates["x"] + (mapCoordinates["width"] / 2))
				mapCoordinates["center_y"] = (mapCoordinates["y"] + (mapCoordinates["height"] / 2))
				systems[name] = System(name, element, self.soup, mapCoordinates, systemId)
		return systems


	def _connectNeighbours(self):
		""" This will find all neigbours of the systems and connect them.
			It takes a look to all the jumps on the map and get the system under
			which the line ends
		"""
		for jump in self.soup.select("#jumps")[0].select(".j"):
			if "jumpbridge" in jump["class"]: continue
			parts = jump["id"].split("-")
			if parts[0] == "j":
				startSystem = self.systemsById[int(parts[1])]
				stopSystem = self.systemsById[int(parts[2])]
				startSystem.addNeighbour(stopSystem)

	def _getSvgFromDotlan(self, region):
		url = self.DOTLAN_BASIC_URL.format(region)
		request = urllib2.Request(url)
		content = urllib2.urlopen(request).read()
		return content

	def addSystemStatistics(self, statistics):
		if statistics is not None:
			for systemId, system in self.systemsById.items():
				if systemId in statistics:
					system.setStatistics(statistics[systemId])
		else:
			for system in self.self.systemsById.values():
				system.setStatistics(None)

	def setJumpbridges(self, jumpbridgeData):
		""" adding the jumpbridges to the map
			format of data: tuples with 3 values (sys1, connection, sys2)
		"""
		soup = self.soup
		for bridge in soup.select(".jumpbridge"):
			bridge.decompose()
		jumps = soup.select("#jumps")[0]
		colorCount = 0
		for bridge in jumpbridgeData:
			if colorCount > len(JB_COLORS) - 1:
				colorCount = 0
			jbColor = JB_COLORS[colorCount]
			start = bridge[0]
			linetype = bridge[1]
			stop = bridge[2]
			if not (start in self.systems and stop in self.systems):
				continue
			self.systems[start].setJumpbridgeColor(jbColor)
			self.systems[stop].setJumpbridgeColor(jbColor)
			aCoords = self.systems[start].mapCoordinates
			bCoords = self.systems[stop].mapCoordinates
			line = soup.new_tag("line", x1 = aCoords["center_x"], y1 = aCoords["center_y"], x2 = bCoords["center_x"], y2 = bCoords["center_y"], visibility = "hidden", style = "stroke:#{0}".format(jbColor))
			line["stroke-width"] = 2
			line["class"] = ["jumpbridge",]
			if "<" in linetype:
				line["marker-start"] = "url(#arrowstart_{0})".format(jbColor)
			if ">" in linetype:
				line["marker-end"] = "url(#arrowend_{0})".format(jbColor)
			jumps.insert(0, line)
			colorCount += 1

	def _preparingSvg(self, soup, systems):
		svg = soup.select("svg")[0]
		svg["onmousedown"] = "return false;"
		# making all jumps black
		for line in soup.select("line"):
			line["class"] = "j"

		# the marker we use for marking a selected system
		group = soup.new_tag("g", id = "select_marker", opacity = "0", activated = "0", transform = "translate(-10000, -10000)")
		ellipse = soup.new_tag("ellipse", cx = "0", cy = "0", rx = "56", ry = "28", style = "fill:#462CFF")
		group.append(ellipse)
		coords = ((0, -10000), (-10000, 0), (10000, 0), (0, 10000))

		for coord in coords:
			line = soup.new_tag("line", x1 = coord[0], y1 = coord[1], x2 = "0", y2 = "0", style = "stroke:#462CFF")
			group.append(line)
		svg.insert(0, group)

		# marker for jumpbridges
		for jbColor in JB_COLORS:
			startPath = soup.new_tag("path", d="M 10 0 L 10 10 L 0 5 z")
			startMarker = soup.new_tag("marker", viewBox="0 0 20 20",
				id="arrowstart_{0}".format(jbColor),
				markerUnits="strokeWidth", markerWidth="20", markerHeight="15",
				refx="-15", refy="5", orient="auto",
				style="stroke:#{0};fill:#{0}".format(jbColor))
			startMarker.append(startPath)
			svg.insert(0, startMarker)
			endpath = soup.new_tag("path", d="M 0 0 L 10 5 L 0 10 z")
			endmarker = soup.new_tag("marker", viewBox="0 0 20 20",
				id="arrowend_{0}".format(jbColor),
				markerUnits="strokeWidth", markerWidth="20", markerHeight="15",
				refx="25", refy="5", orient="auto",
				style="stroke:#{0};fill:#{0}".format(jbColor))
			endmarker.append(endpath)
			svg.insert(0, endmarker)
		jumps = soup.select("#jumps")[0]

		for systemId, system in self.systemsById.items():
			coords = system.mapCoordinates
			stats = system.statistics
			text = "stats n/a"
			style = "text-anchor:middle;font-size:7;font-family:Arial;"
			svgtext = soup.new_tag("text", x=coords["center_x"], y=coords["y"] + coords["height"] + 7, fill="blue", style=style, visibility="hidden")
			svgtext["id"] = "stats_" +	str(systemId)
			svgtext["class"] = ["statistics",]
			svgtext.string = text
			jumps.append(svgtext)


class System(object):
	""" A System in the Map
	"""

	ALARM_COLORS = [(60*4, "#FF0000", "FFFFFF"), (60*10, "#FF9B0F", "#FFFFFF"),
					(60*15, "#FFFA0F", "#000000"), (60*25, "#FFFDA2", "#000000"),
					(60*60*24, "#FFFFFF", "#000000")]
	ALARM_COLOR = ALARM_COLORS[0][1]
	UNKNOWN_COLOR = "#FFFFFF"
	CLEAR_COLOR = "#59FF6C"

	def __init__(self, name, svgElement, mapSoup, mapCoordinates, systemId):
		self.status = states.UNKNOWN
		self.name = name
		self.svgElement = svgElement
		self.mapSoup = mapSoup
		self.origSvgElement = svgElement
		self.rect =	 svgElement.select("rect")[0]
		self.secondLine = svgElement.select("text")[1]
		self.lastAlarmTime = 0
		self.messages = []
		self.setStatus(states.UNKNOWN)
		self.__locatedCharacters = []
		self.backgroundColor = "#FFFFFF"
		self.mapCoordinates = mapCoordinates
		self.systemId = systemId
		self._neighbours = set()
		self.statistics = {"jumps": "?", "shipkills": "?", "factionkills": "?", "podkills": "?"}

	def setJumpbridgeColor(self, color):
		idName = self.name + u"_jb_marker"
		for element in self.mapSoup.select(u"#" + idName):
			element.decompose()
		coords = self.mapCoordinates
		style = "fill:{0};stroke:{0};stroke-width:2;fill-opacity:0.4"
		tag = self.mapSoup.new_tag("rect", x=coords["x"]-3, y=coords["y"],
			width=coords["width"]+1.5, height=coords["height"], id=idName,
			style=style.format(color), visibility="hidden")
		tag["class"] = ["jumpbridge",]
		jumps = self.mapSoup.select("#jumps")[0]
		jumps.insert(0, tag)

	def mark(self):
		marker = self.mapSoup.select("#select_marker")[0]
		x = self.mapCoordinates["center_x"]
		y = self.mapCoordinates["center_y"]
		marker["transform"] = "translate({x},{y})".format(x=x, y=y)
		marker["opacity"] = "1"
		marker["activated"] = time.time()

	def addLocatedCharacter(self, charname):
		idName = self.name + u"_loc"
		wasLocated = bool(self.__locatedCharacters)
		if charname not in self.__locatedCharacters:
			self.__locatedCharacters.append(charname)
		if not wasLocated:
			coords = self.mapCoordinates
			newTag = self.mapSoup.new_tag(
				"ellipse", cx=coords["center_x"]-2.5, cy=coords["center_y"],
				id=idName, rx=coords["width"]/2+4, ry=coords["height"]/2+4,
				style="fill:#8b008d")
			jumps = self.mapSoup.select("#jumps")[0]
			jumps.insert(0, newTag)

	def setBackgroundColor(self, color):
		for rect in self.svgElement("rect"):
			if "location" not in rect.get("class", []) and "marked" not in rect.get("class", []):
				rect["style"] = "fill: {0};".format(color)

	def getLocatedCharacters(self):
		characters = []
		for char in self.__locatedCharacters:
			characters.append(char)
		return characters

	def removeLocatedCharacter(self, charname):
		idName = self.name + u"_loc"

		if charname in self.__locatedCharacters:
			self.__locatedCharacters.remove(charname)
			if not self.__locatedCharacters:
				for element in self.mapSoup.select("#" + idName):
					element.decompose()

	def addNeighbour(self, neighbourSystem):
		""" Add a neigbour system to this system
			neighbour_system: a system (not a system's name!)
		"""
		self._neighbours.add(neighbourSystem)
		neighbourSystem._neighbours.add(self)

	def getNeighbours(self, distance=1):
		""" Get all neigboured system with a distance of distance.
			example: sys1 <-> sys2 <-> sys3 <-> sys4 <-> sys5
					 sys3(distance=1) will find sys2, sys3, sys4
					 sys3(distance=2) will find sys1, sys2, sys3, sys4, sys5
			returns a dictionary with the system (not the system's name!)
					as key and a dict as value. key "distance" contains the
					distance. for first example:
							  {sys3: {"distance"}: 0, sys2: {"distance"}: 1}
		"""
		neighbours = []
		systems = {self: {"distance": 0}}
		currentDistance = 0
		while currentDistance < distance:
			currentDistance += 1
			newSystems = []
			for system in systems.keys():
				for neighbour in system._neighbours:
					if neighbour not in systems:
						newSystems.append(neighbour)
			for newSystem in newSystems:
				systems[newSystem] = {"distance": currentDistance}
		return systems

	def removeNeighbour(self, system):
		""" Removes the link between to neighboured systems
		"""
		if system in self._neighbours:
			self._neighbours.remove(system)
		if self in system._neighbours:
			system._neigbours.remove(self)

	def setStatus(self, newStatus):
		if newStatus == states.ALARM:
			self.lastAlarmTime = time.time()
			if "stopwatch" not in self.secondLine["class"]:
				self.secondLine["class"].append("stopwatch")
			self.secondLine["alarmtime"] = self.lastAlarmTime
			self.secondLine["style"] = "fill: #FFFFFF;"
			self.setBackgroundColor(self.ALARM_COLOR)
		elif newStatus == states.CLEAR:
			self.lastAlarmTime = time.time()
			self.setBackgroundColor(self.CLEAR_COLOR)
			self.secondLine["alarmtime"] = 0
			if "stopwatch" not in self.secondLine["class"]:
				self.secondLine["class"].append("stopwatch")
			self.secondLine["alarmtime"] = self.lastAlarmTime
			self.secondLine["style"] = "fill: #000000;"
			self.secondLine.string = "clear"
		elif newStatus == states.WAS_ALARMED:
			self.setBackgroundColor(self.UNKNOWN_COLOR)
			self.secondLine["style"] = "fill: #000000;"
		elif newStatus == states.UNKNOWN:
			self.setBackgroundColor(self.UNKNOWN_COLOR)
			# second line in the rects is reserved for the clock
			self.secondLine.string = "?"
			self.secondLine["style"] = "fill: #000000;"
		if newStatus not in (states.NOT_CHANGE, states.REQUEST):  # unknon not affect system status
			self.status = newStatus

	def setStatistics(self, statistics):
		if statistics is None:
			text = "stats n/a"
		else:
			text = "J:{jumps} | S:{shipkills} F:{factionkills} P:{podkills}".format(**statistics)
		svgtext = self.mapSoup.select("#stats_" +  str(self.systemId))[0]
		svgtext.string = text

	def update(self):
		# state changed?
		if (self.status == states.ALARM):
			alarmtime = time.time() - self.lastAlarmTime
			for maxDiff, alarmColor, secondLineColor in self.ALARM_COLORS:
				if alarmtime < maxDiff:
					if self.backgroundColor != alarmColor:
						self.backgroundColor = alarmColor
						for rect in self.svgElement("rect"):
							if "location" not in rect.get("class", []) and "marked" not in rect.get("class", []):
								rect["style"] = "fill: {0};".format(self.backgroundColor)
						self.secondLine["style"] = "fill: {0};".format(secondLineColor)
					break
		if self.status in (states.ALARM, states.WAS_ALARMED, states.CLEAR):	 # timer
			diff = math.floor(time.time() - self.lastAlarmTime)
			minutes = int(math.floor(diff / 60))
			seconds = int(diff - minutes * 60)
			string = "{m:02d}:{s:02d}".format(m=minutes, s=seconds)
			if self.status == states.CLEAR:
				g = 255
				secondsUntilWhite = 10*60
				calcValue = int(diff / (secondsUntilWhite / 255.0))
				if calcValue > 255:
					calcValue = 255
					self.secondLine["style"] = "fill: #008100;"
				string = "clr: {m:02d}:{s:02d}".format(m=minutes, s=seconds)
				self.setBackgroundColor("rgb({r},{g},{b})".format(g=g, r=calcValue, b=calcValue))
			self.secondLine.string = string


def convertRegionName(name):
	""" Converts a (system)name to the format that dotland uses
	"""
	converted = []
	nextUpper = False

	for index, char in enumerate(name):
		if index == 0:
			converted.append(char.upper())
		else:
			if char in (u" ", u"_"):
				char = "_"
				nextUpper = True
			else:
				if nextUpper:
					char = char.upper()
				else:
					char= char.lower()
				nextUpper = False
			converted.append(char)
	return u"".join(converted)


# this is for testing:
if __name__ == "__main__":
	map = Map("Providence", "Providence.svg")
	s = map.systems["I7S-1S"]
	s.setStatus(states.ALARM)
	print map.svg
