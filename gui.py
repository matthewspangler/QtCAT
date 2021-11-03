import os
from functools import partial

import toml
from PySide6.QtCore import QFile, QObject, SIGNAL, SLOT
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QMdiArea, QLineEdit, QPushButton, QListWidget, QComboBox, QDialogButtonBox, QDialog
from yapsy.PluginManager import PluginManager

from device_session import DeviceSession
from session_widget import QSessionSubWindow

# Discovers relative path (for differentiating between development and production plugin directories)
here = os.path.abspath(os.path.dirname(__file__))
get_path = partial(os.path.join, here)

sessions_toml_file = "session_list.toml"


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


class QtCAT(QObject):
    def __init__(self, ui_file, parent=None):
        super(QtCAT, self).__init__(parent)
        ui_file = QFile(ui_file)
        ui_file.open(QFile.ReadOnly)

        loader = QUiLoader()
        self.window = loader.load(ui_file)
        ui_file.close()

        # Buttons
        self.sessionButton = self.window.findChild(QPushButton, 'sessionButton')
        self.connectButton = self.window.findChild(QPushButton, 'connectButton')
        self.runButton = self.window.findChild(QPushButton, 'runButton')
        self.sendButton = self.window.findChild(QPushButton, 'sendButton')
        self.addButton = self.window.findChild(QPushButton, 'addButton')
        self.infoButton = self.window.findChild(QPushButton, 'infoButton')
        self.deleteButton = self.window.findChild(QPushButton, 'deleteButton')
        # Lists
        self.pluginList = self.window.findChild(QListWidget, 'pluginList')
        self.sessionList = self.window.findChild(QListWidget, 'sessionList')
        # Line Edits
        self.ipEdit = self.window.findChild(QLineEdit, 'ipEdit')
        self.portEdit = self.window.findChild(QLineEdit, 'portEdit')
        self.userEdit = self.window.findChild(QLineEdit, 'userEdit')
        self.passEdit = self.window.findChild(QLineEdit, 'passEdit')
        self.enpassEdit = self.window.findChild(QLineEdit, 'enpassEdit')
        self.commandEdit = self.window.findChild(QLineEdit, 'commandEdit')
        # Combo Box
        self.osCombo = self.window.findChild(QComboBox, 'osCombo')
        # MDI Area
        self.sessionMDI = self.window.findChild(QMdiArea, 'sessionMDI')

        # Connect widgets with functions:
        self.sessionButton.clicked.connect(self.session_connect_button)
        self.connectButton.clicked.connect(self.top_connect_button)
        self.runButton.clicked.connect(self.run_script_handler)
        self.sendButton.clicked.connect(self.run_command_handler)
        self.infoButton.clicked.connect(self.show_plugin_info)
        self.addButton.clicked.connect(self.show_session_dialog)
        self.deleteButton.clicked.connect(self.delete_session)
        self.sessionMDI.subWindowActivated.connect(self.handle_subwindow_focus)

        # Dialogs
        self.info_dialog = InfoDialog('info_dialog.ui')
        self.new_session_dialog = NewSessionDialog('new_sesson_dialog.ui')
        self.new_session_dialog.okButton.clicked.connect(self.add_session)
        #self.new_session_dialog.accepted.connect(self.add_session)

        # Keep track of the focused subwindow, so we know what window to run plugins on.
        self.focused_subwindow = None

        # Build the manager
        self.cxl_plugins = PluginManager()
        # Tell it the default place(s) where to find plugins
        self.cxl_plugins.setPluginPlaces([get_path("./plugins")])
        # Load all plugins
        self.plugins = {}
        self.populate_plugins()

        # Load sessions list from toml data
        self.sessions_toml = {}
        self.sessions = {}
        self.populate_sessions_list()

        self.window.show()

    def delete_session(self):
        for selection in self.sessionList.selectedItems():
            self.sessions_toml.pop(selection.text())
            self.sessionList.takeItem(self.sessionList.row(selection))
        self.save_session_toml()

    def show_session_dialog(self):
        self.new_session_dialog.window.show()

    def add_session(self):
        name, session_data = self.new_session_dialog.create_session_dict()
        self.new_session_dialog.window.close()
        self.sessions_toml[name] = session_data
        self.save_session_toml()
        self.sessionList.clear()
        for item in self.sessions_toml:
            self.sessionList.addItem(item)

    def show_plugin_info(self):
        self.info_dialog.window.show()

    def handle_subwindow_focus(self, subwindow):
        self.focused_subwindow = subwindow

    def new_tab_session(self, ip, port, username, password, enable_pass, device_type):
        # New connection to device
        new_window = QSessionSubWindow("{}:{}".format(ip, port))
        self.sessionMDI.addSubWindow(new_window)
        new_window.show()
        device_info = {"hostname": ip,
                       "username": username,
                       "password": password,
                       "optional_args": {"port": port,
                                         "transport": "telnet",
                                         "global_delay_factor": 2}
                       }
        new_session = DeviceSession(new_window, device_info, device_type)
        # Associate DeviceSession with the session widget (QSessionSubWindow)
        self.sessions[new_window] = new_session

    def close_tab_session(self):
        # TODO
        pass

    def set_session_toml(self):
        self.sessions_toml = toml.load(sessions_toml_file)

    def save_session_toml(self):
        toml_data = toml.dumps(self.sessions_toml)
        f = open(sessions_toml_file, 'w')
        toml.dump(self.sessions_toml, f)
        f.close()

    def populate_sessions_list(self):
        self.set_session_toml()
        for item in self.sessions_toml:
            self.sessionList.addItem(item)

    def save_sessions_list(self):
        # TODO
        pass

    def populate_plugins(self):
        self.cxl_plugins.collectPlugins()
        for plugin in self.cxl_plugins.getAllPlugins():
            self.plugins["{} - {}".format(plugin.name, plugin.description)] = plugin
        for plugin in self.plugins:
            self.pluginList.addItem(plugin)

    def run_script_handler(self):
        plugin_text = self.pluginList.selectedItems()[0].text()
        plugin_choice = self.plugins[plugin_text]
        self.sessions[self.focused_subwindow].thread.plugin = plugin_choice

    def run_command_handler(self):
        command = self.commandEdit.text()
        self.sessions[self.focused_subwindow].thread.command = command

    def session_connect_button(self):
        self.set_session_toml()
        # TODO - multiple device selections
        list_selection = self.sessionList.selectedItems()[0].text()
        device_toml = self.sessions_toml[list_selection]
        ip = device_toml["ip"]
        port = device_toml["port"]
        username = device_toml["username"]
        password = device_toml["password"]
        enable_password = device_toml["enable_password"]
        device_type = device_toml["device_type"]
        self.new_tab_session(ip, port, username, password, enable_password, device_type)

    def top_connect_button(self):
        # TODO: error handling for invalid values, and detecting default line edit values:
        ip = self.ipEdit.text()
        port = self.portEdit.text()
        username = self.userEdit.text()
        password = self.passEdit.text()
        enable_pass = self.enpassEdit.text()
        device_type = self.osCombo.currentText()

        self.new_tab_session(ip, port, username, password, enable_pass, device_type)
