# -*- coding: utf-8 -*-
import sys
from PyQt5.QtWidgets import QApplication
from .interface.main_window import MainWindow

def main():
    appQt = QApplication(sys.argv)
    resolution = appQt.desktop().screenGeometry()
    appQt.processEvents()

    window = MainWindow(resolution)
    window.show()

    appQt.exec_()
