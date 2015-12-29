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

import datetime
import json
import urllib
import urllib2

from PyQt4.QtGui import QImage, QPixmap
from bs4 import BeautifulSoup

from vi.version import VERSION
from vi.cache.cache import Cache

ERROR = -1
NOT_EXISTS = 0
EXISTS = 1
USERAGENT = "VINTEL/{version} (+http://drachenjaeger.eu/vintel/vintel.html)".format(version=VERSION)


def charnameToId(name):
	""" Uses the EVE API to convert a charname to his ID
	"""
	try:
		url = "https://api.eveonline.com/eve/CharacterID.xml.aspx"
		data = urllib.urlencode({"names": name})
		request = urllib2.urlopen(url=url, data=data)
		content = request.read()
		soup = BeautifulSoup(content, 'html.parser')
		rowSet = soup.select("rowset")[0]
		for row in rowSet.select("row"):
			if row["name"] == name:
				return int(row["characterid"])

	except Exception as e:
		print("Exception turning charname to id via API: {0}".format(str(e)))
		# fallback! if there is a problem with the API, we use evegate
		baseUrl = "https://gate.eveonline.com/Profile/"
		qcharname = urllib2.quote(name)
		url = baseUrl + qcharname
		content = urllib2.urlopen(url).read()
		soup = BeautifulSoup(content, 'html.parser')
		img = soup.select("#imgActiveCharacter")
		imageUrl = soup.select("#imgActiveCharacter")[0]["src"]
		return imageUrl[imageUrl.rfind("/") + 1:imageUrl.rfind("_")]


def namesToIds(names):
	""" Uses the EVE API to convert a list of names to ids_to_names
		names: list of names
		returns a dict: key=name, value=id
	"""
	if len(names) == 0:
		return {}
	data = {}
	apiCheckNames = set()
	cache = Cache()

	# do we have allready something in the cache?
	for name in names:
		cacheKey = "_".join(("id", "name", name))
		id = cache.getFromCache(cacheKey)
		if id:
			data[name] = id
		else:
			apiCheckNames.add(name)

	# not in cache? asking the EVE API
	if len(apiCheckNames) > 0:
		url = "https://api.eveonline.com/eve/CharacterID.xml.aspx"
		requestData = urllib.urlencode({"names": u",".join(apiCheckNames)})
		request = urllib2.urlopen(url=url, data=requestData)
		content = request.read()
		soup = BeautifulSoup(content, 'html.parser')
		rowSet = soup.select("rowset")[0]
		for row in rowSet.select("row"):
			data[row["name"]] = row["characterid"]
		# writing the cache
		for name in apiCheckNames:
			cacheKey = "_".join(("id", "name", name))
			cache.putIntoCache(cacheKey, data[name], 60 * 60 * 24 * 365)
	return data


def idsToNames(ids):
	""" Returns the names for ids
		ids = iterable list of ids
		returns a dict key = id, value = name
	"""
	data = {}
	if len(ids) == 0:
		return data
	apiCheckIds = set()
	cache = Cache()

	# something allready in the cache?
	for id in ids:
		cacheKey = u"_".join(("name", "id", unicode(id)))
		name = cache.getFromCache(cacheKey)
		if name:
			data[id] = name
		else:
			apiCheckIds.add(id)

	try:
		# call the EVE-Api for those entries we didn't have in the cache
		url = "https://api.eveonline.com/eve/CharacterName.xml.aspx"
		if len(apiCheckIds) > 0:
			requestData = urllib.urlencode({"ids": ",".join(apiCheckIds)})
			request = urllib2.urlopen(url=url, data=requestData)
			content = request.read()
			soup = BeautifulSoup(content, 'html.parser')
			rowSet = soup.select("rowset")[0]
			for row in rowSet.select("row"):
				data[row["characterid"]] = row["name"]
			# and writing into cache
			for id in apiCheckIds:
				cacheKey = u"_".join(("name", "id", unicode(id)))
				cache.putIntoCache(cacheKey, data[id], 60 * 60 * 24 * 365)
	except Exception as e:
		print "Exception during idsToNames: ", str(e)

	return data


