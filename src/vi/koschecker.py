###########################################################################
#  Vintel - Visual Intel Chat Analyzer                                    #
#  Copyright (C) 2014-15 Sebastian Meyer (sparrow.242.de+eve@gmail.com )  #
#                                                                         #
#  This program is free software: you can redistribute it and/or modify   #
#  it under the terms of the GNU General Public License as published by   #
#  the Free Software Foundation, either version 3 of the License, or      #
#  (at your option) any later version.                                    #
#                                                                         #
#  This program is distributed in the hope that it will be useful,        #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of         #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the          #
#  GNU General Public License for more details.                           #
#                                                                         #
#                                                                         #
#  You should have received a copy of the GNU General Public License      #
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.  #
###########################################################################

import json
import urllib
import urllib2

from vi import evegate
from vi.cache.cache import Cache

UNKNOWN = "?"
NOT_KOS = 'NOT kos'
KOS = "KOS"
RED_BY_LAST = "RED by last"

def check(parts):

	data = {}
	baseUrl = "http://kos.cva-eve.org/api/?c=json&type=multi&q="
	names = [name.strip() for name in parts]
	checkBylastChars = []
	quotedNames = urllib.quote_plus(",".join(names))
	targetUrl = "".join((baseUrl, quotedNames))

	try:
		request = urllib2.urlopen(targetUrl)
	except URLError as e:
		print "Error on pilot KOS check request" + e.reason
	
	kosData = json.loads(request.read())
	
	for char in kosData["results"]:
		charName = char["label"]
		corpname = char["corp"]["label"]
		names.remove(charName)
		
		if char["kos"] or char["corp"]["kos"] or char["corp"]["alliance"]["kos"]:
			data[charName] = {"kos": KOS}
		elif corpname not in evegate.NPC_CORPS:
			data[charName] = {"kos": NOT_KOS}
		else:
			if char not in checkBylastChars:
				checkBylastChars.append(charName)
	
	for name in names:  # Still names there (the kos checker not found) ?
		checkBylastChars.append(name)
	
	# Deeper check
	deeperData = {}
	namesAsIds = evegate.namesToIds(checkBylastChars)
	
	for name, id in namesAsIds.items():
		deeperData[name] = {"id": id, "need_check": False, "corpids": evegate.getCorpidsForCharId(id)}
	
	corpIds = set()
	for name in namesAsIds.keys():
		for number in deeperData[name]["corpids"]:
			corpIds.add(number)
	
	corpIdName = evegate.idsToNames(corpIds)
	for name, nameData in deeperData.items():
		nameData["corpnames"] = [corpIdName[id] for id in nameData["corpids"]]
		for corpName in nameData["corpnames"]:
			if corpName not in evegate.NPC_CORPS:
				nameData["need_check"] = True
				nameData["corp_to_check"] = corpName
				break
	
	corpsToCheck = set([nameData["corp_to_check"] for nameData in deeperData.values() if nameData["need_check"] == True])
	corpsResult = {}
	baseUrl = "http://kos.cva-eve.org/api/?c=json&type=unit&q="
	
	for corp in corpsToCheck:
		quotedName = urllib.quote_plus(corp)
		targetUrl = "".join((baseUrl, quotedName))

		try:
			request = urllib2.urlopen(targetUrl)
		except URLError as e:
			print "Error on corp KOS check request" + e.reason

		kosData = json.loads(request.read())
		kosResult = False

		for result in kosData["results"]:
			if result["kos"] == True:
				kosResult = True
			elif "alliance" in result and result["alliance"]["kos"] == True:
				  kosResult = True
		corpsResult[corp] = kosResult
	
	for charName, nameData in deeperData.items():
		if not nameData["need_check"]:
			data[charName] = {"kos": UNKNOWN}
		if nameData["need_check"] and corpsResult[nameData["corp_to_check"]] == True:
			data[charName] = {"kos": RED_BY_LAST}
		else:
			data[charName] = {"kos": UNKNOWN}
	
	return data


def resultToText(results, onlyKos=False):

	groups = {}
	paragraphs = []
	
	for charName, resultData in results.items():
		state = resultData["kos"]
		if state not in groups:
			groups[state] = set()
		groups[state].add(charName)
		
	if KOS in groups:
		paragraphs.append(KOS + u": " +  u", ".join(groups[KOS]))
	if RED_BY_LAST in groups:
		paragraphs.append(RED_BY_LAST + u": " + u", ".join(groups[RED_BY_LAST]))
	if UNKNOWN in groups:
		paragraphs.append(UNKNOWN + u": " + ", ".join(groups[UNKNOWN]))
	if NOT_KOS in groups and not onlyKos:
		paragraphs.append(NOT_KOS + u": " + ", ".join(groups[NOT_KOS]))
		
	return u"\n\n".join(paragraphs)
