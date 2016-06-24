
<p align="center">
  <img align="middle" src="src/vi/ui/res/logo.png">
</p>
# Welcome To Vintel

Visual intel chat analysis, planning and notification application for [EVE Online](http://www.eveonline.com). Gathers status through in-game intelligence channels on all known hostiles and presents all the data on a [dotlan](http://evemaps.dotlan.net/map/Cache#npc24) generated regional map. The map is annotated in real-time as players report intel in monitored chat channels.

Vintel is written with Python 2.7, using PyQt4 for the application presentation layer, BeautifulSoup4 for SVG parsing, and Pyglet for audio playback.

### News
_The current release version of Vintel is **1.1.3** and [can be found here](https://github.com/Xanthos-Eve/vintel/releases/tag/1.1.3). Both Mac and Windows distributions are now available for download with this release._

Release 1.2.0 development is beginning, and the focus is on simplfying some UI in the app. Mostly around system information display and settings management. Keep up on progress, add ideas, bugs or suggestions [here](https://github.com/Xanthos-Eve/vintel/issues).

## Screenshot

![](https://github.com/Xanthos-Eve/vintel/blob/master/src/docs/screenshot.png)

## Features

 - Platforms supported: Mac, Windows and Linux.
 - A pilot may be KOS-checked right from in-game chat channels.
 - Quick batch KOS-checking of the Local system when foregrounding Vintel.
 - Notifications and alarms can be spoken using text-to-speech on select platforms (currently only OS X).
 - "TheCitadel", "North Provi Intel", and "North Catch Intel" are merged to one chat stream. You can add or remove channels via a menu option.
 - An interactive map of Providence / Catch is provided. Systems on the map display real-time intel data as reported through intel channels.
 - Systems on the map display different color backgrounds as their alarms age, with text indicating how long ago the specific system was reported. Background color becomes red when a system is reported and lightens (red->orange->yellow->white) in the following intervals: 4min, 10min, 15min, and 25min.
 - Systems reported clear display on the map with a green background for 10 minutes.
 - Clicking on a specific system will display all messages bound on that system. From there one can can set a system alarm, set the sytems clear or set it as the current system for one or more of your characters.
 - Clicking on a system in the intel channel causes it to be highlighted on the map with a blue background for 10 seconds.
 - The system where your character is currently located is highlighted on the map with an violet background automatically whenever a characater changes systems.
 - Alarms can be set so that task-bar notifications are displayed when an intel report calls out a system within a specified number of jumps from your character(s). This can be configured from the task-bar icon.
 - The main window can be set up to remain "always on top" and be displayed with a specified level of transparency.
 - Ship names in the intel chat are marked blue.

## Usage

 - Manually checking pilot(s) using an EVE client chat channel:
 Type xxx in any chat channel and drag and drop the pilots names after this. (e.g., xxx [Xanthos](http://image.eveonline.com/Character/183452271_256.jpg)). Vintel recognizes this as a request and checks the pilots listed.
 - Checking all pilots in the local system:
This option must first be activated by checking the Vintel app menu: Menu > Auto KOS-Check Clipboard.
To use this feature: click on a pilot in the local pilot list and then type the shortcuts for select-all and copy-selection. This places the pilots in local on your clipboard. Next switch to the Vintel app momentarily and back to Eve. KOS checking of these pilots will continue in the background.


## KOS Results

"KOS" status values reported by Vintel

 - **KOS**: the pilot is known as KOS to the alliance and has been marked as such in the KOS-checker system.
 - **RED by last**: the last player (non-NPC) corp in the pilot's employment history is KOS.
 - **Not KOS**: the pilot is known as NOT KOS to the alliance and has been marked as such in the KOS-checker system.
 - **? (Unknown)**: the pilot is not known by the KOS-checker system and there are no hostile corporations in her employment history.


## Running Vintel from Source

To run or build from the source you need the following packages installed on your machine. Most, if not all, can be installed from the command line using package management software such as "pip". Mac and Linux both come with pip installed, Windows users may need to install [cygwin](https://www.cygwin.com) to get pip. Of course all the requirements also have downoad links.

The packages required are:
- Python 2.7.x
https://www.python.org/downloads/
Vintel is not compatible with Python 3!
- PyQt4x
http://www.riverbankcomputing.com/software/pyqt/download
Please use the PyQt Binary Package for Py2.7
Vintel is not compatible with PyQt5!
- BeautifulSoup 4
https://pypi.python.org/pypi/beautifulsoup4
- Pyglet 1.2.4 (for python 2.7)
https://bitbucket.org/pyglet/pyglet/wiki/Download
pyglet is used to play the sound – If it is not available the sound option will be disabled.
- Requests 2
https://pypi.python.org/pypi/requests
- Six for python 3 compatibility https://pypi.python.org/pypi/six

## Building the Vintel Standalone Package

 - The standalone is created using pyinstaller. All media files and the .spec-file with the configuration for pyinstaller are included in the source repo. Pyinstaller can be found here: https://github.com/pyinstaller/pyinstaller/wiki.
 - Edit the .spec file to match your src path in the "a = Analysis" section and execute "pyinstaller vintel.spec vintel.py". If everything went correctly you should get a dist folder that contains the standalone executable.

## FAQ

**License?**

Vintel is licensed under the [GPLv3](http://www.gnu.org/licenses/gpl-3.0.html).

**Vintel does not play sounds - is there a remedy for this?**

The most likely cause of this is that pyglet is not installed.

**A litte bit to big for such a little tool.**

The .exe ships with the complete environment and needed libs. You could save some space using the the source code instead.

**Will you bring the GUI to the EVE in-game browser?**

There are no plans to bring the GUI to HTML/JS. But you can set the Vintel window always on top with a menu option.

**What platforms are supported?**

Vintel runs on Mac (OS X), Windows and Linux. Mac and Windows standalone packages are provided with each release. Linux users are advised to install all the requirements listed above then download and run from source.

**What file system permissions does Vintel need?**

- It reads your EVE chatlogs
- It creates and writes to **path-to-your-chatlogs**/../../vintel/.
- It needs to connect the internet (dotlan.evemaps.net, eveonline.com, cva-eve.org, and eve gate).

**Vintel calls home?**

Yes it does. If you don't want to this, use a firewall to forbid it.
Vintel looks for a new version at startup and loads dynamic infomation (i.e., jump bridge routes) from home. It will run without this connection but some functionality will be limited.

**Vintel does not find my chatlogs or is not showing changes to chat when it should. What can I do?**

Vintel looks for your chat logs in ~\EVE\logs\chatlogs and ~\DOCUMENTS\EVE\logs\chatlogs. Logging must be enabled in the EVE client options. You can set this path on your own by giving it to Vintel at startup. For this you have to start it on the command line and call the program with the path to the logs.

Examples:

`win> vintel-1.0.exe "d:\strange\path\EVE\logs\chatlogs"`

    – or –

`linux and mac> python vintel.py "/home/user/myverypecialpath/EVE/logs/chatlogs"`

**Vintel does not start! What can I do?**

Please try to delete Vintel's Cache. It is located in the EVE-directory where the chatlogs are in. If your chatlogs are in \Documents\EVE\logs\chatlogs Vintel writes the cachte to \Documents\EVE\vintel

**Vintel takes many seconds to start up; what are some of the causes and what can I do about it?**

Vintel asks the operating system to notifiy when a change has been made to the ChatLogs directory - this will happen when a new log is created or an existing one is updated. In response to this notification, Vintel examines all of the files in the directory to analysze the changes. If you have a lot of chat logs this can make Vintel slow to scan for file changes. Try perodically moving all the chatlogs out of the ChatLogs directory (zip them up and save them somewhere else if you think you may need them some day).

**How can I resolve the "empty certificate data" error?**

Do not use the standalone EXE, install the environment and use the sourcecode directly. There are missing certificates that must be provided by the environment. This error was discovered when running the standalone EXE on Linux using wine.

**Vintel is misbehaving and I dont know why - how can I easily help diagnose problems with Vintel**

Vintel writes its own set of logs to the \Documents\EVE\vintel\vintel directory. A new log is created as the old one fills up to its maximum size setting. Each entry inside the log file is time-stamped. These logs are emitted in real-time so you can watch the changes to the file as you use the app.

**I love Vintel - how can I help?**

If you are technically inclined and have a solid grasp of Python, [contact the project maintainer via email](mailto:xanthos.eve@gmail.com) to see how you can best help out.

**I'm not a coder, how can I help?**

Your feedback is needed! Use the program for a while, then come back [here and create issues](https://github.com/Xanthos-Eve/vintel/issues). Record anything you think about Vintel - bugs, frustrations, and ideas to make Vintel better.
