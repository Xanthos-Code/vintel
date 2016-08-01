
from PyQt5.QtCore import Qt, QPoint, QRect, QEvent, pyqtSignal, QUrl
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import QApplication
from vi.ui.viui import MainWindow

if MainWindow.oldStyleWebKit:
    from PyQt5.QtWebKitWidgets import QWebPage
    from PyQt5.QtWebKitWidgets import QWebView
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
        self.offset = QPoint(0, 0)
        self.handIsClosed = False
        self.clickedInScrollBar = False
        self.widget = None
        self.setPage(VintelSvgPage(parent=self))


    def setPage(self, newPage):
        super(PanningWebView, self).setPage(newPage)
        if MainWindow.oldStyleWebKit:
            self.widget = self.page().mainFrame()
        else:
            self.widget = self.page()


    def mousePressEvent(self, mouseEvent):
        pos = mouseEvent.pos()

        if mouseEvent.buttons() == Qt.LeftButton and (self.pointInScroller(pos, Qt.Vertical) or self.pointInScroller(pos, Qt.Horizontal)):
            self.clickedInScrollBar = True
        else:
            if self.ignored.count(mouseEvent):
                self.ignored.remove(mouseEvent)
                return super(PanningWebView, self).mousePressEvent(mouseEvent)

            if not self.pressed and not self.scrolling and mouseEvent.modifiers() == Qt.NoModifier:
                if mouseEvent.buttons() == Qt.LeftButton:
                    self.pressed = True
                    self.scrolling = False
                    self.handIsClosed = False
                    QApplication.setOverrideCursor(Qt.OpenHandCursor)

                    self.position = mouseEvent.pos()
                    self.offset = self.widget.scrollPosition()
                    return

        return super(PanningWebView, self).mousePressEvent(mouseEvent)


    def mouseReleaseEvent(self, mouseEvent):
        if self.clickedInScrollBar:
            self.clickedInScrollBar = False
        else:
            if self.ignored.count(mouseEvent):
                self.ignored.remove(mouseEvent)
                return super(PanningWebView, self).mousePressEvent(mouseEvent)

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

                event1 = QMouseEvent(QEvent.MouseButtonPress, self.position, Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
                event2 = QMouseEvent(mouseEvent)

                self.ignored.append(event1)
                self.ignored.append(event2)

                QApplication.postEvent(self, event1)
                QApplication.postEvent(self, event2)
                return

        return super(PanningWebView, self).mouseReleaseEvent(mouseEvent)


    def mouseMoveEvent(self, mouseEvent):
        if not self.clickedInScrollBar:
            if self.scrolling:
                if not self.handIsClosed:
                    QApplication.restoreOverrideCursor()
                    QApplication.setOverrideCursor(Qt.ClosedHandCursor)
                    self.handIsClosed = True
                delta = mouseEvent.pos() - self.position
                p = self.offset - delta
                if MainWindow.oldStyleWebKit:
                    self.widget.setScrollPosition(p)
                else:
                    self.widget.runJavaScript('window.scrollTo({}, {});'.format(p.x(), p.y()))
                return

            if self.pressed:
                self.pressed = False
                self.scrolling = True
                return

        return super(PanningWebView, self).mouseMoveEvent(mouseEvent)


    def pointInScroller(self, position, orientation):
        rect = self.widget.scrollBarGeometry(orientation)
        topLeft = self.mapToGlobal(rect.topLeft())
        bottomRight = self.mapToGlobal(rect.bottomRight())
        globalRect = QRect(topLeft, bottomRight)
        return globalRect.contains(self.mapToGlobal(position))


class VintelSvgPage(QWebPage if MainWindow.oldStyleWebKit else QWebEnginePage):

    def __init__(self, parent=None):
        if MainWindow.oldStyleWebKit:
            QWebPage.__init__(self, parent)
        else:
            QWebEnginePage.__init__(self, parent)


    def acceptNavigationRequest(self, url, type, isMainFrame):
        if MainWindow.oldStyleWebKit:
            return super(PanningWebView, self).acceptNavigationRequest(url, type, isMainFrame)
        else:
            if type == QWebEnginePage.NavigationTypeLinkClicked:
                self.view().mapLinkClicked.emit(url)
                return False
            return True
