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

"""
you can add external databaseupdates to database updates.
they should be a tuple like (query, condition)
query     = the query to run on the database connection
condition = if TRUE the query qull be executed
"""
databaseUpdates = []

def updateDatabase(oldVersion, con):
    """ Changes for the database-structure should be added here,
        or added to added_database_updates
        con = the database connection
    """
    queries = []
    if oldVersion < 1:
        queries += ["CREATE TABLE version (version INT)",
                    "INSERT INTO version (version) VALUES (1)"]
    if oldVersion < 2:
        queries += ["""CREATE TABLE playernames
                       (charname VARCHAR PRIMARY KEY, status INT, modified INT)
                    """,
                    """CREATE TABLE avatars
                       (charname VARCHAR PRIMARY KEY, data  BLOB, modified INT)
                    """,
                    "UPDATE version SET version = 2"]
    if oldVersion < 3:
        queries += ["""CREATE TABLE cache
                       (key VARCHAR PRIMARY KEY, data BLOB, modified INT,
                        maxage INT)""",
                    "UPDATE version SET version = 3"]
    for query in queries:
        con.execute(query)
    for update in databaseUpdates:
        if update[1]:
            con.execute(update[0])
    con.commit()
