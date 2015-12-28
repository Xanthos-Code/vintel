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

import datetime
import os
import sys
import time
import urllib2
import webbrowser

from PyQt4 import Qt, QtGui, uic, QtCore
from PyQt4.QtGui import QImage, QPixmap, QMessageBox
from PyQt4.QtWebKit import QWebPage
from PyQt4.QtCore import QPoint

from vi.ui.systemtray import TrayContextMenu
from vi.ui.threads import AvatarFindThread, KOSCheckerThread
from vi.ui.threads import MapStatisticsThread
import vi.version
from vi import chatparser, dotlan, filewatcher, koschecker
from vi import drachenjaeger, evegate
from vi.cache.cache import Cache
from vi import states
from vi.sound import Sound

from vi.resources import resourcePath

VERSION = vi.version.VERSION
DEBUG = False


class MainWindow(QtGui.QMainWindow):
	def __init__(self, pathToLogs, trayIcon):
		""" systems = list of system-objects created by dotlan.py
		"""
		QtGui.QMainWindow.__init__(self)
		uic.loadUi(resourcePath('vi/ui/MainWindow.ui'), self)
		self.setWindowTitle("Xintel " + VERSION)
		self.setWindowIcon(QtGui.QIcon(resourcePath("vi/ui/res/logo_small.png")))
		self.pathToLogs = pathToLogs
		self.trayIcon = trayIcon
		self.trayIcon.activated.connect(self.systemTrayActivated)
		self.cache = Cache()
		self.sound = Sound()

		# Set up cached items
		#
		# Maps
		regionName = self.cache.getFromCache("region_name")
		svg = None

		if not regionName:
			regionName = "Providence"
		try:
			with open(resourcePath("vi/ui/res/mapdata/{0}.svg".format(regionName))) as svgFile:
				svg = svgFile.read()
		except Exception as e:
			pass

		try:
			self.dotlan = dotlan.Map(regionName, svg)
		except dotlan.DotlanException as e:
			QtGui.QMessageBox.critical(None, "Error getting map", unicode(e), "Quit")
			sys.exit(1)

		if self.dotlan.outdatedCacheError:
			e = self.dotlan.outdatedCacheError
			diagText = "Something went wrong getting map data. To proceed I use the data I " \
					   "have in my cache. This could be outdated.\nIf this problem " \
					   "is permanent, there might be a change in the dotlan data " \
					   "and Xintel must be modified. Check for a newer version " \
					   "and inform the maintainer.\n\nWhat went wrong: {0} {1}".format(type(e), unicode(e))
			print str(e)
			QtGui.QMessageBox.warning(None, "Using map from my cache", diagText, "OK")

		# Add a contextual menu to the map
		self.map.contextmenu = TrayContextMenu(self.trayIcon)

		def mapContextMenuEvent(event):
			self.map.contextmenu.exec_(self.mapToGlobal(QPoint(event.x(), event.y())))

		self.map.contextMenuEvent = mapContextMenuEvent
		self.map.connect(self.map, Qt.SIGNAL("linkClicked(const QUrl&)"), self.mapLinkClicked)

		# Load the jumpbridges
		jumpbridgeUrl = self.cache.getFromCache("jumpbridge_url")
		self.setJumpbridges(jumpbridgeUrl)

		# Load my toon names and intel rooms
		self.knownPlayerNames = self.cache.getFromCache("known_player_names")
		if self.knownPlayerNames:
			self.knownPlayerNames = set(self.knownPlayerNames.split(","))
		else:
			self.knownPlayerNames = set()
		roomnames = self.cache.getFromCache("room_names")
		if roomnames:
			roomnames = roomnames.split(",")
		else:
			roomnames = (u"TheCitadel", u"North Provi Intel", u"North Catch Intel")
			self.cache.putIntoCache("room_names", u",".join(roomnames), 60 * 60 * 24 * 365 * 5)

		# Wire up state and UI connections
		self.isFrameless = None  # we need this because 2 places to change
		self.oldClipboardContent = ""
		self.alarmDistance = 0
		self.lastStatisticsUdpdate = 0

		self.initMapPosition = None  # we read this after first rendering
		self.setMapContent(self.dotlan.svg)
		self.systems = self.dotlan.systems
		self.chatEntries = []
		self.avatarFindThread = AvatarFindThread()
		self.connect(self.avatarFindThread, QtCore.SIGNAL("avatar_update"), self.updateAvatarOnChatEntry)
		self.avatarFindThread.start()
		self.clipboard = QtGui.QApplication.clipboard()
		self.clipboard.clear(mode=self.clipboard.Clipboard)
		self.frameButton.setVisible(False)
		self.opacityGroup = QtGui.QActionGroup(self.menu)

		self.connect(self.clipboard, Qt.SIGNAL("changed(QClipboard::Mode)"), self.clipboardChanged)
		self.connect(self.zoomInButton, Qt.SIGNAL("clicked()"), self.zoomMapIn)
		self.connect(self.zoomOutButton, Qt.SIGNAL("clicked()"), self.zoomMapOut)
		self.connect(self.statisticsButton, Qt.SIGNAL("clicked()"), self.dotlan.changeStatisticsVisibility)
		self.connect(self.chatLargeButton, Qt.SIGNAL("clicked()"), self.chatLarger)
		self.connect(self.chatSmallButton, Qt.SIGNAL("clicked()"), self.chatSmaller)
		self.connect(self.infoAction, Qt.SIGNAL("triggered()"), self.showInfo)
		self.connect(self.showChatAvatarsAction, Qt.SIGNAL("triggered()"), self.changeShowAvatars)
		self.connect(self.alwaysOnTopAction, Qt.SIGNAL("triggered()"), self.changeAlwaysOnTop)
		self.connect(self.jumpbridgeDataAction, Qt.SIGNAL("triggered()"), self.changeJumpbridgeView)
		self.connect(self.chooseChatRoomsAction, Qt.SIGNAL("triggered()"), self.showChatroomChooser)
		self.connect(self.chooseRegionAction, Qt.SIGNAL("triggered()"), self.showRegionChooser)
		self.connect(self.showChatAction, Qt.SIGNAL("triggered()"), self.changeChatVisibility)
		self.connect(self.soundSetupAction, Qt.SIGNAL("triggered()"), self.showSoundSetup)
		self.connect(self.activateSoundAction, Qt.SIGNAL("triggered()"), self.changeSound)
		self.connect(self.useSpokenNotificationsAction, Qt.SIGNAL("triggered()"), self.changeUseSpokenNotifications)
		self.connect(self.floatingOverviewAction, Qt.SIGNAL("triggered()"), self.showFloatingOverview)
		self.connect(self.trayIcon, Qt.SIGNAL("alarm_distance"), self.changeAlarmDistance)
		self.connect(self.framelessWindowAction, Qt.SIGNAL("triggered()"), self.changeFrameless)
		self.connect(self.trayIcon, Qt.SIGNAL("change_frameless"), self.changeFrameless)
		self.connect(self.frameButton, Qt.SIGNAL("clicked()"), self.changeFrameless)
		self.connect(self.quitAction, Qt.SIGNAL("triggered()"), self.close)
		self.connect(self.trayIcon, Qt.SIGNAL("quit"), self.close)
		self.connect(self.jumpbridgeDataAction, Qt.SIGNAL("triggered()"), self.showJumbridgeChooser)

		# Fill in opacity values and connections
		for i in (100, 80, 60, 40, 20):
			action = QtGui.QAction("Opacity {0}%".format(i), None, checkable=True)
			if i == 100:
				action.setChecked(True)
			action.opacity = i / 100.0
			self.connect(action, QtCore.SIGNAL("triggered()"), self.changeOpacity)
			self.opacityGroup.addAction(action)
			self.menuTransparency.addAction(action)

		# Recall cached user settings
		try:
			self.cache.recallAndApplySettings(self, "settings")
		except Exception as e:
			print str(e)
			self.trayIcon.showMessage("Settings error", "Something went wrong loading saved state:\n {0}".format(str(e)), 1)

		# Disable the sound UI if sound is not available
		if not self.sound.soundAvailable:
			self.changeSound(disable=True)
		else:
			self.changeSound()

		# Set up threads and their connections
		self.kosRequestThread = KOSCheckerThread()
		self.connect(self.kosRequestThread, Qt.SIGNAL("kos_result"), self.showKosResult)
		self.kosRequestThread.start()
		self.filewatcherThread = filewatcher.FileWatcher(self.pathToLogs, 60 * 60 * 24)
		self.connect(self.filewatcherThread, QtCore.SIGNAL("file_change"), self.logFileChanged)
		self.filewatcherThread.start()
		self.mapTimer = QtCore.QTimer(self)
		self.connect(self.mapTimer, QtCore.SIGNAL("timeout()"), self.updateMap)
		self.mapTimer.start(1000)
		self.chatparser = chatparser.ChatParser(self.pathToLogs, roomnames, self.systems)
		versionCheckThread = drachenjaeger.NotifyNewVersionThread()
		versionCheckThread.connect(versionCheckThread, Qt.SIGNAL("newer_version"), self.notifyNewerVersion)
		versionCheckThread.run()

	def closeEvent(self, event):
		""" writing the cache before closing the window
		"""
		# known playernames
		if self.knownPlayerNames:
			value = ",".join(self.knownPlayerNames)
			self.cache.putIntoCache("known_player_names", value, 60 * 60 * 24 * 365)
		# program state to cache (to read it on next startup)
		settings = ((None, "restoreGeometry", str(self.saveGeometry())),
					(None, "restoreState", str(self.saveState())),
					("splitter", "restoreGeometry", str(self.splitter.saveGeometry())),
					("splitter", "restoreState", str(self.splitter.saveState())),
					("map", "setZoomFactor", self.map.zoomFactor()),
					(None, "changeOpacity", self.opacityGroup.checkedAction().opacity),
					(None, "changeAlwaysOnTop", self.alwaysOnTopAction.isChecked()),
					(None, "changeShowAvatars", self.showChatAvatarsAction.isChecked()),
					(None, "changeAlarmDistance", self.alarmDistance),
					(None, "changeSound", self.activateSoundAction.isChecked()),
					(None, "changeChatVisibility", self.showChatAction.isChecked()),
					(None, "setInitMapPosition", (self.map.page().mainFrame().scrollPosition().x(), self.map.page().mainFrame().scrollPosition().y())),
					(None, "setSoundVolume", self.sound.soundVolume),
					(None, "changeFrameless", self.framelessWindowAction.isChecked()),
					(None, "changeUseSpokenNotifications", self.useSpokenNotificationsAction.isChecked()),
					(None, "changeClipboard", self.kosClipboardActiveAction.isChecked()),
					(None, "changeFloatingOverview", self.floatingOverviewAction.isChecked()),
					(None, "alreadyShowedSoundWarning", self.alreadyShowedSoundWarning))
		self.cache.putIntoCache("settings", str(settings), 60 * 60 * 24 * 365)
		event.accept()


	def notifyNewerVersion(self, newestVersion):
		self.trayIcon.showMessage("Newer Version", ("A newer Version of VINTEL is available.\nFind the URL in the info!"), 1)


	def changeFloatingOverview(self, newValue=None):
		pass

	def changeChatVisibility(self, newValue=None):
		if newValue is None:
			newValue = self.showChatAction.isChecked()
		self.chatbox.setVisible(newValue)


	def changeClipboard(self, newValue=None):
		if newValue is None:
			newValue = not self.kosClipboardActiveAction.isChecked()
		self.kosClipboardActiveAction.setChecked(newValue)
		self.sound.setUseSpokenNotifications(newValue)


	def changeUseSpokenNotifications(self, newValue=None):
		if newValue is None:
			newValue = self.useSpokenNotificationsAction.isChecked()
		self.useSpokenNotificationsAction.setChecked(newValue)
		self.sound.setUseSpokenNotifications(newValue)


	def changeOpacity(self, newValue=None):
		if newValue is not None:
			for action in self.opacityGroup.actions():
				if action.opacity == newValue:
					action.setChecked(True)
		action = self.opacityGroup.checkedAction()
		self.setWindowOpacity(action.opacity)


	def changeSound(self, newValue=None, disable=False):
		if disable:
			self.activateSoundAction.setChecked(False)
			self.activateSoundAction.setEnabled(False)
			self.soundSetupAction.setEnabled(False)
			self.soundButton.setEnabled(False)
			if not self.alreadyShowedSoundWarning:
				self.alreadyShowedSoundWarning = True
				QtGui.QMessageBox.warning(None, "Sound disabled", "I can't find the lib 'pygame' which I use to play sounds, ""so I have to disable the soundsystem.\nIf you want sound, please install the 'pygame' library.", "OK")
		else:
			if newValue is None:
				newValue = self.activateSoundAction.isChecked()
			self.sound.soundActive = newValue


	def changeAlwaysOnTop(self, newValue=None):
		if newValue is None:
			newValue = self.alwaysOnTopAction.isChecked()
		self.hide()
		self.alwaysOnTopAction.setChecked(newValue)
		if newValue:
			self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
		else:
			self.setWindowFlags(self.windowFlags() & (~QtCore.Qt.WindowStaysOnTopHint))
		self.show()


	def changeFrameless(self, newValue=None):
		self.hide()
		if newValue is None:
			newValue = self.framelessWindowAction.isChecked()

		if newValue:
			self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
			self.changeAlwaysOnTop(True)
		else:
			self.setWindowFlags(self.windowFlags() & (~QtCore.Qt.FramelessWindowHint))
		self.menubar.setVisible(not newValue)
		self.frameButton.setVisible(newValue)

		for cm in TrayContextMenu.instances:
			cm.framelessCheck.setChecked(newValue)
		self.show()


	def changeShowAvatars(self, newValue=None):
		if newValue is None:
			newValue = self.showChatAvatarsAction.isChecked()
		self.showChatAvatarsAction.setChecked(newValue)
		ChatEntry.SHOW_AVATAR = newValue
		for entry in self.chatEntries:
			entry.avatarLabel.setVisible(newValue)


	def chatSmaller(self):
		newSize = ChatEntry.TEXT_SIZE - 1
		ChatEntry.TEXT_SIZE = newSize
		for entry in self.chatEntries:
			entry.changeFontSize(newSize)


	def chatLarger(self):
		newSize = ChatEntry.TEXT_SIZE + 1
		ChatEntry.TEXT_SIZE = newSize
		for entry in self.chatEntries:
			entry.changeFontSize(newSize)


	def changeAlarmDistance(self, distance):
		self.alarmDistance = distance
		for cm in TrayContextMenu.instances:
			for action in cm.distanceGroup.actions():
				if action.alarmDistance == distance:
					action.setChecked(True)
		self.trayIcon.alarmDistance = distance


	def changeJumpbridgeView(self):
		self.dotlan.changeJumpbrigdeVisibility()
		self.updateMap()


	def clipboardChanged(self, mode):
		if mode == 0 and self.kosClipboardActiveAction.isChecked():
			content = unicode(self.clipboard.text())
			# Limit redundant kos checks
			if content != self.oldClipboardContent:
				parts = content.split("\n")
				for part in parts:
					if part in self.knownPlayerNames:
						self.trayIcon.setIcon(QtGui.QIcon(resourcePath("vi/ui/res/logo_small_green.png")))
						self.kosRequestThread.addRequest(parts, "clipboard", True)
						break
				self.oldClipboardContent = content


	def mapLinkClicked(self, url):
		systemName = unicode(url.path().split("/")[-1]).upper()
		system = self.systems[str(systemName)]
		sc = SystemChat(self, SystemChat.SYSTEM, system, self.chatEntries, self.knownPlayerNames)
		sc.connect(self, Qt.SIGNAL("chat_message_added"), sc.addChatEntry)
		sc.connect(self, Qt.SIGNAL("avatar_loaded"), sc.newAvatarAvailable)
		sc.connect(sc, Qt.SIGNAL("location_set"), self.setLocation)
		sc.show()


	def markSystemOnMap(self, systemname):
		self.systems[unicode(systemname)].mark()
		self.updateMap()


	def setLocation(self, char, newSystem):
		for system in self.systems.values():
			system.removeLocatedCharacter(char)
		if not newSystem == "?" and newSystem in self.systems:
			self.systems[newSystem].addLocatedCharacter(char)
			self.setMapContent(self.dotlan.svg)

	def setMapContent(self, content):
		if self.initMapPosition is None:
			scrollposition = self.map.page().mainFrame().scrollPosition()
		else:
			scrollposition = self.initMapPosition
			self.initMapPosition = None
		self.map.setContent(content)
		self.map.page().mainFrame().setScrollPosition(scrollposition)
		self.map.page().setLinkDelegationPolicy(QWebPage.DelegateAllLinks)


	def setInitMapPosition(self, xy):
		self.initMapPosition = QPoint(xy[0], xy[1])


	def showChatroomChooser(self):
		chooser = ChatroomsChooser(self)
		chooser.connect(chooser, Qt.SIGNAL("rooms_changed"), self.changedRoomnames)
		chooser.show()


	def showJumbridgeChooser(self):
		url = self.cache.getFromCache("jumpbridge_url")
		chooser = JumpbridgeChooser(self, url)
		chooser.connect(chooser, Qt.SIGNAL("set_jumpbridge_url"), self.setJumpbridges)
		chooser.show()


	def setSoundVolume(self, value):
		self.sound.setSoundVolume(value)


	def setJumpbridges(self, url):
		if url is None:
			url = ""
		try:
			data = []
			if url != "":
				content = urllib2.urlopen(url).read()
				for line in content.split("\n"):
					parts = line.strip().split()
					if len(parts) == 3:
						data.append(parts)
			else:
				data = drachenjaeger.getJumpbridgeData(self.dotlan.region.lower())
			self.dotlan.setJumpbridges(data)
			self.cache.putIntoCache("jumpbridge_url", url, 60 * 60 * 24 * 365 * 8)
		except Exception as e:
			QtGui.QMessageBox.warning(None, "Loading jumpbridges failed!", "Error: {0}".format(unicode(e)), "OK")


	def showRegionChooser(self):
		chooser = RegionChooser(self)
		chooser.show()


	def addMessageToIntelChat(self, message):
		scrollToBottom = False
		if (self.chatListWidget.verticalScrollBar().value() == self.chatListWidget.verticalScrollBar().maximum()):
			scrollToBottom = True
		entry = ChatEntry(message)
		listWidgetItem = QtGui.QListWidgetItem(self.chatListWidget)
		listWidgetItem.setSizeHint(entry.sizeHint())
		self.chatListWidget.addItem(listWidgetItem)
		self.chatListWidget.setItemWidget(listWidgetItem, entry)
		self.avatarFindThread.addChatEntry(entry)
		self.chatEntries.append(entry)
		self.connect(entry, Qt.SIGNAL("mark_system"), self.markSystemOnMap)
		self.emit(Qt.SIGNAL("chat_message_added"), entry)
		if scrollToBottom:
			self.chatListWidget.scrollToBottom()


	def showKosResult(self, state, text, requestType, hasKos):
		if hasKos:
			self.sound.playSound("kos", text)
		self.trayIcon.setIcon(QtGui.QIcon(resourcePath("vi/ui/res/logo_small.png")))
		if state == "ok":
			if requestType == "xxx":  # a xxx request out of the chat
				self.trayIcon.showMessage("Player KOS-Check", text, 1)
			elif requestType == "clipboard":  # request from clipboard-change
				if len(text) <= 0:
					text = "None KOS"
				self.trayIcon.showMessage("Your KOS-Check", text, 1)
			text = text.replace("\n\n", "<br>")
			message = chatparser.chatparser.Message("Vintel KOS-Check", text, evegate.currentEveTime(), "VINTEL", [],
													states.NOT_CHANGE, text.upper(), text)
			self.addMessageToIntelChat(message)
		elif state == "error":
			self.trayIcon.showMessage("KOS Failure", text, 3)


	def changedRoomnames(self, newRoomnames):
		self.cache.putIntoCache("room_names", u",".join(newRoomnames), 60 * 60 * 24 * 365 * 5)
		self.chatparser.rooms = newRoomnames


	def showInfo(self):
		infoDialog = QtGui.QDialog(self)
		uic.loadUi(resourcePath("vi/ui/Info.ui"), infoDialog)
		infoDialog.versionLabel.setText(u"Version: {0}".format(VERSION))
		infoDialog.logoLabel.setPixmap(QtGui.QPixmap(resourcePath("vi/ui/res/logo.png")))
		infoDialog.connect(infoDialog.closeButton, Qt.SIGNAL("clicked()"), infoDialog.accept)
		infoDialog.show()


	def showFloatingOverview(self):
		pass


	def showSoundSetup(self):
		dialog = QtGui.QDialog(self)
		uic.loadUi(resourcePath("vi/ui/SoundSetup.ui"), dialog)
		dialog.volumeSlider.setValue(self.sound.soundVolume)
		dialog.connect(dialog.volumeSlider, Qt.SIGNAL("valueChanged(int)"), self.sound.setSoundVolume)
		dialog.connect(dialog.testSoundButton, Qt.SIGNAL("clicked()"), self.sound.playSound)
		dialog.connect(dialog.closeButton, Qt.SIGNAL("clicked()"), dialog.accept)
		dialog.show()


	def systemTrayActivated(self, reason):
		if reason == QtGui.QSystemTrayIcon.Trigger:
			if self.isMinimized():
				self.showNormal()
				self.activateWindow()
			elif not self.isActiveWindow():
				self.activateWindow()
			else:
				self.showMinimized()


	def updateAvatarOnChatEntry(self, chatEntry, avatarData):
		updated = chatEntry.updateAvatar(avatarData)
		if not updated:
			self.avatarFindThread.addChatEntry(chatEntry, clearCache=True)
		else:
			self.emit(Qt.SIGNAL("avatar_loaded"), chatEntry.message.user, avatarData)


	def updateMap(self):
		def updateStatisticsOnMap(data):
			if data["result"] == "ok":
				self.dotlan.addSystemStatistics(data["statistics"])
			elif data["result"] == "error":
				text = data["text"]
				self.trayIcon.showMessage("Loading statstics failed", text, 3)

		if self.lastStatisticsUdpdate < time.time() - (5 * 60):
			self.lastStatisticsUdpdate = time.time()
			statisticsThread = MapStatisticsThread()
			self.connect(statisticsThread, Qt.SIGNAL("statistic_data_update"), updateStatisticsOnMap)
			statisticsThread.start()
		self.setMapContent(self.dotlan.svg)


	def zoomMapIn(self):
		self.map.setZoomFactor(self.map.zoomFactor() + 0.1)


	def zoomMapOut(self):
		self.map.setZoomFactor(self.map.zoomFactor() - 0.1)


	def logFileChanged(self, path):
		messages = self.chatparser.fileModified(path)
		for message in messages:
			# if players location changed
			if message.status == states.LOCATION:
				self.knownPlayerNames.add(message.user)
				self.setLocation(message.user, message.systems[0])
			# SOUND_TEST special
			elif message.status == states.SOUND_TEST and message.user in self.knownPlayerNames:
				words = message.message.split()
				if len(words) > 1:
					self.sound.playSound(words[1])
			# KOS request
			elif message.status == states.KOS_STATUS_REQUEST:
				text = message.message[4:]
				text = text.replace("  ", ",")
				parts = (name.strip() for name in text.split(","))
				self.trayIcon.setIcon(QtGui.QIcon(resourcePath("vi/ui/res/logo_small_green.png")))
				self.kosRequestThread.addRequest(parts, "xxx", False)
			# if it is a 'normal' chat message
			elif (message.user not in ("EVE-System", "EVE System") and message.status != states.IGNORE):
				self.addMessageToIntelChat(message)
				if message.systems:
					for system in message.systems:
						systemname = system.name
						self.dotlan.systems[systemname].setStatus(message.status)
						if message.status in (
						states.REQUEST, states.ALARM) and message.user not in self.knownPlayerNames:
							alarmDistance = self.alarmDistance if message.status == states.ALARM else 0
							for nsystem, data in system.getNeighbours(alarmDistance).items():
								distance = data["distance"]
								chars = nsystem.getLocatedCharacters()
								if len(chars) > 0 and message.user not in chars:
									self.trayIcon.showNotification(message, system.name, ", ".join(chars), distance)
				self.setMapContent(self.dotlan.svg)


