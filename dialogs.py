from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QWidget, QPushButton, QLabel, QInputDialog, QLineEdit, QDialog, QComboBox
from PySide6.QtCore import QRect, QFile


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


class InfoDialog(QDialog):
    def __init__(self, ui_file):
        super().__init__()
        ui_file = QFile(ui_file)
        ui_file.open(QFile.ReadOnly)

        loader = QUiLoader()
        self.window = loader.load(ui_file)
        ui_file.close()


class NewSessionDialog(QDialog):
    def __init__(self, ui_file, parent=None):
        super().__init__()
        ui_file = QFile(ui_file)
        ui_file.open(QFile.ReadOnly)

        loader = QUiLoader()
        self.window = loader.load(ui_file)
        ui_file.close()

        # Dialog's widgets
        self.nameEdit = self.window.findChild(QLineEdit, 'nameEdit')
        self.ipEdit = self.window.findChild(QLineEdit, 'ipEdit')
        self.portEdit = self.window.findChild(QLineEdit, 'portEdit')
        self.usernameEdit = self.window.findChild(QLineEdit, 'usernameEdit')
        self.passwordEdit = self.window.findChild(QLineEdit, 'passwordEdit')
        self.enpassEdit = self.window.findChild(QLineEdit, 'enpassEdit')
        self.deviceBox = self.window.findChild(QComboBox, 'deviceBox')
        self.okButton = self.window.findChild(QPushButton, 'okButton')
        self.cancelButton = self.window.findChild(QPushButton, 'cancelButton')
        self.cancelButton.clicked.connect(self.cancel)
        self.session_data = {}

    def cancel(self):
        self.window.close()

    def create_session_dict(self):
        # Sets up session info in a dict for being added to the toml data later
        name = self.nameEdit.text()
        ip = self.ipEdit.text()
        port = self.portEdit.text()
        username = self.usernameEdit.text()
        password = self.passwordEdit.text()
        enable_password = self.enpassEdit.text()
        device_type = self.deviceBox.currentText()
        session_data = {"ip": ip,
                        "port": port,
                        "username": username,
                        "password": password,
                        "enable_password": enable_password,
                        "device_type": device_type}
        return name, session_data