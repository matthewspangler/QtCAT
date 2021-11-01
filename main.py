from gui import CXAGui
from PySide6.QtWidgets import QApplication
import sys
import os


def main():
    sys._excepthook = sys.excepthook

    def exception_hook(exctype, value, traceback):
        print(exctype, value, traceback)
        sys._excepthook(exctype, value, traceback)
        sys.exit(1)

    sys.excepthook = exception_hook

    print("Running in " + os.getcwd() + " .\n")

    app = QApplication(sys.argv)
    #app.setStyle('Fusion')
    form = CXAGui('cxagui.ui')
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