class FloatingOverview(QtGui.QDockWidget):
	def __init__(self):
		QtGui.QDockWidget.__init__(self)
		uic.loadUi(resourcePath('vi/ui/FloatingOverview.ui'), self)


class ChatroomsChooser(QtGui.QDialog):
	def __init__(self, parent):
		QtGui.QDialog.__init__(self, parent)
		uic.loadUi(resourcePath("vi/ui/ChatroomsChooser.ui"), self)
		self.connect(self.defaultButton, Qt.SIGNAL("clicked()"), self.setDefaults)
		self.connect(self.cancelButton, Qt.SIGNAL("clicked()"), self.accept)
		self.connect(self.saveButton, Qt.SIGNAL("clicked()"), self.saveClicked)
		cache = Cache()
		roomnames = cache.getFromCache("room_names")
		if not roomnames:
			roomnames = u"TheCitadel, North Provi Intel, North Catch Intel"
		self.roomnamesField.setPlainText(roomnames)


	def saveClicked(self):
		text = unicode(self.roomnamesField.toPlainText())
		rooms = [unicode(name.strip()) for name in text.split(",")]
		self.emit(Qt.SIGNAL("rooms_changed"), rooms)
		self.accept()


	def setDefaults(self):
		self.roomnamesField.setPlainText(u"TheCitadel,North Provi Intel,North Catch Intel")


