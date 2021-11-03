import os
from functools import partial
import webbrowser
import yaml

import toml
from PySide6.QtCore import QFile, QObject
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QMdiArea, QLineEdit, QPushButton, QListWidget, QComboBox
from yapsy.PluginManager import PluginManager

from device_session import DeviceSession
from dialogs import InfoDialog, NewSessionDialog
from session_widget import QSessionWidget

# Discovers relative path (for differentiating between development and production plugin directories)
here = os.path.abspath(os.path.dirname(__file__))
get_path = partial(os.path.join, here)

sessions_toml_file = "session_list.toml"


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
        self.disconnectButton = self.window.findChild(QPushButton, 'disconnectButton')
        self.runButton = self.window.findChild(QPushButton, 'runButton')
        self.sendButton = self.window.findChild(QPushButton, 'sendButton')
        self.addButton = self.window.findChild(QPushButton, 'addButton')
        self.editButton = self.window.findChild(QPushButton, 'editButton')
        self.infoButton = self.window.findChild(QPushButton, 'infoButton')
        self.deleteButton = self.window.findChild(QPushButton, 'deleteButton')
        self.refreshSessionButton = self.window.findChild(QPushButton, 'refreshSessionButton')
        self.refreshPluginButton = self.window.findChild(QPushButton, 'refreshPluginButton')
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
        self.editButton.clicked.connect(self.edit_sessions)
        self.refreshSessionButton.clicked.connect(self.refresh_sessions)
        self.refreshPluginButton.clicked.connect(self.refresh_plugins)
        self.sessionButton.clicked.connect(self.session_connect_button)
        self.connectButton.clicked.connect(self.top_connect_button)
        self.disconnectButton.clicked.connect(self.disconnect_handler)
        self.runButton.clicked.connect(self.run_script_handler)
        self.sendButton.clicked.connect(self.run_command_handler)
        self.commandEdit.returnPressed.connect(self.run_command_handler)
        self.infoButton.clicked.connect(self.show_plugin_info)
        self.addButton.clicked.connect(self.show_session_dialog)
        self.deleteButton.clicked.connect(self.delete_session)
        self.sessionMDI.subWindowActivated.connect(self.handle_subwindow_focus)

        # Dialogs
        self.info_dialog = InfoDialog('info_dialog.ui')
        self.new_session_dialog = NewSessionDialog('new_sesson_dialog.ui')
        self.new_session_dialog.okButton.clicked.connect(self.add_session)
        # self.new_session_dialog.accepted.connect(self.add_session)

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
        self.sessions = []
        self.populate_sessions_list()

        self.window.show()

    def get_focused_subwindow(self):
        return self.sessionMDI.activeSubWindow()

    def delete_session(self):
        if self.sessionList.selectedItems():
            for selection in self.sessionList.selectedItems():
                self.sessions_toml.pop(selection.text())
                self.sessionList.takeItem(self.sessionList.row(selection))
            self.save_session_toml()

    def edit_sessions(self):
        editor = os.getenv('EDITOR')
        if editor:
            os.system(editor + ' ' + sessions_toml_file)
        else:
            webbrowser.open(sessions_toml_file)

    def refresh_sessions(self):
        self.sessionList.clear()
        self.sessions = {}
        self.populate_sessions_list()
        pass

    def refresh_plugins(self):
        self.pluginList.clear()
        self.plugins = {}
        self.populate_plugins()

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
        if self.pluginList.selectedItems():
            plugin_text = self.pluginList.selectedItems()[0].text()
            plugin = self.plugins[plugin_text]
            plugin_info = {"name": plugin.name,
                           "description": plugin.description,
                           "author": plugin.author}
            pretty_info = yaml.dump(plugin_info, allow_unicode=True, default_flow_style=False)
            self.info_dialog.plugin = plugin
            self.info_dialog.infoBrowser.append(pretty_info)
            self.info_dialog.window.show()

    def handle_subwindow_focus(self, subwindow):
        self.focused_subwindow = subwindow

    def new_tab_session(self, ip, port, username, password, enable_pass, device_type):
        # TODO: check for existing session!
        # New connection to device
        line_edit = QSessionWidget("{}:{}".format(ip, port))
        new_window = self.sessionMDI.addSubWindow(line_edit)
        new_window.outputEdit = line_edit
        new_window.outputEdit.show()
        device_info = {"hostname": ip,
                       "username": username,
                       "password": password,
                       "optional_args": {"port": port,
                                         "transport": "telnet",
                                         "global_delay_factor": 2}
                       }
        new_session = DeviceSession(device_info, device_type)
        # Associate DeviceSession with the session widget (QSessionWidget)
        self.sessions.append(new_session)

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
        if os.path.exists(sessions_toml_file):
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
        if self.pluginList.selectedItems():
            plugin_text = self.pluginList.selectedItems()[0].text()
            plugin_choice = self.plugins[plugin_text]
            self.get_focused_subwindow().thread.plugin = plugin_choice

    def disconnect_handler(self):
        if self.focused_subwindow:
            self.get_focused_subwindow().disconnect = True

    def run_command_handler(self):
        command = self.commandEdit.text()
        self.get_focused_subwindow().thread.command = command

    def session_connect_button(self):
        if self.sessionList.selectedItems() != 0:
            self.set_session_toml()
            for list_selection in self.sessionList.selectedItems():
                device_toml = self.sessions_toml[list_selection.text()]
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
