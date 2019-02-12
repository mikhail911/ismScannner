""" DOCSTRING """

import os
from time import gmtime, strftime

from PySide2.QtCore import QThread
from PySide2.QtDataVisualization import QtDataVisualization
from PySide2.QtGui import QColor, QGuiApplication, QIcon, QPainter, QTextCursor


class WriteToFile(QThread):
    """ Write text from console to file """

    def __init__(self, parent=None):
        super(WriteToFile, self).__init__(parent)
        self.logging_folder_location = "user_data/logs"
        self.logging_file_name = '' + self.logging_folder_location + '/' +\
                    strftime("%a-%d-%b-%Y-%H-%M-%S", gmtime()) + '.txt'
        self.logging = False

    def enable_logging(self):
        """ Enable logging from console to file """
        self.check_dir_status()
        self.logging = True
        file = open(str(self.logging_file_name), 'w')
        file.write("ISM 2.4GHz Scanner log file, created: " +
                   strftime("%a %d %b %Y %H:%M:%S", gmtime()) + "\n")
        file.write(
            "---------------------------------------------------------\n")
        file.close()

    def write_to_file(self, data):
        """ Write text from console to file """
        if self.logging is True:
            file = open(str(self.logging_file_name), 'a', encoding='utf-8')
            file.write("" + strftime("%a %d %b %Y %H:%M:%S", gmtime()) + " : ")
            file.write(str(data))
            file.write("\n")
            file.close()

    def check_dir_status(self):
        """ Checks if user dir is created, if not create it """
        if not os.path.exists(self.logging_folder_location):
            os.makedirs(self.logging_folder_location)