def getAvatarForPlayer(charname):
	""" Downlaoding th eavatar for a player/character
		charname = name of the character
		returns None if something gone wrong
	"""
	avatar = None
	try:
		charId = charnameToId(charname)
		if charId:
			imageUrl = "http://image.eveonline.com/Character/{id}_{size}.jpg"
			avatar = urllib2.urlopen(imageUrl.format(id=charId, size=32)).read()
	except Exception as e:
		print "Exception during getAvatarForPlayer:", str(e)
		avatar = None
	return avatar


def checkPlayername(charname):
	""" Checking on evegate for an exiting playername
		returns 1 if exists, 0 if not and -1 if an error occured
	"""
	baseUrl = "https://gate.eveonline.com/Profile/"
	qcharname = urllib2.quote(charname)
	url = baseUrl + qcharname
	retvalue = -1
	try:
		urllib2.urlopen(url)
		retvalue = 1
	except urllib2.HTTPError as e:
		if ("404") in str(e):
			retvalue = 0
	except Exception as e:
		print "Exception on checkPlayername: ", str(e)
	return retvalue


def currentEveTime():
	""" returns the current eve-time as a datetime.datetime
	"""
	return datetime.datetime.utcnow()


def eveEpoch():
	""" returns the seconds since epoch in eve timezone
	"""
	return time.mktime(datetime.datetime.utcnow().timetuple())


def getCharinfoForCharId(charId):
	cacheKey = u"_".join(("playerinfo_id_", unicode(charId)))
	cache = Cache()
	soup = cache.getFromCache(cacheKey)
	if soup is not None:
		soup = BeautifulSoup(soup, 'html.parser')
	else:
		charId = int(charId)
		url = "https://api.eveonline.com/eve/CharacterInfo.xml.aspx"
		data = urllib.urlencode({"characterID": charId})
		content = urllib2.urlopen(url=url, data=data).read()
		soup = BeautifulSoup(content, 'html.parser')
		cacheUntil = datetime.datetime.strptime(soup.select("cacheduntil")[0].text, "%Y-%m-%d %H:%M:%S")
		diff = cacheUntil - currentEveTime()
		cache.putIntoCache(cacheKey, str(soup), diff.seconds)
	return soup


def getCorpidsForCharId(charId):
	""" returns a list with the ids if the corporation history of a charId
	"""
	data = []
	soup = getCharinfoForCharId(charId)
	for rowSet in soup.select("rowset"):
		if rowSet["name"] == "employmentHistory":
			for row in rowSet.select("row"):
				data.append(row["corporationid"])
	return data


def getSystemStatistics():
	""" Reads the informations for all solarsystems from the EVE API
		Reads a dict like:
			systemid: "jumps", "shipkills", "factionkills", "podkills"
	"""
	data = {}
	cache = Cache()
	# first the data for the jumps
	cacheKey = "jumpstatistic"
	jumpdata = cache.getFromCache(cacheKey)

	if jumpdata is None:
		jumpdata = {}
		url = "https://api.eveonline.com/map/Jumps.xml.aspx"
		content = urllib2.urlopen(url=url).read()
		soup = BeautifulSoup(content, 'html.parser')

		for result in soup.select("result"):
			for row in result.select("row"):
				jumpdata[int(row["solarsystemid"])] = int(row["shipjumps"])

		cacheUntil = datetime.datetime.strptime(soup.select("cacheduntil")[0].text, "%Y-%m-%d %H:%M:%S")
		diff = cacheUntil - currentEveTime()
		cache.putIntoCache(cacheKey, json.dumps(jumpdata), diff.seconds)
	else:
		jumpdata = json.loads(jumpdata)

	# now the further data
	cacheKey = "systemstatistic"
	systemdata = cache.getFromCache(cacheKey)

	if systemdata is None:
		systemdata = {}
		url = "https://api.eveonline.com/map/Kills.xml.aspx"
		content = urllib2.urlopen(url=url).read()
		soup = BeautifulSoup(content, 'html.parser')

		for result in soup.select("result"):
			for row in result.select("row"):
				systemdata[int(row["solarsystemid"])] = {"ship": int(row["shipkills"]), "faction": int(row["factionkills"]), "pod": int(row["podkills"])}

		cacheUntil = datetime.datetime.strptime(soup.select("cacheduntil")[0].text, "%Y-%m-%d %H:%M:%S")
		diff = cacheUntil - currentEveTime()
		cache.putIntoCache(cacheKey, json.dumps(systemdata), diff.seconds)
	else:
		systemdata = json.loads(systemdata)

	# we collected all data (or loaded them from cache) - now zip it together
	for i, v in jumpdata.items():
		i = int(i)
		if i not in data:
			data[i] = {"shipkills": 0, "factionkills": 0, "podkills": 0}
		data[i]["jumps"] = v
	for i, v in systemdata.items():
		i = int(i)
		if i not in data:
			data[i] = {"jumps": 0}
		data[i]["shipkills"] = v["ship"] if "ship" in v else 0
		data[i]["factionkills"] = v["faction"] if "faction" in v else 0
		data[i]["podkills"] = v["pod"] if "pod" in v else 0
	return data


