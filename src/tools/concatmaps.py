###########################################################################
#  concatmaps - Tool to concat evemaps                                    #
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

from __future__ import print_function
import sys
import os

from bs4 import BeautifulSoup

def checkArguments(args):
    error = False
    for path in args[1:3]:
        if not os.path.exists(path):
            errout("ERROR: {0} does not exist!".format(path))
            error = True
    if error:
        sys.exit(2) 
        
def concat(firstFile, secondFile):
    firstSvg = loadSvg(firstFile)
    secondSvg = loadSvg(secondFile)
    symbols = []
    jumps = []
    sysuses = []
    for def_element in secondSvg.select("defs"):
        for symbol in def_element.select("symbol"):
            symbols.append(symbol)
    for jumpgroup in secondSvg.select("#jumps"):
        for jump in jumpgroup.select("line"):
            jump["x1"] = float(jump["x1"]) + 3000
            jump["x2"] = float(jump["x2"]) + 3000
            jumps.append(jump)
    for sysgroup in secondSvg.select("#sysuse"):
        for sysuse in sysgroup.select("use"):
            sysuse["x"] = float(sysuse["x"]) + 3000
            sysuses.append(sysuse)
    defElement = firstSvg.select("defs")[0]
    for symbol in symbols:
        defElement.append(symbol)
    jumpsElement = firstSvg.select("#jumps")[0]
    for jump in jumps:
        jumpsElement.append(jump)
    systemUseElement = firstSvg.select("#sysuse")[0]
    for systemUse in systemUses:
        systemUseElement.append(systemUse)
    return firstSvg
    
        
def loadSvg(path):
    content = None
    with open(path) as f:
        content = f.read()
    return BeautifulSoup(content)

def main():
    if len(sys.argv) != 3:
        errout("Sorry, wrong number of arguments. Use this this way:")
        errout("{0} firstmap secondmap".format(sys.argv[0]))
        errout("All argumens are pathes to files")
        errout("The new map is written to stdout")
        sys.exit(1)
    checkArguments(sys.argv)
    newSvg = concat(sys.argv[1], sys.argv[2])
    result = newSvg.body.next.prettify().encode("utf-8")
    print(result)
    
def errout(*objs):
    print(*objs, file=sys.stderr)

if __name__ == "__main__":
    main()