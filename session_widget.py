from PySide6.QtWidgets import QTextBrowser, QMdiSubWindow


class QSessionSubWindow(QMdiSubWindow):
    def __init__(self, title):
        super().__init__()
        self.outputEdit = QTextBrowser()
        self.setWidget(self.outputEdit)
        self.setWindowTitle(title)
