""" DOCSTRING """
import datetime

import serial
import serial.tools.list_ports
from PySide2.QtCharts import QtCharts
from PySide2.QtCore import QEventLoop, QPoint, QThread, QTimer, Signal, Slot
from PySide2.QtWidgets import QListWidgetItem
from PySide2.QtGui import QIcon

# Application imports
import src.get_manufacturer as manu

class MakeSerialConnection(QThread):
    """ Connect to selected serial port, receive data and send it to proper tabs """
    start_btn_state = Signal(bool)
    stop_btn_state = Signal(bool)
    baud_box_state = Signal(bool)
    port_box_state = Signal(bool)
    board_box_state = Signal(bool)
    time_edit_state = Signal(bool)
    wifi_check_state = Signal(bool)
    blue_check_state = Signal(bool)
    serial_port_placeholder = Signal(str)
    serial_port_clear = Signal()
    send_text_signal = Signal(str)
    conn_stat_text = Signal(str)
    conn_stat_style = Signal(str)
    clear_wifi_list = Signal()
    clear_blue_list = Signal()
    append_wifi_list_item = Signal(QListWidgetItem)
    append_blue_list_item = Signal(QListWidgetItem)
    append_wifi_timeline_data = Signal(list)
    save_wifi_timeline_data = Signal(tuple)
    clear_wifi_series = Signal()
    add_wifi_series = Signal(QtCharts.QLineSeries)
    set_axis_y_series = Signal(QtCharts.QLineSeries)
    set_axis_x_series = Signal(QtCharts.QLineSeries)
    wifi_data_to_func = Signal(dict)
    wifi_data_to_func_graph = Signal(dict)
    wifi_data_to_func_time = Signal(dict)
    blue_data_to_func = Signal(dict)

    def __init__(self, parent=None):
        super(MakeSerialConnection, self).__init__(parent)
        self.current_port = ''
        self.current_baud = 9600
        self.current_board = 'ESP32'
        self.current_time = 10000
        self.wifi_scan_status = True
        self.blue_scan_status = False
        self.first_conn = True
        self.arduino = ''
        self.loop = ''
        self.reading = True
        self.data_collection = False
        self.blue_data_collection = False
        self.collected_data = {}
        self.collected_blue_data = {}
        self.default_array = []
        self.default_tupple = ()
        self.final_tuple = ()
        self.save_data_to_db = False
        self.channels_occ = {
            1: [1, 2],
            2: [1, 2, 3],
            3: [2, 3, 4],
            4: [3, 4, 5],
            5: [4, 5, 6],
            6: [5, 6, 7],
            7: [6, 7, 8],
            8: [7, 8, 9],
            10: [9, 10, 11],
            11: [10, 11, 12],
            12: [11, 12, 13],
            13: [12, 13]
        }
        self.current_lang = 'English'

    def run(self):
        """ DOCSTRING """
        if self.first_conn is True:
            self.arduino = serial.Serial(self.current_port, self.current_baud, write_timeout=1)
            self.disable_settings_options(False)
            self.send_config_to_esp()
        else:
            self.show_status_reconnect()
            self.disable_settings_options(False)
            self.loop = QEventLoop()
            QTimer.singleShot(5000, self.loop.quit)
            self.loop.exec_()
            self.arduino = serial.Serial(self.current_port, self.current_baud, write_timeout=1)
            self.send_config_to_esp()
            self.reading = True

        while self.reading is True:
            self.show_status_connected()
            try:
                data = self.arduino.readline()[:-1].decode(encoding='utf-8', errors="replace")
                if data.split() == ['[CFG]BOARD_ERROR']:
                    self.show_status_wrong_board()
                    self.send_text_signal.emit(
                        'Selected wrong board! Disconnected')
                    self.stop_serial_communication()
                if data.split() == ['[SCN]WIFI_START_SCAN'] or self.data_collection is True:
                    if self.data_collection is True and data.split() != ['[SCN]WIFI_STOP_SCAN']:
                        if len(data) > 1:
                            self.collected_data[str(data.split(" | ")[1])] = [
                                int(data.split(" | ")[2]),
                                int(data.split(" | ")[3]),
                                str(data.split(" | ")[4]),
                                str(data.split(" | ")[5]),
                                str(data.split(" | ")[6])]
                    elif data.split() == ['[SCN]WIFI_STOP_SCAN']:
                        self.data_collection = False
                        self.wifi_data_to_func.emit(self.collected_data)
                    else:
                        self.collected_data = {}
                        self.data_collection = True
                if data.split() == ['[SCN]BLUE_START_SCAN'] or self.blue_data_collection is True:
                    if (self.blue_data_collection is True and data.split() !=
                            ['[SCN]BLUE_STOP_SCAN']):
                        if data.split()[0] == 'DEV':
                            if len(data) > 1:
                                # Data template: DEV | Name | RSSI | MAC | MSG
                                self.collected_blue_data[str(data.split(" | ")[1])] = [
                                    str(data.split(" | ")[2]),
                                    int(data.split(" | ")[3]),
                                    str(data.split(" | ")[4])]
                    elif data.split() == ['[SCN]BLUE_STOP_SCAN']:
                        self.blue_data_collection = False
                        self.blue_data_to_func.emit(self.collected_blue_data)
                    else:
                        self.blue_data_collection = True
                self.send_text_signal.emit(data)

            except serial.SerialException:
                self.show_status_uart_error()
                self.send_text_signal.emit(
                    'Disconnect of USB->UART occured.\nRestart needed!')
                self.stop_serial_communication()
        self.arduino.close()

    def send_config_to_esp(self):
        """send config to ESP"""
        self.arduino.write("[CFG]START".encode())
        self.arduino.write("\n".encode())
        self.arduino.write(str("[CFG]BOARD="+self.current_board+"").encode())
        self.arduino.write("\n".encode())
        self.arduino.write(str("[CFG]TIME="+str(self.current_time)+"").encode())
        self.arduino.write("\n".encode())
        self.arduino.write(str("[CFG]WIFI_SCAN="+str(self.wifi_scan_status).upper()+"").encode())
        self.arduino.write("\n".encode())
        self.arduino.write(str("[CFG]BLUE_SCAN="+str(self.blue_scan_status).upper()+"").encode())
        self.arduino.write("\n".encode())
        self.arduino.write("[CFG]STOP\n".encode())
        self.arduino.write("\n".encode())
        self.arduino.write("[SCN]START".encode())
        self.arduino.write("\n".encode())

    def stop_serial_communication(self):
        """ Stop reading from serial port """
        self.reading = False
        self.first_conn = False
        self.arduino.close()
        self.disable_settings_options(True)
        self.show_status_disconnected()

    def get_curr_port(self, port):
        """ Get selected serial port """
        self.current_port = str(port)

    def get_curr_baud(self, baud):
        """ DOCSTRING """
        self.current_baud = int(baud)

    def get_curr_board(self, board):
        """ DOCSTRING """
        self.current_board = str(board)

    def get_curr_time(self, user_time):
        """ DOCSTRING """
        self.current_time = (int(user_time.toString("m:ss").split(":")[0]) * 60 +
                             int(user_time.toString("m:ss").split(":")[1])) * 1000

    def get_wifi_check(self, state):
        """ DOCSTRING """
        self.wifi_scan_status = state

    def get_blue_check(self, state):
        """ DOCSTRING """
        self.blue_scan_status = state

    def set_style_sheet(self, color):
        """ Set stylesheet for connection status label """

        return "background: " + color + "; color: white; font-size: 14px; border-width: 1px; \
            border-style: solid; border-radius: 2px; border-color: " + color + ";"

    def show_status_connected(self):
        """ Show connected status in MainWindow class """
        self.start_btn_state.emit(False)
        self.stop_btn_state.emit(True)
        if self.current_lang == "Polski":
            self.conn_stat_text.emit('Połączono')
        else:
            self.conn_stat_text.emit('Connected')
        self.conn_stat_style.emit(self.set_style_sheet('green'))

    def show_status_disconnected(self):
        """ Show disconnected status in MainWindow class """
        self.start_btn_state.emit(True)
        self.stop_btn_state.emit(False)
        if self.current_lang == "Polski":
            self.conn_stat_text.emit('Rozłączono')
        else:
            self.conn_stat_text.emit('Disconnected')
        self.conn_stat_style.emit(self.set_style_sheet('red'))

    def show_status_uart_error(self):
        """ Show UART error status in MainWindow """
        self.start_btn_state.emit(False)
        self.stop_btn_state.emit(True)
        if self.current_lang == "Polski":
            self.conn_stat_text.emit(
                'Rozłączono. Wymagany restart')
        else:
            self.conn_stat_text.emit(
                'Disconnect of USB->UART occured. Need restart')
        self.conn_stat_style.emit(self.set_style_sheet('orange'))

    def show_status_wrong_board(self):
        """ Show selected wrong board status in MainWindow """
        self.start_btn_state.emit(False)
        self.stop_btn_state.emit(True)
        if self.current_lang == "Polski":
            self.conn_stat_text.emit('Wybrano złą płytkę!')
        else:
            self.conn_stat_text.emit('Selected wrong board!')
        self.conn_stat_style.emit(self.set_style_sheet('red'))

    def show_status_reconnect(self):
        """ Show reconnect status in MainWindow """
        self.start_btn_state.emit(False)
        self.stop_btn_state.emit(False)
        if self.current_lang == "Polski":
            self.conn_stat_text.emit('Ponowne łączenie... Czekaj 5s')
        else:
            self.conn_stat_text.emit('Reconnecting... Wait 5s')
        self.conn_stat_style.emit(self.set_style_sheet('orange'))

    @Slot(dict)
    def append_wifi_data(self, data):
        """ Append data to list in WiFi list tab """
        self.clear_wifi_list.emit()
        i = 1
        for i in data:
            if self.current_lang == "Polski":
                item = QListWidgetItem('BSID: '+str(i)+' \nKanał: '+str(
                    data[i][1])+' \nRSSI: '+str(data[i][0])+' dBm \nMAC: '+str(data[i][3])+
                                   ' (Producent: '+str(
                                       manu.search_manufacturer_by_mac(str(data[i][3])))+')')
            else:
                item = QListWidgetItem('BSID: '+str(i)+' \nChannel: '+str(
                    data[i][1])+' \nRSSI: '+str(data[i][0])+' dBm \nMAC: '+str(data[i][3])+
                                   ' (Manufacturer: '+str(
                                       manu.search_manufacturer_by_mac(str(data[i][3])))+')')
            if int(abs(data[i][0])) < 50:
                item.setIcon(QIcon('icons/icons8-no-connection-64-green.png'))
            elif int(abs(data[i][0])) >= 50 and int(abs(data[i][0])) < 70:
                item.setIcon(QIcon('icons/icons8-no-connection-64-blue.png'))
            elif int(abs(data[i][0])) >= 70 and int(abs(data[i][0])) < 80:
                item.setIcon(QIcon('icons/icons8-no-connection-64-orange.png'))
            elif int(abs(data[i][0])) >= 80 and int(abs(data[i][0])) < 90:
                item.setIcon(QIcon('icons/icons8-no-connection-64-red.png'))
            elif int(abs(data[i][0])) >= 90:
                item.setIcon(QIcon('icons/icons8-no-connection-64-black.png'))
            self.append_wifi_list_item.emit(item)
            self.loop = QEventLoop()
            QTimer.singleShot(50, self.loop.quit)
            self.loop.exec_()

    @Slot(dict)
    def append_blue_data(self, data):
        """ DOCSTRING """
        self.clear_blue_list.emit()
        i = 1
        for i in data:
            if self.current_lang == "Polski":
                item = QListWidgetItem('Nazwa: ' + str(i) + ' \nMAC: ' + str(data[i][0].upper()) +
                                   ' \nRSSI: '+str(data[i][1]) + ' dBm\nProducent: ' +
                                   str(manu.search_manufacturer_by_mac(str(data[i][0].upper())))
                                   + '')
            else:
                item = QListWidgetItem('Name: ' + str(i) + ' \nMAC: ' + str(data[i][0].upper()) +
                                   ' \nRSSI: '+str(data[i][1]) + ' dBm\nManufacturer: ' +
                                   str(manu.search_manufacturer_by_mac(str(data[i][0].upper())))
                                   + '')
            if int(abs(data[i][1])) < 50:
                item.setIcon(QIcon('icons/icons8-no-connection-64-green.png'))
            elif int(abs(data[i][1])) >= 50 and int(abs(data[i][1])) < 70:
                item.setIcon(QIcon('icons/icons8-no-connection-64-blue.png'))
            elif int(abs(data[i][1])) >= 70 and int(abs(data[i][1])) < 80:
                item.setIcon(QIcon('icons/icons8-no-connection-64-orange.png'))
            elif int(abs(data[i][1])) >= 80 and int(abs(data[i][1])) < 90:
                item.setIcon(QIcon('icons/icons8-no-connection-64-red.png'))
            elif int(abs(data[i][1])) >= 90:
                item.setIcon(QIcon('icons/icons8-no-connection-64-black.png'))
            self.append_blue_list_item.emit(item)
            self.loop = QEventLoop()
            QTimer.singleShot(50, self.loop.quit)
            self.loop.exec_()

    def disable_settings_options(self, state):
        """ DOCSTRING """
        self.port_box_state.emit(state)
        self.baud_box_state.emit(state)
        self.board_box_state.emit(state)
        self.time_edit_state.emit(state)
        self.wifi_check_state.emit(state)
        self.blue_check_state.emit(state)
        if state is False:
            self.serial_port_placeholder.emit(self.current_port)
        else:
            self.serial_port_clear.emit()

    @Slot(dict)
    def append_data_to_wifi_graph(self, wifi_dict):
        """DOCSTRING"""
        self.clear_wifi_series.emit()
        for var_x in wifi_dict:
            self.line_series = QtCharts.QLineSeries()
            self.line_series.setName(str(var_x))
            self.line_series.append(
                QPoint(2400+(wifi_dict[var_x][1]*5-4), -100))
            self.line_series.append(
                QPoint(2411+(wifi_dict[var_x][1]*5-9), int(wifi_dict[var_x][0])))
            self.line_series.append(
                QPoint(2411+(wifi_dict[var_x][1]*5+1), int(wifi_dict[var_x][0])))
            self.line_series.append(
                2422+(wifi_dict[var_x][1]*5-4), -100)
            self.add_wifi_series.emit(self.line_series)
            self.set_axis_x_series.emit(self.line_series)
            self.set_axis_y_series.emit(self.line_series)
            self.loop = QEventLoop()
            QTimer.singleShot(50, self.loop.quit)
            self.loop.exec_()

    @Slot(dict)
    def append_data_to_wifi_timeline(self, wifi_dict):
        """ DOCSTRING """
        self.default_array = [-100, -100, -100, -100, -100, -100, -100, -100, -100, -100, -100,
                              -100, -100]
        for var_x in wifi_dict:
            self.append_lowest_rssi_to_array(wifi_dict[var_x][1], wifi_dict[var_x][0])
        self.append_wifi_timeline_data.emit(self.default_array)
        self.default_tupple = tuple(self.default_array)
        self.final_tuple = (datetime.datetime.now().strftime('%H:%M:%S'), *self.default_tupple)
        self.save_wifi_timeline_data.emit(self.final_tuple)
        self.loop = QEventLoop()
        QTimer.singleShot(50, self.loop.quit)
        self.loop.exec_()

    def append_lowest_rssi_to_array(self, x, value):
        """ DOCSTRING """
        for i in self.channels_occ[int(x)]:
            if self.default_array[i-1] < value:
                self.default_array[i-1] = value

    def enable_saving_to_db(self, state):
        """ DOCSTRING """
        if state is True:
            self.save_data_to_db = True
        else:
            self.save_data_to_db = False

    def get_current_lang(self, lang):
        """ DOCSTRING """
        self.current_lang = lang
