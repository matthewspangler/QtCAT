from PySide6.QtWidgets import QTextEdit, QMdiSubWindow


class QSessionSubWindow(QMdiSubWindow):
    def __init__(self, title):
        super().__init__()
        self.outputEdit = QTextEdit()
        self.setWidget(self.outputEdit)
        self.setWindowTitle(title)
