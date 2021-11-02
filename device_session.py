import napalm
from session_widget import QSessionSubWindow
from PySide6.QtCore import QThread, Signal, Slot, QMutex
import threading, queue
import time


class DeviceThread(threading.Thread):
    """
    This is where the ssh/telnet connection happens, and where plugins are run on that connection.
    """
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
        # Anything put in le_queue is printed to the GUI
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
    """
    This class creates 2 threads, one for running the device connection, and another for updating the GUI with output
    from the device connection.
    """
    def __init__(self, session_window: QSessionSubWindow, device_info: dict, device_type: str):
        # Anything put in le_queue is printed to the GUI
        self.le_queue = queue.Queue()

        # QSubWindow corresponding to the device session
        self.session_window = session_window

        # Device connection thread
        self.thread = DeviceThread(device_info, device_type, self.le_queue)
        self.thread.start()

        # If set to true, loop in refresh_output() quits
        self.refresh = True
        # Thread for refreshing GUI with output from DeviceThread()
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

    def disconnect(self):
        self.refresh = False
        self.thread.disconnect = True
        #del self.session_window
