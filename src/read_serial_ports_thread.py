""" DOCSTRING """
from sys import platform as _platform

import serial
import serial.tools.list_ports
from PySide2.QtCore import QEventLoop, QThread, QTimer, Signal


class ReadSerialPortsThread(QThread):
    """ Find connected serial ports and send it to GUI """
    add_serial_port = Signal(str)
    remove_serial_port = Signal(str)

    def __init__(self, parent=None):
        QThread.__init__(self, parent)
        self.current_port = ''
        self.result = []
        self.loop = ""

        if _platform.startswith('linux'):
            self.ports = ['/dev/ttyS%s' % (i + 1) for i in range(256)]
        elif _platform.startswith('win32'):
            self.ports = ['COM%s' % (i + 1) for i in range(256)]
        elif _platform.startswith('darwin'):
            self.ports = ['/dev/cu.serial%s' % (i + 1) for i in range(256)]

    def run(self):
        """ DOCSTRING """
        while True:
            for port in self.ports:
                if port in self.result:
                    try:
                        serial_conn = serial.Serial(port)
                        serial_conn.close()
                    except(OSError, serial.SerialException):
                        if port != self.current_port:
                            self.result.remove(port)
                            self.remove_serial_port.emit(port)
                else:
                    try:
                        serial_conn = serial.Serial(port)
                        serial_conn.close()
                        if port not in self.result:
                            self.result.append(port)
                            self.add_serial_port.emit(port)
                    except (OSError, serial.SerialException):
                        pass
            self.loop = QEventLoop()
            QTimer.singleShot(50, self.loop.quit)
            self.loop.exec_()