class RegionChooser(QtGui.QDialog):
	def __init__(self, parent):
		QtGui.QDialog.__init__(self, parent)
		uic.loadUi(resourcePath("vi/ui/RegionChooser.ui"), self)
		self.connect(self.defaultButton, Qt.SIGNAL("clicked()"), self.setDefaults)
		self.connect(self.cancelButton, Qt.SIGNAL("clicked()"), self.accept)
		self.connect(self.saveButton, Qt.SIGNAL("clicked()"), self.saveClicked)
		cache = Cache()
		regionName = cache.getFromCache("region_name")
		if not regionName:
			regionName = u"Providence"
		self.regionNameField.setPlainText(regionName)


	def saveClicked(self):
		text = unicode(self.regionNameField.toPlainText())
		text = dotlan.convertRegionName(text)
		self.regionNameField.setPlainText(text)
		correct = False
		try:
			url = dotlan.Map.DOTLAN_BASIC_URL.format(text)
			request = urllib2.urlopen(url)
			content = request.read()
			if u"not found" in content:
				correct = False
				# Fallback -> ships vintel with this map?
				try:
					with open(resourcePath("vi/ui/res/mapdata/{0}.svg".format(text))) as _:
						correct = True
				except Exception as e:
					print str(e)
					correct = False
				if not correct:
					QMessageBox.warning(self, u"No such region!", u"I can't find a region called '{0}'".format(text))
			else:
				correct = True
		except Exception as e:
			QMessageBox.critical(self, u"Something went wrong!", u"Error while testing existing '{0}'".format(str(e)))
			print str(e)
			correct = False
		if correct:
			cache = Cache()
			cache.putIntoCache("region_name", text, 60 * 60 * 24 * 365)
			QMessageBox.information(self, u"VINTEL needs restart", u"Region was changed, you need to restart VINTEL!")
			self.accept()


	def setDefaults(self):
		self.regionNameField.setPlainText(u"Providence")


