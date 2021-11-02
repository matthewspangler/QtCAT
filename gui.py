from PySide6.QtWidgets import QMdiArea, QLineEdit, QPushButton, QListWidget, QComboBox, QTextEdit, QMdiSubWindow
from PySide6.QtCore import QFile, QIODevice, QObject
from PySide6.QtUiTools import QUiLoader
from yapsy.PluginManager import PluginManager
from functools import partial
from PySide6.QtWidgets import QDialog
import sys
import os
import toml
from device_session import DeviceSession
from session_widget import QSessionSubWindow

# Discovers relative path (for differentiating between development and production plugin directories)
here = os.path.abspath(os.path.dirname(__file__))
get_path = partial(os.path.join, here)

sessions_toml_file = "session_list.toml"


class CXAGui(QObject):
    def __init__(self, ui_file, parent=None):
        super(CXAGui, self).__init__(parent)
        ui_file = QFile(ui_file)
        ui_file.open(QFile.ReadOnly)

        loader = QUiLoader()
        self.window = loader.load(ui_file)
        ui_file.close()

        # Dialogs
        info_dialog_file = QFile('info_dialog.ui')
        info_dialog_file.open(QFile.ReadOnly)
        self.info_dialog = loader.load(info_dialog_file)
        new_session_dialog_file = QFile('new_sesson_dialog.ui')
        new_session_dialog_file.open(QFile.ReadOnly)
        self.new_session_dialog = loader.load(new_session_dialog_file)
        # Dialog's widgets
        self.info_dialog.nameEdit = self.info_dialog.findChild(QLineEdit, 'nameEdit')
        self.info_dialog.ipEdit = self.info_dialog.findChild(QLineEdit, 'ipEdit')
        self.info_dialog.portEdit = self.info_dialog.findChild(QLineEdit, 'portEdit')
        self.info_dialog.usernameEdit = self.info_dialog.findChild(QLineEdit, 'usernameEdit')
        self.info_dialog.passwordEdit = self.info_dialog.findChild(QLineEdit, 'passwordEdit')
        self.info_dialog.enpassEdit = self.info_dialog.findChild(QLineEdit, 'enpassEdit')
        self.info_dialog.deviceBox = self.info_dialog.findChild(QComboBox, 'deviceBox')
        # Buttons
        self.sessionButton = self.window.findChild(QPushButton, 'sessionButton')
        self.connectButton = self.window.findChild(QPushButton, 'connectButton')
        self.runButton = self.window.findChild(QPushButton, 'runButton')
        self.sendButton = self.window.findChild(QPushButton, 'sendButton')
        self.addButton = self.window.findChild(QPushButton, 'addButton')
        self.infoButton = self.window.findChild(QPushButton, 'infoButton')
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
        self.addButton.clicked.connect(self.add_session)
        self.sessionMDI.subWindowActivated.connect(self.handle_subwindow_focus)

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
        self.sessions_toml = None
        self.sessions = {}
        self.populate_sessions_list()

        self.window.show()

    def add_session(self):
        self.new_session_dialog.show()
        session_data = {}
        ip = self.info_dialog.ipEdit.text()
        port = self.info_dialog.portEdit.text()
        username = self.info_dialog.usernameEdit.text()
        password = self.info_dialog.passwordEdit.text()
        enable_password = self.info_dialog.enpassEdit.text()
        device_type = self.info_dialog.deviceBox.currentText()

        pass

    def show_plugin_info(self):
        #self.info_dialogs
        self.info_dialog.show()

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
