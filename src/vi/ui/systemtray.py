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

import time

from PyQt4 import QtGui, QtCore, Qt

from vi.resources import resourcePath
from vi import states
from vi.sound import SoundThread

class TrayContextMenu(QtGui.QMenu):

	instances = set()

	def __init__(self, trayicon):
		""" trayicon = the object with the methods to call
		"""
		QtGui.QMenu.__init__(self)
		TrayContextMenu.instances.add(self)
		self.trayicon = trayicon
		self._buildMenu()


	def _buildMenu(self):
		self.framelessCheck = QtGui.QAction("Frameless Window", self, checkable=True)
		self.connect(self.framelessCheck, QtCore.SIGNAL("triggered()"), self.trayicon.changeFrameless)
		self.addAction(self.framelessCheck)
		self.addSeparator()
		self.requestCheck = QtGui.QAction("Show status request notifications", self, checkable=True)
		self.requestCheck.setChecked(True)
		self.addAction(self.requestCheck)
		self.connect(self.requestCheck, QtCore.SIGNAL("triggered()"), self.trayicon.switchRequest)
		self.alarmCheck = QtGui.QAction("Show alarm notifications", self, checkable=True)
		self.alarmCheck.setChecked(True)
		self.connect(self.alarmCheck, QtCore.SIGNAL("triggered()"), self.trayicon.switchAlarm)
		self.addAction(self.alarmCheck)
		distanceMenu = self.addMenu("Alarm Distance")
		self.distanceGroup = QtGui.QActionGroup(self)
		for i in xrange(0, 6):
			action = QtGui.QAction("{0} Jumps".format(i), None, checkable=True)
			if i == 0:
				action.setChecked(True)
			action.alarmDistance = i
			self.connect(action, QtCore.SIGNAL("triggered()"), self.changeAlarmDistance)
			self.distanceGroup.addAction(action)
			distanceMenu.addAction(action)
		self.addMenu(distanceMenu)
		self.addSeparator()
		self.quitAction = QtGui.QAction("Quit", self)
		self.connect(self.quitAction, Qt.SIGNAL("triggered()"), self.trayicon.quit)
		self.addAction(self.quitAction)

	def changeAlarmDistance(self):
		for action in self.distanceGroup.actions():
			if action.isChecked():
				self.trayicon.alarmDistance = action.alarmDistance
				self.trayicon.changeAlarmDistance()


class TrayIcon(QtGui.QSystemTrayIcon):

	# Min seconds between two notifications
	MIN_WAIT_NOTIFICATION = 15

	def __init__(self, app):
		self.icon = QtGui.QIcon(resourcePath("vi/ui/res/logo_small.png"))
		QtGui.QSystemTrayIcon.__init__(self, self.icon, app)
		self.setToolTip("Your Vintel-Information-Service! :)")
		self.lastNotifications = {}
		self.setContextMenu(TrayContextMenu(self))
		self.showAlarm = True
		self.showRequest = True
		self.alarmDistance = 0

	def changeAlarmDistance(self):
		distance = self.alarmDistance
		self.emit(Qt.SIGNAL("alarm_distance"), distance)

	def changeFrameless(self):
		self.emit(Qt.SIGNAL("change_frameless"))

	@property
	def distanceGroup(self):
		return self.contextMenu().distanceGroup

	def quit(self):
		self.emit(Qt.SIGNAL("quit"))

	def switchAlarm(self):
		newValue = not self.showAlarm
		for cm in TrayContextMenu.instances:
			cm.alarmCheck.setChecked(newValue)
		self.showAlarm = newValue

	def switchRequest(self):
		newValue = not self.showRequest
		for cm in TrayContextMenu.instances:
			cm.requestCheck.setChecked(newValue)
		self.showRequest = newValue

	def showNotification(self, message, system, char, distance):
		if message is None:
			return
		room = message.room
		title = None
		text = None
		icon = None
		text = ""
		if (message.status == states.ALARM and self.showAlarm and self.lastNotifications.get(states.ALARM, 0) < time.time() - self.MIN_WAIT_NOTIFICATION):
			title = "ALARM!"
			text = (u"{system} alarmed in {room}. Pilot {distance} jumps out: {char}\nText: {messageText}")
			icon = 2
			messageText = message.plainText
			self.lastNotifications[states.ALARM] = time.time()
			SoundThread.sharedInstance.playSound("alarm", text)
		elif (message.status == states.REQUEST and self.showRequest and self.lastNotifications.get(states.REQUEST, 0) < time.time() - self.MIN_WAIT_NOTIFICATION):
			title = "Status request"
			icon = 1
			text = (u"Someone is requesting status of {system} in {room}.")
			self.lastNotifications[states.REQUEST] = time.time()
			SoundThread.sharedInstance.playSound("request", text)
		if not (title is None or text is None or icon):
			text = text.format(**locals())
			self.showMessage(title, text, icon)
