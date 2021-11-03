from yapsy.IPlugin import IPlugin
from device_session import QDeviceSession
from ciscoconfparse import CiscoConfParse
from yapsy.IPlugin import IPlugin
import napalm
import queue


class TemplatePlugin(IPlugin):
    def run(self, device: napalm.base.NetworkDriver, queue: queue.Queue):
        run_conf = device.get_config().splitlines()

        parse = CiscoConfParse(run_conf, syntax='ios')

        # Choose the first interface (parent) object
        for intf_obj in parse.find_objects('^interface')[0:1]:
            print("Parent obj: " + str(intf_obj))

            # Iterate over all the child objects of that parent object
            for c_obj in intf_obj.children:
                print("Child obj :    " + str(c_obj))

        return None