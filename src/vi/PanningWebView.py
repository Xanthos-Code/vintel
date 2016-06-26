
from PyQt4.QtWebKit import QWebView
from PyQt4.QtGui import *
from PyQt4 import QtCore
from PyQt4.QtCore import QPoint
from PyQt4.QtCore import QString
from PyQt4.QtCore import QEvent

class PanningWebView(QWebView):

    def __init__(self, parent=None):
        super(PanningWebView, self).__init__()
        self.pressed = False
        self.scrolling = False
        self.ignored = []
        self.position = None
        self.offset = 0


    def mousePressEvent(self, mouseEvent):

        if self.ignored.count(mouseEvent):
            self.ignored.remove(mouseEvent)
            return QWebView.mousePressEvent(self, mouseEvent)

        if not self.pressed and not self.scrolling and mouseEvent.modifiers() == QtCore.Qt.NoModifier:
            if mouseEvent.buttons() == QtCore.Qt.LeftButton:
                self.pressed = True
                self.scrolling = False
                self.position = mouseEvent.pos()
                frame = self.page().mainFrame()
                xTuple = frame.evaluateJavaScript("window.scrollX").toInt()
                yTuple = frame.evaluateJavaScript("window.scrollY").toInt()
                self.offset = QPoint(xTuple[0], yTuple[0])
                QApplication.setOverrideCursor(QtCore.Qt.OpenHandCursor)
                return

        return QWebView.mousePressEvent(mouseEvent)


    def mouseReleaseEvent(self, mouseEvent):

        if self.ignored.count(mouseEvent):
            self.ignored.remove(mouseEvent)
            return QWebView.mousePressEvent(self, mouseEvent)

        if self.scrolling:
            self.pressed = False
            self.scrolling = False
            QApplication.restoreOverrideCursor()
            return

        if self.pressed:
            self.pressed = False
            self.scrolling = False

            event1 = QMouseEvent(QEvent.MouseButtonPress, self.position, QtCore.Qt.LeftButton, QtCore.Qt.LeftButton, QtCore.Qt.NoModifier)
            event2 = QMouseEvent(mouseEvent)

            self.ignored.append(event1)
            self.ignored.append(event2)

            QApplication.postEvent(self, event1)
            QApplication.postEvent(self, event2)
            QApplication.restoreOverrideCursor()
            return

        return QWebView.mouseReleaseEvent(self, mouseEvent)


    def mouseMoveEvent(self, mouseEvent):

        if self.scrolling:
            delta = mouseEvent.pos() - self.position
            p = self.offset - delta
            frame = self.page().mainFrame()
            frame.evaluateJavaScript(QString("window.scrollTo(%1, %2);").arg(p.x()).arg(p.y()));
            return

        if self.pressed:
            self.pressed = False
            self.scrolling = True
            return

        return QWebView.mouseMoveEvent(self, mouseEvent)