def secondsTillDowntime():
	""" return the seconds till the next downtime"""
	now = currentEveTime()
	target = now
	if now.hour > 11:
		target = target + datetime.timedelta(1)
	target = datetime.datetime(target.year, target.month, target.day, 11, 0, 0, 0)
	delta = target - now
	return delta.seconds


SHIPNAMES = (u'ABADDON', u'ABSOLUTION', u'AEON', u'AMARR SHUTTLE', u'ANATHEMA', u'ANSHAR', u'APOCALYPSE',
			 u'APOCALYPSE IMPERIAL ISSUE', u'APOCALYPSE NAVY ISSUE', u'APOTHEOSIS', u'ARAZU', u'ARBITRATOR', u'ARCHON',
			 u'ARES', u'ARK', u'ARMAGEDDON', u'ARMAGEDDON IMPERIAL ISSUE', u'ASHIMMU', u'ASTARTE', u'ATRON', u'AUGOROR',
			 u'AUGOROR NAVY ISSUE', u'AVATAR', u'BADGER', u'BADGER MARK II', u'BANTAM', u'BASILISK', u'BELLICOSE',
			 u'BESTOWER', u'BHAALGORN', u'BLACKBIRD', u'BREACHER', u'BROADSWORD', u'BRUTIX', u'BURST', u'BUSTARD',
			 u'BUZZARD', u'CONCORD ARMY BATTLESHIP', u'CONCORD ARMY CRUISER', u'CONCORD ARMY FRIGATE',
			 u'CONCORD POLICE BATTLESHIP', u'CONCORD POLICE CRUISER', u'CONCORD POLICE FRIGATE',
			 u'CONCORD SWAT BATTLESHIP', u'CONCORD SWAT CRUISER', u'CONCORD SWAT FRIGATE',
			 u'CONCORD SPECIAL OPS BATTLESHIP', u'CONCORD SPECIAL OPS CRUISER', u'CONCORD SPECIAL OPS FRIGATE',
			 u'CALDARI NAVY HOOKBILL', u'CALDARI SHUTTLE', u'CARACAL', u'CARACAL NAVY ISSUE', u'CATALYST', u'CELESTIS',
			 u'CERBERUS', u'CHARON', u'CHEETAH', u'CHIMERA', u'CLAW', u'CLAYMORE', u'COERCER', u'CONDOR', u'CORMORANT',
			 u'COVETOR', u'CRANE', u'CROW', u'CRUCIFIER', u'CRUOR', u'CRUSADER', u'CURSE', u'CYCLONE', u'CYNABAL',
			 u'DAMNATION', u'DAREDEVIL', u'DEIMOS', u'DEVOTER', u'DOMINIX', u'DRAKE', u'DRAMIEL', u'EAGLE', u'EIDOLON',
			 u'ENIGMA', u'ENYO', u'EOS', u'EREBUS', u'ERIS', u'EXECUTIONER', u'EXEQUROR', u'EXEQUROR NAVY ISSUE',
			 u'FALCON', u'FEDERATION NAVY COMET', u'FENRIR', u'FEROX', u'FLYCATCHER', u'GALLENTE SHUTTLE', u'GILA',
			 u'GOLD MAGNATE', u'GOLEM', u'GRIFFIN', u'GUARDIAN', u'HARBINGER', u'HARPY', u'HAWK', u'HEL', u'HELIOS',
			 u'HERETIC', u'HERON', u'HOARDER', u'HOUND', u'HUGINN', u'HULK', u'HURRICANE', u'HYENA', u'HYPERION',
			 u'IBIS', u'IMICUS', u'IMPAIROR', u'IMPEL', u'IMPERIAL NAVY SLICER', u'INCURSUS', u'ISHKUR', u'ISHTAR',
			 u'ITERON', u'ITERON MARK II', u'ITERON MARK III', u'ITERON MARK IV', u'ITERON MARK V', u'JAGUAR', u'KERES',
			 u'KESTREL', u'KITSUNE', u'KRONOS', u'LACHESIS', u'LEVIATHAN', u'MACHARIEL', u'MACKINAW', u'MAELSTROM',
			 u'MAGNATE', u'MALEDICTION', u'MALLER', u'MAMMOTH', u'MANTICORE', u'MASTODON', u'MAULUS', u'MEGATHRON',
			 u'MEGATHRON FEDERATE ISSUE', u'MEGATHRON NAVY ISSUE', u'MERLIN', u'MINMATAR SHUTTLE', u'MOA', u'MOROS',
			 u'MUNINN', u'MYRMIDON', u'NAGLFAR', u'NAVITAS', u'NEMESIS', u'NIDHOGGUR', u'NIGHTHAWK', u'NIGHTMARE',
			 u'NOMAD', u'NYX', u'OBELISK', u'OCCATOR', u'OMEN', u'OMEN NAVY ISSUE', u'ONEIROS', u'ONYX',
			 u'OPUX DRAGOON YACHT', u'OPUX LUXURY YACHT', u'ORACLE', u'ORCA', u'OSPREY', u'OSPREY NAVY ISSUE',
			 u'PALADIN', u'PANTHER', u'PHANTASM', u'PHANTOM', u'PHOBOS', u'PHOENIX', u'PILGRIM', u'POLARIS CENTURION',
			 u'POLARIS INSPECTOR', u'POLARIS LEGATUS', u'PROBE', u'PROCURER', u'PROPHECY', u'PRORATOR', u'PROVIDENCE',
			 u'PROWLER', u'PUNISHER', u'PURIFIER', u'RAGNAROK', u'RAPIER', u'RAPTOR', u'RATTLESNAKE', u'RAVEN',
			 u'RAVEN NAVY ISSUE', u'RAVEN STATE ISSUE', u'REAPER', u'REDEEMER', u'REPUBLIC FLEET FIRETAIL',
			 u'RETRIBUTION', u'RETRIEVER', u'REVELATION', u'RHEA', u'RIFTER', u'ROKH', u'ROOK', u'RORQUAL', u'RUPTURE',
			 u'SABRE', u'SACRILEGE', u'SCIMITAR', u'SCORPION', u'SCYTHE', u'SCYTHE FLEET ISSUE', u'SENTINEL', u'SIGIL',
			 u'SILVER MAGNATE', u'SIN', u'SKIFF', u'SLASHER', u'SLEIPNIR', u'SPECTER', u'STABBER',
			 u'STABBER FLEET ISSUE', u'STILETTO', u'SUCCUBUS', u'TARANIS', u'TEMPEST', u'TEMPEST FLEET ISSUE',
			 u'TEMPEST TRIBAL ISSUE', u'THANATOS', u'THORAX', u'THRASHER', u'TORMENTOR', u'TRISTAN', u'TYPHOON',
			 u'VAGABOND', u'VARGUR', u'VELATOR', u'VENGEANCE', u'VEXOR', u'VEXOR NAVY ISSUE', u'VIATOR', u'VIGIL',
			 u'VIGILANT', u'VINDICATOR', u'VISITANT', u'VULTURE', u'WIDOW', u'WOLF', u'WORM', u'WRAITH', u'WREATHE',
			 u'WYVERN', u'ZEALOT', u'CAPSULE',)
