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

import subprocess, sys, os

from vi.resources import resourcePath

soundCache = {}
soundVolume = 25   # Must be an integer beween 0 and 100!
soundAvailable = False
soundActive = True
useSpokenNotifications = True
useDarwinSound = False

SOUNDS = {"alarm": "178032__zimbot__redalert-klaxon-sttos-recreated.wav",
          "kos": "178031__zimbot__transporterstartbeep0-sttos-recreated.wav",
          "request": "178028__zimbot__bosun-whistle-sttos-recreated.wav"}

try:
    import pygame
    soundAvailable = True
    pygame.mixer.init()
except ImportError:
    if sys.platform.startswith("darwin"):
        useDarwinSound = True;
        soundAvailable = True
    else:
        useSpokenNotifications = False
        soundVolume = 0.0
    

def useSpokenNotifications(value):
    _useSpokenNotifications = value

def setSoundVolume(value):
    """ Accepts and stores a number between 0 and 100.
    """
    if value < 0:
        value = 0
    elif value > 100:
        value = 100
    _soundVolume = value
    for sound in soundCache.values():
        # Convert to a value between 0 and 1
        sound.setVolume(float(value)  / 100.0)
    

def playSound(name="alarm", message=None):
    if soundAvailable and soundActive:
        if name not in SOUNDS:
            raise ValueError("Sound '{0}' is not available".format(name))

    # Workaround for OSX, since pygame wants *exactly* 2.7; and py is at 2.71
    if useDarwinSound:
        path = resourcePath("vi/ui/res/{0}".format(SOUNDS[name]))
        if useSpokenNotifications and message:
            os.system("say [[volm {0}]] {1}".format(float(soundVolume) / 100.0, message))
        else:
            subprocess.call(["afplay -v {0} {1}".format(float(soundVolume) / 100.0, path)], shell=True)
    else:
        if name not in soundCache and not useDarwinSound:
            path = resourcePath("vi/ui/res/{0}".format(SOUNDS[name]))
            soundCache[name] = pygame.mixer.Sound(path)
        soundCache[name].play()
