from ciscoconfparse import CiscoConfParse
from yapsy.IPlugin import IPlugin
import napalm
import queue


class TemplatePlugin(IPlugin):
    def run(self, device: napalm.base.NetworkDriver, queue: queue.Queue):
        queue.put(str(device.get_environment()))