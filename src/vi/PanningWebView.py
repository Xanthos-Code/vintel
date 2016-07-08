
import six

from vi.ui.viui import MainWindow
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5 import QtCore
from PyQt5.QtCore import QPoint, QEvent, pyqtSignal, QUrl

if MainWindow.oldStyleWebKit:
    from PyQt5.QtWebWidgets import QWebPage
    from PyQt5.QtWebWidgets import QWebView
else:
    from PyQt5.QtWebEngineWidgets import QWebEnginePage
    from PyQt5.QtWebEngineWidgets import QWebEngineView


class PanningWebView(QWebView if MainWindow.oldStyleWebKit else QWebEngineView):

    mapLinkClicked = pyqtSignal(QUrl)

    def __init__(self, parent=None):
        super(PanningWebView, self).__init__()
        self.pressed = False
        self.scrolling = False
        self.ignored = []
        self.position = None
        self.offset = 0
        self.handIsClosed = False
        if not MainWindow.oldStyleWebKit:
            self.setPage(VintelSvgPage(parent=self))


    def mousePressEvent(self, mouseEvent):
        if self.ignored.count(mouseEvent):
            self.ignored.remove(mouseEvent)
            return super(PanningWebView, self).mousePressEvent(self, mouseEvent)

        if not self.pressed and not self.scrolling and mouseEvent.modifiers() == QtCore.Qt.NoModifier:
            if mouseEvent.buttons() == QtCore.Qt.LeftButton:
                self.pressed = True
                self.scrolling = False
                self.handIsClosed = False
                QApplication.setOverrideCursor(QtCore.Qt.OpenHandCursor)

                self.position = mouseEvent.pos()
                frame = self.page()
                scrollx = frame.evaluateJavaScript("window.scrollX")
                scrolly = frame.evaluateJavaScript("window.scrollY")
                self.offset = QPoint(scrollx, scrolly)
                return
        return super(PanningWebView, self).mousePressEvent(self, mouseEvent)


    def mouseReleaseEvent(self, mouseEvent):
        if self.ignored.count(mouseEvent):
            self.ignored.remove(mouseEvent)
            return super(PanningWebView, self).mousePressEvent(self, mouseEvent)

        if self.scrolling:
            self.pressed = False
            self.scrolling = False
            self.handIsClosed = False
            QApplication.restoreOverrideCursor()
            return

        if self.pressed:
            self.pressed = False
            self.scrolling = False
            self.handIsClosed = False
            QApplication.restoreOverrideCursor()

            event1 = QMouseEvent(QEvent.MouseButtonPress, self.position, QtCore.Qt.LeftButton, QtCore.Qt.LeftButton, QtCore.Qt.NoModifier)
            event2 = QMouseEvent(mouseEvent)

            self.ignored.append(event1)
            self.ignored.append(event2)

            QApplication.postEvent(self, event1)
            QApplication.postEvent(self, event2)
            return
        return super(PanningWebView, self).mouseReleaseEvent(self, mouseEvent)


    def mouseMoveEvent(self, mouseEvent):
        if self.scrolling:
            if not self.handIsClosed:
                QApplication.restoreOverrideCursor()
                QApplication.setOverrideCursor(QtCore.Qt.ClosedHandCursor)
                self.handIsClosed = True
            delta = mouseEvent.pos() - self.position
            p = self.offset - delta
            frame = self.page()
            frame.evaluateJavaScript('window.scrollTo({}, {});'.format(p.x(), p.y()))
            return

        if self.pressed:
            self.pressed = False
            self.scrolling = True
            return
        return super(PanningWebView, self).mouseMoveEvent(self, mouseEvent)


class VintelSvgPage(QWebPage if MainWindow.oldStyleWebKit else QWebEnginePage):

    def __init__(self, parent=None):
        QWebEnginePage.__init__(self, parent)


    def acceptNavigationRequest(self, url, type, isMainFrame):
        if type == QWebEnginePage.NavigationTypeLinkClicked:
            self.view().mapLinkClicked.emit(url)
            return False
        return True
