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

import logging
import requests

from requests.exceptions import RequestException
from vi import evegate

UNKNOWN = "No Result"
NOT_KOS = 'Not Kos'
KOS = "KOS"
RED_BY_LAST = "Red by last"
CVA_KOS_URL = "http://kos.cva-eve.org/api/"


def check(parts):
    data = {}
    checkBylastChars = []
    namesAsIds = {}
    names = [name.strip() for name in parts]

    try:
        kosData = requests.get(CVA_KOS_URL, params = {'c': 'json', 'type': 'multi', 'q': ','.join(names)}).json()
    except RequestException as e:
        kosData = None
        logging.error("Error on pilot KOS check request %s", str(e))

    for char in kosData["results"]:
        charname = char["label"]
        corpname = char["corp"]["label"]
        names.remove(charname)

        if char["kos"] or char["corp"]["kos"] or char["corp"]["alliance"]["kos"]:
            data[charname] = {"kos": KOS}
        elif corpname not in evegate.NPC_CORPS:
            data[charname] = {"kos": NOT_KOS}
        else:
            if char not in checkBylastChars:
                checkBylastChars.append(charname)

    # Names still in the list are not showing as KOS, so consider their last player corporation
    for name in names:
        checkBylastChars.append(name)

    # Corporation check
    corpCheckData = {}
    try:
        namesAsIds = evegate.namesToIds(checkBylastChars)
    except Exception:
        pass

    # Prune any pairs that have no id
    for key, value in namesAsIds.items():
        if int(value) == 0:
            del namesAsIds[key]

    # Anything left - do the corp check and fill in kos status
    if namesAsIds:
        for name, id in namesAsIds.items():
            corpCheckData[name] = {"id": id, "need_check": False, "corpids": evegate.getCorpidsForCharId(id)}

        corpIds = set()
        for name in namesAsIds.keys():
            for number in corpCheckData[name]["corpids"]:
                corpIds.add(number)

        corpIdName = evegate.idsToNames(corpIds)
        for name, nameData in corpCheckData.items():
            nameData["corpnames"] = [corpIdName[id] for id in nameData["corpids"]]
            for corpname in nameData["corpnames"]:
                if corpname not in evegate.NPC_CORPS:
                    nameData["need_check"] = True
                    nameData["corp_to_check"] = corpname
                    break

        corpsToCheck = set([nameData["corp_to_check"] for nameData in corpCheckData.values() if nameData["need_check"] == True])
        corpsResult = {}

        for corp in corpsToCheck:
            try:
                kosData = requests.get(CVA_KOS_URL, params = { 'c': 'json', 'type': 'unit', 'q': corp }).json()
            except RequestException as e:
                logging.error("Error on corp KOS check request: %s", str(e))

            kosResult = False

            for result in kosData["results"]:
                if result["kos"] == True:
                    kosResult = True
                elif "alliance" in result and result["alliance"]["kos"] == True:
                    kosResult = True
            corpsResult[corp] = kosResult

        for charname, nameData in corpCheckData.items():
            if not nameData["need_check"]:
                data[charname] = {"kos": UNKNOWN}
            if nameData["need_check"] and corpsResult[nameData["corp_to_check"]] == True:
                data[charname] = {"kos": RED_BY_LAST}
            else:
                data[charname] = {"kos": UNKNOWN}

    return data


def resultToText(results, onlyKos=False):
    groups = {}
    paragraphs = []

    for charname, resultData in results.items():
        state = resultData["kos"]
        if state not in groups:
            groups[state] = set()
        groups[state].add(charname)

    if KOS in groups:
        paragraphs.append(KOS + u": " + u", ".join(groups[KOS]))
    if RED_BY_LAST in groups:
        paragraphs.append(RED_BY_LAST + u": " + u", ".join(groups[RED_BY_LAST]))
    if UNKNOWN in groups:
        paragraphs.append(UNKNOWN + u": " + ", ".join(groups[UNKNOWN]))
    if NOT_KOS in groups and not onlyKos:
        paragraphs.append(NOT_KOS + u": " + ", ".join(groups[NOT_KOS]))

    return u"\n\n".join(paragraphs)
