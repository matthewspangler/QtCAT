from yapsy.IPlugin import IPlugin
import napalm
import queue

class GetFacts(IPlugin):
    def run(self, device: napalm.base.NetworkDriver, queue: queue.Queue):
        queue.put("Running the script: get_facts.py")
        output = device.get_config()
        queue.put(str(output))
        queue.put("Plugin done running.")
