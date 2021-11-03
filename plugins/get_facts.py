from yapsy.IPlugin import IPlugin
import napalm
import queue

class GetFacts(IPlugin):
    def run(self, device: napalm.base.NetworkDriver, output_queue: queue.Queue):
        output_queue.put("Running the script: get_facts.py")
        output = device.get_interfaces_ip()
        output_queue.put(str(output))
        output_queue.put("Plugin done running.")
