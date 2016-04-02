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
import six
import requests
import logging

from bs4 import BeautifulSoup
from vi import states
from vi.cache.cache import Cache

from . import evegate

JB_COLORS = ("800000", "808000", "BC8F8F", "ff00ff", "c83737", "FF6347", "917c6f", "ffcc00",
             "88aa00" "FFE4E1", "008080", "00BFFF", "4682B4", "00FF7F", "7FFF00", "ff6600",
             "CD5C5C", "FFD700", "66CDAA", "AFEEEE", "5F9EA0", "FFDEAD", "696969", "2F4F4F")


class DotlanException(Exception):
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)


class Map(object):
    """
        The map including all information from dotlan
    """

    DOTLAN_BASIC_URL = u"http://evemaps.dotlan.net/svg/{0}.svg"

    @property
    def svg(self):
        # Re-render all systems
        for system in self.systems.values():
            system.update()
        # Update the marker
        if not self.marker["opacity"] == "0":
            now = time.time()
            newValue = (1 - (now - float(self.marker["activated"])) / 10)
            if newValue < 0:
                newValue = "0"
            self.marker["opacity"] = newValue
        content = str(self.soup)
        return content

    def __init__(self, region, svgFile=None):
        self.region = region
        cache = Cache()
        self.outdatedCacheError = None

        # Get map from dotlan if not in the cache
        if not svgFile:
            svg = cache.getFromCache("map_" + self.region)
        else:
            svg = svgFile
        if not svg:
            try:
                svg = self._getSvgFromDotlan(self.region)
                cache.putIntoCache("map_" + self.region, svg, evegate.secondsTillDowntime() + 60 * 60)
            except Exception as e:
                self.outdatedCacheError = e
                svg = cache.getFromCache("map_" + self.region, True)
                if not svg:
                    t = "No Map in cache, nothing from dotlan. Must give up " \
                        "because this happened:\n{0} {1}\n\nThis could be a " \
                        "temporary problem (like dotlan is not reachable), or " \
                        "everythig went to hell. Sorry. This makes no sense " \
                        "without the map.\n\nRemember the site for possible " \
                        "updates: https://github.com/Xanthos-Eve/vintel".format(type(e), six.text_type(e))
                    raise DotlanException(t)
        # Create soup from the svg
        self.soup = BeautifulSoup(svg, 'html.parser')
        self.systems = self._extractSystemsFromSoup(self.soup)
        self.systemsById = {}
        for system in self.systems.values():
            self.systemsById[system.systemId] = system
        self._prepareSvg(self.soup, self.systems)
        self._connectNeighbours()
        self._jumpMapsVisible = False
        self._statisticsVisible = False
        self.marker = self.soup.select("#select_marker")[0]

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
                try:
                    transform = uses[symbolId]["transform"]
                except KeyError:
                    transform = "translate(0,0)"
                systems[name] = System(name, element, self.soup, mapCoordinates, transform, systemId)
        return systems

    def _prepareSvg(self, soup, systems):
        svg = soup.select("svg")[0]
        # Disable dotlan mouse functionality and make all jump lines black
        svg["onmousedown"] = "return false;"
        for line in soup.select("line"):
            line["class"] = "j"

        # Current system marker ellipse
        group = soup.new_tag("g", id="select_marker", opacity="0", activated="0", transform="translate(0, 0)")
        ellipse = soup.new_tag("ellipse", cx="0", cy="0", rx="56", ry="28", style="fill:#462CFF")
        group.append(ellipse)

        # The giant cross-hairs
        for coord in ((0, -10000), (-10000, 0), (10000, 0), (0, 10000)):
            line = soup.new_tag("line", x1=coord[0], y1=coord[1], x2="0", y2="0", style="stroke:#462CFF")
            group.append(line)
        svg.insert(0, group)

        # Create jumpbridge markers in a variety of colors
        for jbColor in JB_COLORS:
            startPath = soup.new_tag("path", d="M 10 0 L 10 10 L 0 5 z")
            startMarker = soup.new_tag("marker", viewBox="0 0 20 20", id="arrowstart_{0}".format(jbColor),
                                       markerUnits="strokeWidth", markerWidth="20", markerHeight="15", refx="-15",
                                       refy="5", orient="auto", style="stroke:#{0};fill:#{0}".format(jbColor))
            startMarker.append(startPath)
            svg.insert(0, startMarker)
            endpath = soup.new_tag("path", d="M 0 0 L 10 5 L 0 10 z")
            endmarker = soup.new_tag("marker", viewBox="0 0 20 20", id="arrowend_{0}".format(jbColor),
                                     markerUnits="strokeWidth", markerWidth="20", markerHeight="15", refx="25",
                                     refy="5", orient="auto", style="stroke:#{0};fill:#{0}".format(jbColor))
            endmarker.append(endpath)
            svg.insert(0, endmarker)
        jumps = soup.select("#jumps")[0]

        # Set up the tags for system statistics
        for systemId, system in self.systemsById.items():
            coords = system.mapCoordinates
            text = "stats n/a"
            style = "text-anchor:middle;font-size:8;font-weight:normal;font-family:Arial;"
            svgtext = soup.new_tag("text", x=coords["center_x"], y=coords["y"] + coords["height"] + 6, fill="blue",
                                   style=style, visibility="hidden", transform=system.transform)
            svgtext["id"] = "stats_" + str(systemId)
            svgtext["class"] = ["statistics", ]
            svgtext.string = text
            jumps.append(svgtext)

    def _connectNeighbours(self):
        """
            This will find all neighbours of the systems and connect them.
            It takes a look at all the jumps on the map and gets the system under
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
        content = requests.get(url).text
        return content

    def addSystemStatistics(self, statistics):
        logging.info("addSystemStatistics start")
        if statistics is not None:
            for systemId, system in self.systemsById.items():
                if systemId in statistics:
                    system.setStatistics(statistics[systemId])
        else:
            for system in self.systemsById.values():
                system.setStatistics(None)
        logging.info("addSystemStatistics complete")


    def setJumpbridges(self, jumpbridgesData):
        """
            Adding the jumpbridges to the map soup; format of data:
            tuples with 3 values (sys1, connection, sys2)
        """
        soup = self.soup
        for bridge in soup.select(".jumpbridge"):
            bridge.decompose()
        jumps = soup.select("#jumps")[0]
        colorCount = 0

        for bridge in jumpbridgesData:
            sys1 = bridge[0]
            connection = bridge[1]
            sys2 = bridge[2]
            if not (sys1 in self.systems and sys2 in self.systems):
                continue

            if colorCount > len(JB_COLORS) - 1:
                colorCount = 0
            jbColor = JB_COLORS[colorCount]
            colorCount += 1
            systemOne = self.systems[sys1]
            systemTwo = self.systems[sys2]
            systemOneCoords = systemOne.mapCoordinates
            systemTwoCoords = systemTwo.mapCoordinates
            systemOneOffsetPoint = systemOne.getTransformOffsetPoint()
            systemTwoOffsetPoint = systemTwo.getTransformOffsetPoint()

            systemOne.setJumpbridgeColor(jbColor)
            systemTwo.setJumpbridgeColor(jbColor)

            # Construct the line, color it and add it to the jumps
            line = soup.new_tag("line", x1=systemOneCoords["center_x"] + systemOneOffsetPoint[0],
                                y1=systemOneCoords["center_y"] + systemOneOffsetPoint[1],
                                x2=systemTwoCoords["center_x"] + systemTwoOffsetPoint[0],
                                y2=systemTwoCoords["center_y"] + systemTwoOffsetPoint[1], visibility="hidden",
                                style="stroke:#{0}".format(jbColor))
            line["stroke-width"] = 2
            line["class"] = ["jumpbridge", ]
            if "<" in connection:
                line["marker-start"] = "url(#arrowstart_{0})".format(jbColor)
            if ">" in connection:
                line["marker-end"] = "url(#arrowend_{0})".format(jbColor)
            jumps.insert(0, line)

    def changeStatisticsVisibility(self):
        newStatus = False if self._statisticsVisible else True
        value = "visible" if newStatus else "hidden"
        for line in self.soup.select(".statistics"):
            line["visibility"] = value
        self._statisticsVisible = newStatus
        return newStatus

    def changeJumpbridgesVisibility(self):
        newStatus = False if self._jumpMapsVisible else True
        value = "visible" if newStatus else "hidden"
        for line in self.soup.select(".jumpbridge"):
            line["visibility"] = value
        self._jumpMapsVisible = newStatus
        # self.debugWriteSoup()
        return newStatus

    def debugWriteSoup(self):
        svgData = self.soup.prettify("utf-8")
        try:
            with open("/Users/mark/Desktop/output.svg", "wb") as svgFile:
                svgFile.write(svgData)
                svgFile.close()
        except Exception as e:
            logging.error(e)


class System(object):
    """
        A System on the Map
    """

    ALARM_COLORS = [(60 * 4, "#FF0000", "#FFFFFF"), (60 * 10, "#FF9B0F", "#FFFFFF"), (60 * 15, "#FFFA0F", "#000000"),
                    (60 * 25, "#FFFDA2", "#000000"), (60 * 60 * 24, "#FFFFFF", "#000000")]
    ALARM_COLOR = ALARM_COLORS[0][1]
    UNKNOWN_COLOR = "#FFFFFF"
    CLEAR_COLOR = "#59FF6C"

    def __init__(self, name, svgElement, mapSoup, mapCoordinates, transform, systemId):
        self.status = states.UNKNOWN
        self.name = name
        self.svgElement = svgElement
        self.mapSoup = mapSoup
        self.origSvgElement = svgElement
        self.rect = svgElement.select("rect")[0]
        self.secondLine = svgElement.select("text")[1]
        self.lastAlarmTime = 0
        self.messages = []
        self.setStatus(states.UNKNOWN)
        self.__locatedCharacters = []
        self.backgroundColor = "#FFFFFF"
        self.mapCoordinates = mapCoordinates
        self.systemId = systemId
        self.transform = transform
        self.cachedOffsetPoint = None
        self._neighbours = set()
        self.statistics = {"jumps": "?", "shipkills": "?", "factionkills": "?", "podkills": "?"}

    def getTransformOffsetPoint(self):
        if not self.cachedOffsetPoint:
            if self.transform:
                # Convert data in the form 'transform(0,0)' to a list of two floats
                pointString = self.transform[9:].strip('()').split(',')
                self.cachedOffsetPoint = [float(pointString[0]), float(pointString[1])]
            else:
                self.cachedOffsetPoint = [0.0, 0.0]
        return self.cachedOffsetPoint

    def setJumpbridgeColor(self, color):
        idName = self.name + u"_jb_marker"
        for element in self.mapSoup.select(u"#" + idName):
            element.decompose()
        coords = self.mapCoordinates
        offsetPoint = self.getTransformOffsetPoint()
        x = coords["x"] - 3 + offsetPoint[0]
        y = coords["y"] + offsetPoint[1]
        style = "fill:{0};stroke:{0};stroke-width:2;fill-opacity:0.4"
        tag = self.mapSoup.new_tag("rect", x=x, y=y, width=coords["width"] + 1.5, height=coords["height"], id=idName, style=style.format(color), visibility="hidden")
        tag["class"] = ["jumpbridge", ]
        jumps = self.mapSoup.select("#jumps")[0]
        jumps.insert(0, tag)

    def mark(self):
        marker = self.mapSoup.select("#select_marker")[0]
        offsetPoint = self.getTransformOffsetPoint()
        x = self.mapCoordinates["center_x"] + offsetPoint[0]
        y = self.mapCoordinates["center_y"] + offsetPoint[1]
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
            newTag = self.mapSoup.new_tag("ellipse", cx=coords["center_x"] - 2.5, cy=coords["center_y"], id=idName,
                    rx=coords["width"] / 2 + 4, ry=coords["height"] / 2 + 4, style="fill:#8b008d",
                    transform=self.transform)
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
        """
            Add a neigbour system to this system
            neighbour_system: a system (not a system's name!)
        """
        self._neighbours.add(neighbourSystem)
        neighbourSystem._neighbours.add(self)

    def getNeighbours(self, distance=1):
        """
            Get all neigboured system with a distance of distance.
            example: sys1 <-> sys2 <-> sys3 <-> sys4 <-> sys5
            sys3(distance=1) will find sys2, sys3, sys4
            sys3(distance=2) will find sys1, sys2, sys3, sys4, sys5
            returns a dictionary with the system (not the system's name!)
            as key and a dict as value. key "distance" contains the distance.
            example:
            {sys3: {"distance"}: 0, sys2: {"distance"}: 1}
        """
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
        """
            Removes the link between to neighboured systems
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
        if newStatus not in (states.NOT_CHANGE, states.REQUEST):  # unknown not affect system status
            self.status = newStatus

    def setStatistics(self, statistics):
        if statistics is None:
            text = "stats n/a"
        else:
            text = "j-{jumps} f-{factionkills} s-{shipkills} p-{podkills}".format(**statistics)
        svgtext = self.mapSoup.select("#stats_" + str(self.systemId))[0]
        svgtext.string = text

    def update(self):
        # state changed?
        if (self.status == states.ALARM):
            alarmTime = time.time() - self.lastAlarmTime
            for maxDiff, alarmColor, secondLineColor in self.ALARM_COLORS:
                if alarmTime < maxDiff:
                    if self.backgroundColor != alarmColor:
                        self.backgroundColor = alarmColor
                        for rect in self.svgElement("rect"):
                            if "location" not in rect.get("class", []) and "marked" not in rect.get("class", []):
                                rect["style"] = "fill: {0};".format(self.backgroundColor)
                        self.secondLine["style"] = "fill: {0};".format(secondLineColor)
                    break
        if self.status in (states.ALARM, states.WAS_ALARMED, states.CLEAR):  # timer
            diff = math.floor(time.time() - self.lastAlarmTime)
            minutes = int(math.floor(diff / 60))
            seconds = int(diff - minutes * 60)
            string = "{m:02d}:{s:02d}".format(m=minutes, s=seconds)
            if self.status == states.CLEAR:
                secondsUntilWhite = 10 * 60
                calcValue = int(diff / (secondsUntilWhite / 255.0))
                if calcValue > 255:
                    calcValue = 255
                    self.secondLine["style"] = "fill: #008100;"
                string = "clr: {m:02d}:{s:02d}".format(m=minutes, s=seconds)
                self.setBackgroundColor("rgb({r},{g},{b})".format(r=calcValue, g=255, b=calcValue))
            self.secondLine.string = string


def convertRegionName(name):
    """
        Converts a (system)name to the format that dotland uses
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
                    char = char.lower()
                nextUpper = False
            converted.append(char)
    return u"".join(converted)


# this is for testing:
if __name__ == "__main__":
    map = Map("Providence", "Providence.svg")
    s = map.systems["I7S-1S"]
    s.setStatus(states.ALARM)
    logging.error(map.svg)