class SystemChat(QtGui.QDialog):
	SYSTEM = 0

	def __init__(self, parent, chatType, selector, chatEntries, knownPlayerNames):
		QtGui.QDialog.__init__(self, parent)
		uic.loadUi(resourcePath("vi/ui/SystemChat.ui"), self)
		self.parent = parent
		self.chatType = 0
		self.selector = selector
		self.chatEntries = []
		for entry in chatEntries:
			self.addChatEntry(entry)
		titleName = ""
		if self.chatType == SystemChat.SYSTEM:
			titleName = self.selector.name
			self.system = selector
		for name in knownPlayerNames:
			self.playerNamesBox.addItem(name)
		self.setWindowTitle("Chat for {0}".format(titleName))
		self.connect(self.closeButton, Qt.SIGNAL("clicked()"), self.closeDialog)
		self.connect(self.alarmButton, Qt.SIGNAL("clicked()"), self.setSystemAlarm)
		self.connect(self.clearButton, Qt.SIGNAL("clicked()"), self.setSystemClear)
		self.connect(self.locationButton, Qt.SIGNAL("clicked()"), self.locationSet)


	def _addMessageToChat(self, message, avatarPixmap):
		scrollToBottom = False
		if (self.chat.verticalScrollBar().value() == self.chat.verticalScrollBar().maximum()):
			scrollToBottom = True
		entry = ChatEntry(message)
		entry.avatarLabel.setPixmap(avatarPixmap)
		listWidgetItem = QtGui.QListWidgetItem(self.chat)
		listWidgetItem.setSizeHint(entry.sizeHint())
		self.chat.addItem(listWidgetItem)
		self.chat.setItemWidget(listWidgetItem, entry)
		self.chatEntries.append(entry)
		self.connect(entry, Qt.SIGNAL("mark_system"), self.parent.markSystemOnMap)
		if scrollToBottom:
			self.chat.scrollToBottom()


	def addChatEntry(self, entry):
		if self.chatType == SystemChat.SYSTEM:
			message = entry.message
			avatarPixmap = entry.avatarLabel.pixmap()
			if self.selector in message.systems:
				self._addMessageToChat(message, avatarPixmap)


	def locationSet(self):
		char = unicode(self.playerNamesBox.currentText())
		self.emit(Qt.SIGNAL("location_set"), char, self.system.name)


	def newAvatarAvailable(self, charname, avatarData):
		for entry in self.chatEntries:
			if entry.message.user == charname:
				entry.updateAvatar(avatarData)

	def setSystemAlarm(self):
		self.system.setStatus(states.ALARM)
		self.parent.updateMap()


	def setSystemClear(self):
		self.system.setStatus(states.CLEAR)
		self.parent.updateMap()


	def closeDialog(self):
		self.accept()