SHIPNAMES = sorted(SHIPNAMES, key=lambda x: len(x), reverse=True)

NPC_CORPS = (u'Republic Justice Department', u'House of Records', u'24th Imperial Crusade', u'Template:NPC corporation',
			 u'Khanid Works', u'Caldari Steel', u'School of Applied Knowledge', u'NOH Recruitment Center',
			 u'Sarum Family', u'Impro', u'Guristas', u'Carthum Conglomerate', u'Secure Commerce Commission',
			 u'Amarr Trade Registry', u'Anonymous', u'Federal Defence Union', u'Federal Freight', u'Ardishapur Family',
			 u'Thukker Mix', u'Sebiestor tribe', u'Core Complexion Inc.', u'Federal Navy Academy', u'Dominations',
			 u'Ishukone Watch', u'Kaalakiota Corporation', u'Nurtura', u'Center for Advanced Studies', u'CONCORD',
			 u'Ammatar Consulate', u'HZO Refinery', u'Joint Harvesting', u'Caldari Funds Unlimited', u'Propel Dynamics',
			 u'Caldari Navy', u'Amarr Navy', u'Amarr Certified News', u'Serpentis Corporation', u'CreoDron',
			 u'Society of Conscious Thought', u'Shapeset', u'Kor-Azor Family', u'Khanid Transport',
			 u'Imperial Chancellor', u'Rapid Assembly', u'Khanid Innovation', u'Combined Harvest',
			 u'Peace and Order Unit', u'The Leisure Group', u'CBD Sell Division', u'DED', u'Six Kin Development',
			 u'Zero-G Research Firm', u'Defiants', u'Noble Appliances', u'Guristas Production', u'Intaki Space Police',
			 u'Spacelane Patrol', u'User talk:ISD Crystal Carbonide', u'Caldari Provisions', u'Brutor tribe',
			 u'True Power', u'Nefantar Miner Association', u'Garoun Investment Bank', u'FedMart', u'Prosper',
			 u'Inherent Implants', u'Chief Executive Panel', u'Top Down', u'Federation Customs',
			 u'Lai Dai Protection Service', u'Roden Shipyards', u'Wiyrkomi Peace Corps', u'Allotek Industries',
			 u'Minedrill', u'Court Chamberlain', u'Intaki Syndicate', u'Caldari Constructions',
			 u'State and Region Bank', u'Amarr Civil Service', u'Pend Insurance', u'Zainou', u'Material Institute',
			 u'Republic Fleet', u'Intaki Bank', u'Hyasyoda Corporation', u'Nugoeihuvi Corporation', u'Modern Finances',
			 u'Bank of Luminaire', u'Ministry of War', u'Genolution', u'Pator Tech School', u'Hedion University',
			 u'Kador Family', u'Ducia Foundry', u'Prompt Delivery', u'Trust Partners', u'Material Acquisition',
			 u'Jovian Directorate', u'DUST 514 NPC Corporations', u'Ministry of Assessment', u'Expert Distribution',
			 u'Ishukone Corporation', u'Caldari Business Tribunal', u'The Scope', u'Eifyr and Co.',
			 u'Jovian directorate', u'Lai Dai Corporation', u'Chemal Tech', u'CBD Corporation', u'Internal Security',
			 u'Salvation Angels', u'TransStellar Shipping', u'InterBus', u'Outer Ring Excavations',
			 u'Tribal Liberation Force', u'Impetus', u'Intaki Commerce', u'University of Caille', u'Home Guard',
			 u'The Draconis Family', u'The Sanctuary', u'Republic University', u'Federal Intelligence Office',
			 u'Egonics Inc.', u'Native Freshfood', u'Republic Security Services', u'Wiyrkomi Corporation',
			 u'Sukuuvestaa Corporation', u'Vherokior tribe', u'Republic Parliament', u'Ytiri', u'Mercantile Club',
			 u'Civic Court', u'Imperial Academy', u'Tash-Murkon Family', u'Viziam', u'Ammatar Fleet',
			 u'Urban Management', u'Royal Amarr Institute', u'Echelon Entertainment', u'Archangels',
			 u'Poteque Pharmaceuticals', u'Imperial Armaments', u'Academy of Aggressive Behaviour',
			 u'Duvolle Laboratories', u'Ministry of Internal Order', u'Quafe Company', u'Serpentis Inquest',
			 u'True Creations', u'Science and Trade Institute', u'Further Foodstuffs', u'Poksu Mineral Group',
			 u'Astral Mining Inc.', u'Krusual tribe', u'Blood Raiders', u'Amarr Constructions', u'Federation Navy',
			 u'Inner Circle', u'State War Academy', u'Zoar and Sons', u'Boundless Creation', u'Guardian Angels',
			 u'Food Relief', u'Royal Khanid Navy', u'Imperial Shipment', u'Perkone', u'Federal Administration',
			 u'Emperor Family', u'Inner Zone Shipping', u'Theology Council', u'Aliastra', u'Republic Military School',
			 u'Freedom Extension', u'Sisters of EVE', u'President', u'Expert Housing', u'Deep Core Mining Inc.',
			 u'Senate', u"Mordu's Legion", u'State Protectorate', u'Jove Navy', u'X-Sense', u'Corporate Police Force',
			 u'Minmatar Mining Corporation', u'Supreme Court')
