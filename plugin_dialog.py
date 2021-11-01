from PySide6.QtWidgets import QWidget, QPushButton, QLabel, QInputDialog, QLineEdit
from PySide6.QtCore import QRect

class PluginDialog(QWidget):
    def __init__(self):
        super().__init__()

    def setupUi(self, title, label):
        self.centralwidget = QWidget()

        self.pushButton = QPushButton(self.centralwidget)
        self.pushButton.setGeometry(QRect(160, 130, 93, 28))

        # For displaying confirmation message along with user's info.
        self.label = QLabel(self.centralwidget)
        self.label.setGeometry(QRect(170, 40, 201, 111))

        # Keeping the text of label empty initially.
        self.label.setText("")

        input, ok = QInputDialog.getText(
            self, title, label, QLineEdit.Normal, "")

        return input, ok