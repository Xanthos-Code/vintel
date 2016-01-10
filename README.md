[](http://github.com/Xanthos-Eve/vintel/src/vi/ui/res/logo.png)

# Welcome To Vintel

Visual intel chat analysis, planning and notification application for [EVE Online](http://www.eveonline.com). Gathers status through in-game intelligence channels on all known hostiles and presents all the data on a [dotlan](http://evemaps.dotlan.net/map/Cache#npc24) generated regional map.

Vintel is written with Python 2.7, using PyQt4 for its application presentation layer.

## Features

 - Platforms supported: Mac, Windows and Linux.
 - A pilot may be KOS-checked right from in-game chat channels.
 - Quick batch KOS-checking of the Local system when foregrounding Vintel.
 - Notifications and alarms can be spoken using text-to-speech on select platforms (currently only OS X).
 - "TheCitadel", "North Provi Intel", and "North Catch Intel" are merged to one chat stream. You can add or remove channels via a menu option.
 - An interactive map of Providence / Catch is provided. Systems on the map display real-time intel data as reported through intel channels.
 - Systems on the map display different color backgrounds as their alarms age, with text indicating how long ago the specific system was reported.
Background start at red when a system is reported and lighten in at the following minute intervals: 4min, 10min, 15m, 25min.
 - Systems reported clear display on the map with a green background for 10 minutes.
 - Clicking on a specific system will display all messages bound on that system. From there one can can set a system clear and alarmed.
 - Clicking on a system in the intel channel causes it to be highlighted on the map with a blue background for 10 seconds.
 - The system where your character is currently located is highlighted on the map with an violet background (works only after first use of a gate).
 - Alarms can be set so that task-bar notifications are displayed if an intel report calls out a system within a specified number of jumps. This can be configured from the task-bar icon.
 - The main window can be set up to remain "always on top" and be displayed with a specified level of transparency.
 - Shipnames in the intel chat are marked blue.

Usage
-----

 - Manually checking one (or some) pilot(s) from an intel channel:
 Type xxx in any chat and drag and drop the pilots names after this. (e.g., xxx Xanthos)
 - Checking the whole local system:
The option must be activated via the Vintel app menu: File > Activate local KOS-Check.
To use this feature: click on a pilot in the local pilot list and then type the shortcuts for select-all, and copy. Next switch to the VIntel app and back to Eve. KOS checking of these pilots will continue in the background.


KOS Results
-----------
"KOS" status values reported by Vintel

 - **? (Unknown)**: the pilot is not known by the KOS-checker and there are no hostile corporations in her employment history.
 - **Not KOS**: the pilot is known as NOT KOS by the KOS-checker.
 - **KOS**: the pilot is known as KOS by the KOS-checker.
 - **RED by last**: the last non-NPC-Corp the pilot was employed is KOS.

Running Vintel from Source
--------------------------

This is for Mac and Windows users; Linux users can install the programs
and tools mostly using distribution's software management.

To run or build from the source you need the following packages:
> - Python 2.7.x
https://www.python.org/downloads/
Vintel is not compatible with Python 3!
> - PyQt4x
http://www.riverbankcomputing.com/software/pyqt/download
Please use the PyQt Binary Package for Py2.7
Vintel is not compatible with PyQt5!
> - BeautifulSoup 4
https://pypi.python.org/pypi/beautifulsoup4
> - Pyglet 1.2.4 (for python 2.7)
https://bitbucket.org/pyglet/pyglet/wiki/Download
pyglet is used to play the sound: If it is not available the
sound option will be disabled.

Building the Vintel Standalone Package 
-------

The standalone is created using pyinstaller. All media files and the .spec-file with the configuration for pyinstaller are included in the source repo. Pyinstaller can be found here: https://github.com/pyinstaller/pyinstaller/wiki.

FAQ
---

**License?**
Vintel is licensed under the GPLv3.

**Vintel does not show any chat. What can I do?**
Vintel only analyzes your chatlogs. It looks for them in USER\EVE\logs\chatlogs and DOCUMENTS\EVE\logs\chatlogs. In EVE you have to enable the logging. Go to the settings, use the register "chat" and activate "log chat to file".

**A litte bit to big for such a little tool.**
The .exe ships with the complete environment and needed libs. You are free to use the sourcecode instead.

**Will you bring the GUI to the ingame-browser (igb)?**
There are no plans to bring the GUI to HTML/JS. Sorry. But you can set the vintel-window always on top (look at the menu).

**EXE? I'm using Linux!**
Great! Same here. VINTEL works great on Linux. Use the sourcecode and install following dependencies: Python 2.7.x, pyQt 4.x, BeautifulSoup 4 and pygame. Should be available through your software repositories.

**I'm using a Mac. Does Vintel run?**
Yes it does! Install all the requirements and follow the instructions above.
 
**What permissions Vintel needs?**
It reads your EVE Chatlogs
It creates and writes to PathToYourChatlogs/../../vintel/.
It needs to connect the internet (dotlan.evemaps.net, eveonline.com, cva-eve.org, eve gate).

**Vintel calls home?**
Yes it does. If you don't want it, use a firewall to forbid it.
VINTEL looks for a new version at startup and loads dynamic infomations from home. It will run without this connection.

**VINTEL does not find my chatlogs. What can I do?**
The program looks for your logs on some default pathes. If those pathes not exist, VINTEL will fail with an error at startup. You can set this path on your own by giving it to VINTEL at startup. For this you have to start it on the command line and call the program with the path to the logs. Examples:
vintel-0.46.exe "d:\strange\path\EVE\logs\chatlogs"
python vintel.py " /home/user/myverypecialpath/EVE/logs/chatlogs"

**Vintel does not start! What can I do?**
Please try to delete VINTEL's Cache. It is located in the EVE-directory where the chatlogs are in. If your chatlogs are in \Documents\EVE\logs\chatlogs Vintel writes the cachte to \Documents\EVE\vintel

**If I do a KOS-check an error occured, telling: "empty certificate data"**
Do not use the standalone EXE, install the environment and use the sourcecode directly.
(long version: there are missing certificats that must be provided by the environment. I found this error when running the standalone EXE on Linux using wine.
