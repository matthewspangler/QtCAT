from gui import CXAGui
from PySide6.QtWidgets import QApplication
import sys
import os


def main():
    print("Running in " + os.getcwd() + " .\n")

    app = QApplication(sys.argv)
    #app.setStyle('Fusion')
    form = CXAGui('cxagui.ui')
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
