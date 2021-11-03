from yapsy.IPlugin import IPlugin
import napalm
import queue
from PySide6.QtWidgets import QInputDialog, QWidget
from PySide6.QtCore import Qt
from dialogs import PluginDialog


class ChangeHostname(IPlugin):
    def run(self, device: napalm.base.NetworkDriver, queue: queue.Queue):
        queue.put("Running change_hostname.py")

        dialog = PluginDialog()
        hostname, ok = dialog.setupUi("Change hostname", "Please enter a hostname")
        if ok:
            queue.put("Changing hostname to '{}'".format(hostname))
            output = device.cli(["conf t",
                                 "host {}".format(hostname)])
            queue.put(output)

        device.commit_config()
        queue.put("Saved running-config!")
