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

soundAvailable = False

try:
    import pygame
    soundAvailable = True
    pygame.mixer.init()
except ImportError:
    pass
    
from vi.resources import resourcePath

SOUNDS = {"alarm": "178032__zimbot__redalert-klaxon-sttos-recreated.wav",
          "beep": "178031__zimbot__transporterstartbeep0-sttos-recreated.wav",
          "request": "178028__zimbot__bosun-whistle-sttos-recreated.wav"
         }

soundCache = {}
soundActive = True
soundVolume = 0   # hast o be a float beween 0 and 1!

def setSoundVolume(value):
    _soundVolume = value
    for sound in soundCache.values():
        sound.setVolume(value)
    

def playSound(name="alarm"):
    if soundAvailable and soundActive:
        if name not in SOUNDS:
            raise ValueError("Sound '{0}' is not available".format(name))
        if name not in soundCache:
            path = resourcePath("vi/ui/res/{0}".format(SOUNDS[name]))
            soundCache[name] = pygame.mixer.Sound(path)
        # soundcache[name].set_volume(sound_volume)
        soundCache[name].play()
