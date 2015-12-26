###########################################################################
#  delstyles - Delete styles from a evemap                                #
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

def readSvg(path):
    if not os.path.exists(path):
        errout("ERROR: {0} does not exist!".format(path))
        sys.exit(2)
    soup = None
    with open(path) as f:
        soup = BeautifulSoup(f.read())
    return soup

def deleteStylesFromSvg(soup):
    def recursiveRemoveStyle(element):
        for subElement in element.select("*"):
            if "style" in subElement.attrs:
                del subElement.attrs["style"]
            if subElement.name == "text":
                subElement.attrs["text-anchor"] = "middle"
            recursiveRemoveStyle(subElement)
    recursiveRemoveStyle(soup)
    return soup


def main():
    if len(sys.argv) <> 2:
        errout("Wrong number of arguments. Please use it like this:")
        errout("{0} mapfile".format(sys.argv[0]))
        errout("Where mapfile is the path to a evemap SVG")
        errout("The modiefied data is written to stdout")
        sys.exit(1)
    path = sys.argv[1]
    source = read_svg(path)
    withoutStyle = deleteStylesFromSvg(source)
    result = withoutStyle.body.next.prettify().encode("utf-8")
    print(result)


def errout(*objs):
    print(*objs, file=sys.stderr)


if __name__ == "__main__":
    main()