
from PyQt5.QtCore import Qt, QPoint, QEvent, pyqtSignal, QUrl
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
        if not MainWindow.oldStyleWebKit:
            self.setPage(VintelSvgPage(parent=self))


    def mousePressEvent(self, mouseEvent):
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
                if MainWindow.oldStyleWebKit:
                    frame = self.page().mainFrame()
                else:
                    frame = self.page()
                scrollx = frame.evaluateJavaScript("window.scrollX")
                scrolly = frame.evaluateJavaScript("window.scrollY")
                self.offset = QPoint(scrollx, scrolly)
                return

        return super(PanningWebView, self).mousePressEvent(mouseEvent)


    def mouseReleaseEvent(self, mouseEvent):
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
        if self.scrolling:
            if not self.handIsClosed:
                QApplication.restoreOverrideCursor()
                QApplication.setOverrideCursor(Qt.ClosedHandCursor)
                self.handIsClosed = True
            delta = mouseEvent.pos() - self.position
            p = self.offset - delta

            if MainWindow.oldStyleWebKit:
                frame = self.page().mainFrame()
            else:
                frame = self.page()
            frame.evaluateJavaScript('window.scrollTo({}, {});'.format(p.x(), p.y()))
            return

        if self.pressed:
            self.pressed = False
            self.scrolling = True
            return

        return super(PanningWebView, self).mouseMoveEvent(mouseEvent)


class VintelSvgPage(QWebPage if MainWindow.oldStyleWebKit else QWebEnginePage):

    def __init__(self, parent=None):
        QWebEnginePage.__init__(self, parent)


    def acceptNavigationRequest(self, url, type, isMainFrame):
        if type == QWebEnginePage.NavigationTypeLinkClicked:
            self.view().mapLinkClicked.emit(url)
            return False
        return True
