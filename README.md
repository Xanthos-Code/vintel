
<p align="center">
  <img align="middle" src="src/vi/ui/res/logo.png">
</p>
# Welcome To Vintel

Visual intel chat analysis, planning and notification application for [EVE Online](http://www.eveonline.com). Gathers status through in-game intelligence channels on all known hostiles and presents all the data on a [dotlan](http://evemaps.dotlan.net/map/Cache#npc24) generated regional map.

Vintel is written with Python 2.7, using PyQt4 for the application presentation layer, BeautifulSoup4 for html parsing, and Pyglet for audio playback.

### News
_The current release version of Vintel is **1.1.2** and [can be found here](https://github.com/Xanthos-Eve/vintel/releases/tag/1.1.2)._

Release 1.2.0 development is beginning - keep up on progress, add ideas, bugs or suggestions [here](https://github.com/Xanthos-Eve/vintel/issues).

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

This is for Mac and Windows users; Linux users can install the programs and tools mostly using the distribution's software management tools.

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
pyglet is used to play the sound – If it is not available the sound option will be disabled.

## Building the Vintel Standalone Package

 - Windows - The standalone is created using pyinstaller. All media files and the .spec-file with the configuration for pyinstaller are included in the source repo. Pyinstaller can be found here: https://github.com/pyinstaller/pyinstaller/wiki.
   - Edit the .spec file to match your src path in the "a = Analysis" section and execute "pyinstaller vintel.spec vintel.py". If everything went correctly you should get a dist folder that contains the standalone executable.
 - Mac - The simplest method is to download all the requirements for running Vintel and use Automator to create a launchable application. Create a new automator Application. Add a Run Shell Script action and configure it as follows: ![Automator setup](https://raw.github.com/Xanthos-Eve/vintel/master/src/docs/automator-setup.jpg)

## FAQ

**License?**

Vintel is licensed under the [GPLv3](http://www.gnu.org/licenses/gpl-3.0.html).

**Vintel does not play sounds - is there a remedy for this?**

The most likely cause of this is that pyglet is not installed.

**Vintel does not show any chat. What can I do?**

Vintel looks for your chat logs in ~\EVE\logs\chatlogs and ~\DOCUMENTS\EVE\logs\chatlogs. Logging must be enabled in the EVE client options. Go to the settings, use the register "chat" and activate "log chat to file".

**A litte bit to big for such a little tool.**

The .exe ships with the complete environment and needed libs. You could save some space using the the source code instead.

**Will you bring the GUI to the EVE in-game browser?**

There are no plans to bring the GUI to HTML/JS. But you can set the Vintel window always on top with a menu option.

**I'm using Linux, will Vintel work for me?**

Vintel works great on Linux! Install the dependencies listed above and the source repository and run from there. The dependencies are available through your software repositories.

**I'm using Mac (OSX), will Vintel work for me?**

Vintel works great on Mac! Install the dependencies listed above and the source repository and run from there or use Automator to wrap the command line into an app.

**What file system permissions does Vintel need?**

It reads your EVE chatlogs
It creates and writes to PathToYourChatlogs/../../vintel/.
It needs to connect the internet (dotlan.evemaps.net, eveonline.com, cva-eve.org, and eve gate).

**Vintel calls home?**

Yes it does. If you don't want to this, use a firewall to forbid it.
Vintel looks for a new version at startup and loads dynamic infomation (i.e., jump bridge routes) from home. It will run without this connection but some functionality will be limited.

**Vintel does not find my chatlogs. What can I do?**

The program looks for your logs on some default pathes. If those paths do not exist, Vintel will fail with an error at startup. You can set this path on your own by giving it to Vintel at startup. For this you have to start it on the command line and call the program with the path to the logs.

Examples:

`win> vintel-1.0.exe "d:\strange\path\EVE\logs\chatlogs"`

    – or –

`mac> python vintel.py "/home/user/myverypecialpath/EVE/logs/chatlogs"`

**Vintel does not start! What can I do?**

Please try to delete Vintel's Cache. It is located in the EVE-directory where the chatlogs are in. If your chatlogs are in \Documents\EVE\logs\chatlogs Vintel writes the cachte to \Documents\EVE\vintel

**How can I resolve the "empty certificate data" error?**

Do not use the standalone EXE, install the environment and use the sourcecode directly. There are missing certificates that must be provided by the environment. This error was discovered when running the standalone EXE on Linux using wine.

**I love Vintel - how can I help?**

If you are technically inclined and have a solid grasp of Python, [contact the project maintainer via email](mailto:xanthos.eve@gmail.com) to see how you can best help out.

**I'm not a coder, how can I help?**

Your feedback is needed! Use the program for a while, then come back [here and create issues](https://github.com/Xanthos-Eve/vintel/issues). Record anything you think about Vintel - bugs, frustrations, and ideas to make Vintel better.
Encourage continued development with motivational contributions of EVE ISK. Send donations in-game to the project maintainer [Xanthos](http://image.eveonline.com/Character/183452271_256.jpg).
