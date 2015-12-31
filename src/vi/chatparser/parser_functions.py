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

""" 12.02.2015
	I know this is a little bit dirty, but I prefer to have all the functions
	to parse the chat in this file together.
	Wer are now work directly with the html-formatted text, which we use to
	display it. We are using a HTML/XML-Parser to have the benefit, that we
	can only work and analyze those text, that is still not on tags, because
	all the text in tags was allready identified.
	f.e. the ship_parser:
		we call it from the chatparser and give them the rtext (richtext).
		if the parser hits a shipname, it will modifiy the tree by creating
		a new tag and replace the old text with it (calls tet_replace),
		than it returns True.
		The chatparser will call the function again until it return False
		(None is False) otherwise.
		We have to call the parser again after a hit, because a hit will change
		the tree and so the original generator is not longer stable.
"""

import vi.evegate as evegate
from bs4 import BeautifulSoup
from bs4.element import NavigableString
from vi import states

CHARS_TO_IGNORE = ("*", "?", ",", "!")


def textReplace(element, newText):
	newText = "<t>" + newText + "</t>"
	newElements = []
	for newPart in BeautifulSoup(newText, 'html.parser').select("t")[0].contents:
		newElements.append(newPart)
	for newElement in newElements:
		element.insert_before(newElement)
	element.replace_with(unicode(""))


def parseStatus(rtext):
	texts = [t for t in rtext.contents if isinstance(t, NavigableString)]
	for text in texts:
		utext = text.strip().upper()
		for char in CHARS_TO_IGNORE:
			utext = utext.replace(char, "")
		uwords = utext.split()
		if (("CLEAR" in uwords or "CLR" in uwords) and not utext.endswith("?")):
			return states.CLEAR
		elif ("STAT" in uwords or "STATUS" in uwords):
			return states.REQUEST
		elif ("?" in utext):
			return states.REQUEST
		elif (text.strip().upper() in ("BLUE", "BLUES ONLY", "ONLY BLUE" "STILL BLUE", "ALL BLUES")):
			return states.CLEAR


def parseShips(rtext):
	def formatShipName(text, word):
		newText = u"""<span style="color:#d95911;font-weight:bold"> {0}</span>"""
		text = text.replace(word, newText.format(word))
		return text

	texts = [t for t in rtext.contents if isinstance(t, NavigableString)]
	for text in texts:
		utext = text.upper()
		for shipName in evegate.SHIPNAMES:
			if shipName in utext:
				hit = True
				start = utext.find(shipName)
				end = start + len(shipName)
				if ((start > 0 and utext[start - 1] not in (" ", "X")) or (end < len(utext) - 1 and utext[end] not in ("S", " "))):
					hit = False
				if hit:
					shipInText = text[start:end]
					formatted = formatShipName(text, shipInText)
					textReplace(text, formatted)
					return True


def parseSystems(systems, rtext, foundSystems):
	# words to ignore on the system parser. use UPPER CASE
	WORDS_TO_IGNORE = ("IN", "IS", "AS")

	def formatSystem(text, word, system):
		newText = u"""<a style="color:#CC8800;font-weight:bold href="mark_system/{0}">{1}</a>"""
		text = text.replace(word, newText.format(system, word))
		return text

	systemNames = systems.keys()
	texts = [t for t in rtext.contents if isinstance(t, NavigableString)]
	for text in texts:
		worktext = text
		for char in CHARS_TO_IGNORE:
			worktext = worktext.replace(char, "")
		words = worktext.split(" ")
		for word in words:
			if len(word.strip()) == 0:
				continue
			uword = word.upper()
			if uword != word and uword in WORDS_TO_IGNORE: continue
			if uword in systemNames:  # - direct hit on name
				foundSystems.add(systems[uword])  # of the system?
				formattedText = formatSystem(text, word, uword)
				textReplace(text, formattedText)
				return True
			elif 1 < len(uword) < 5:  # - uword < 4 chars.
				for system in systemNames:  # system begins with?
					if system.startswith(uword):
						foundSystems.add(systems[system])
						formattedText = formatSystem(text, word, system)
						textReplace(text, formattedText)
						return True
			elif "-" in uword and len(uword) > 2:  # - short with - (minus)
				uwordParts = uword.split("-")  # (I-I will bis I43-IF3)
				for system in systemNames:
					systemParts = system.split("-")
					if (len(uwordParts) == 2 and len(systemParts) == 2 and len(uwordParts[0]) > 1 and len(
							uwordParts[1]) > 1 and len(systemParts[0]) > 1 and len(systemParts[1]) > 1 and len(
							uwordParts) == len(systemParts) and uwordParts[0][0] == systemParts[0][0] and uwordParts[1][
						0] == systemParts[1][0]):
						foundSystems.add(systems[system])
						formattedText = formatSystem(text, word, system)
						textReplace(text, formattedText)
						return True
			elif len(uword) > 1:  # what if F-YH58 is named FY?
				for system in systemNames:
					clearedSystem = system.replace("-", "")
					if clearedSystem.startswith(uword):
						foundSystems.add(systems[system])
						formattedText = formatSystem(text, word, system)
						textReplace(text, formattedText)
						return True


def parseUrls(rtext):
	def findUrls(s):
		# yes, this is faster than regex and less complex to read
		urls = []
		prefixes = ("http://", "https://")
		for prefix in prefixes:
			start = 0
			while start >= 0:
				start = s.find(prefix, start)
				if start >= 0:
					stop = s.find(" ", start)
					if stop < 0:
						stop = len(s)
					urls.append(s[start:stop])
					start += 1
		return urls

	def formatUrl(text, url):
		newText = u"""<a style="color:#28a5ed;font-weight:bold href="link/{0}">{0}</a>"""
		text = text.replace(url, newText.format(url))
		return text

	texts = [t for t in rtext.contents if isinstance(t, NavigableString)]
	for text in texts:
		urls = findUrls(text)
		for url in urls:
			textReplace(text, formatUrl(text, url))
			return True
