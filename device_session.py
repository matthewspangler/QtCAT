import napalm
from session_widget import QSessionSubWindow
from PySide6.QtCore import QThread, Signal, Slot, QMutex
import threading, queue
import time


class DeviceThread(threading.Thread):
    def __init__(self, device_info: dict, device_type: str, le_queue: queue):
        threading.Thread.__init__(self)
        self.lock = threading.Lock()
        self.device_type = device_type
        self.device_info = device_info
        self.driver = napalm.get_network_driver(self.device_type)
        self.device = self.driver(**self.device_info)
        # If set to true, loop in run() quits
        self.disconnect = False
        self.run_plugin = False
        self.plugin = None
        self.le_queue = le_queue

    def run(self):
        try:
            self.le_queue.put("Connecting...")
            self.device.open()
        except Exception as e:
            self.le_queue.put(str(e))
            return
        self.le_queue.put("Connected!")
        self.le_queue.put("Awaiting plugin choice.")
        while not self.disconnect:
            time.sleep(1)
            if self.run_plugin:
                self.le_queue.put("Running '{}' plugin...".format(self.plugin.name))
                try:
                    self.plugin.plugin_object.run(self.device, self.le_queue)
                except Exception as e:
                    self.le_queue.put(str(e))
                self.run_plugin = False
        self.le_queue.put("Disconnecting...")
        self.device.close()


class DeviceSession:
    def __init__(self, session_window: QSessionSubWindow, device_info: dict, device_type: str):
        self.le_queue = queue.Queue()

        self.session_window = session_window
        self.thread = DeviceThread(device_info, device_type, self.le_queue)
        self.thread.start()

        # If set to true, loop in refresh_output() quits
        self.refresh = True
        self.refresh_thread = threading.Thread(target=self.refresh_output, args=[self.le_queue])
        self.refresh_thread.start()

        # Comment or uncomment this function to run code automatically on connect:
        self.test_function()

    def refresh_output(self, le_queue: queue):
        count = 1
        stuff = []
        while self.refresh:
            time.sleep(1)
            # Refresh output every 1 second:
            while not le_queue.empty():
                output = le_queue.get()
                le_queue.task_done()
                stuff.append(output)
                # TODO: crashes if queue output is very large?
                self.session_window.outputEdit.append(output)


    def test_function(self):
        print("Test Function")

    def connect(self):
        pass

    def disconnect(self):
        self.refresh = False
        self.thread.disconnect = True

    def user_exec(self):
        pass

    def priv_exec(self):
        pass

    def global_conf(self):
        pass

    def interface_conf(self):
        pass

    def get_running_config(self):
        pass

    def get_startup_config(self):
        pass

    def get_interfaces(self):
        pass
