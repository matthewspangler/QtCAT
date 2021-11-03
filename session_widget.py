from PySide6.QtWidgets import QTextBrowser, QWidget, QTabWidget, QMdiSubWindow
from PySide6.QtGui import QCloseEvent
from PySide6.QtCore import Qt


class QSessionWidget(QTextBrowser):
    def __init__(self, title, ):
        super().__init__()
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowTitle(title)

    def closeEvent(self, event: QCloseEvent) -> None:
        pass