class ChatEntry(QtGui.QWidget):
	TEXT_SIZE = 11
	SHOW_AVATAR = True

	def __init__(self, message):
		QtGui.QWidget.__init__(self)
		uic.loadUi(resourcePath("vi/ui/ChatEntry.ui"), self)
		self.avatarLabel.setPixmap(QtGui.QPixmap(resourcePath("vi/ui/res/qmark.png")))
		self.message = message
		self.updateText()
		self.connect(self.textLabel, QtCore.SIGNAL("linkActivated(QString)"), self.linkClicked)
		self.changeFontSize(self.TEXT_SIZE)
		if not ChatEntry.SHOW_AVATAR:
			self.avatarLabel.setVisible(False)


	def linkClicked(self, link):
		link = unicode(link)
		function, parameter = link.split("/", 1)
		if function == "mark_system" or function == "markSystem":
			self.emit(QtCore.SIGNAL("mark_system"), parameter)
		if function == "link":
			webbrowser.open(parameter)


	def updateText(self):
		time = datetime.datetime.strftime(self.message.timestamp, "%H:%M:%S")
		text = u"<small>{time} - <b>{user}</b> - <i>{room}</i></small><br>{text}".format(user=self.message.user,
				room=self.message.room, time=time, text=self.message.message)
		self.textLabel.setText(text)


	def updateAvatar(self, avatarData):
		image = QImage.fromData(avatarData)
		pixmap = QPixmap.fromImage(image)
		if pixmap.isNull():
			return False
		scaledAvatar = pixmap.scaled(32, 32)
		self.avatarLabel.setPixmap(scaledAvatar)
		return True


	def changeFontSize(self, newSize):
		font = self.textLabel.font()
		font.setPointSize(newSize)
		self.textLabel.setFont(font)


class JumpbridgeChooser(QtGui.QDialog):
	def __init__(self, parent, url):
		QtGui.QDialog.__init__(self, parent)
		uic.loadUi(resourcePath("vi/ui/JumpbridgeChooser.ui"), self)
		self.connect(self.saveButton, Qt.SIGNAL("clicked()"), self.savePath)
		self.connect(self.cancelButton, Qt.SIGNAL("clicked()"), self.accept)
		self.urlField.setText(url)
		# loading format explanation from textfile
		with open(resourcePath("docs/jumpbridgeformat.txt")) as f:
			self.formatInfoField.setPlainText(f.read())

	def savePath(self):
		try:
			url = unicode(self.urlField.text())
			if url != "":
				urllib2.urlopen(url)
			self.emit(QtCore.SIGNAL("set_jumpbridge_url"), url)
			self.accept()
		except Exception as e:
			QtGui.QMessageBox.critical(None, "Finding Jumpbridgedata failed", "Error: {0}".format(unicode(e)), "OK")
