""" ISM 2.4GHz Scanner App by Michal Stojke, 2018 """
import datetime
import sys

from PySide2.QtCharts import QtCharts
from PySide2.QtCore import (QCoreApplication, QFile, QObject, QPoint, QSize,
                            Qt, QTranslator, Signal)
from PySide2.QtDataVisualization import QtDataVisualization
from PySide2.QtGui import QColor, QGuiApplication, QIcon, QPainter, QTextCursor
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import (QApplication, QCheckBox, QComboBox, QHBoxLayout,
                               QLineEdit, QListWidget, QMessageBox,
                               QPushButton, QSizePolicy, QTabWidget, QTextEdit,
                               QTimeEdit, QVBoxLayout, QWidget)

import src.make_serial_connection as MakeSerialConnection
# Application imports
import src.read_serial_ports_thread as ReadSerialPortsThread
import src.write_to_database as WriteToDatabase
import src.write_to_file as WriteToFile

QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)

class MainWindow(QObject):
    """ Appliaction GUI """
    current_port_signal = Signal(str)
    current_table = Signal(str)

    def __init__(self, ui_fil, parent=None):
        super(MainWindow, self).__init__(parent)
        self.ui_file = QFile(ui_fil)
        self.ui_file.open(QFile.ReadOnly)
        self.loader = QUiLoader()
        self.loader.setLanguageChangeEnabled(True)
        self.window = self.loader.load(self.ui_file)
        self.window.setGeometry(50, 50, 860, 640)
        self.window.setWindowIcon(QIcon('icons/icons8-wi-fi-64.png'))
        self.ui_file.close()

        self.trans = QTranslator()
        self.trans.load('lang/pl_PL.qm')
        self.conn_baudrates = ["9600", "115200", "300", "1200", "2400",
                               "4800", "14400", "19200", "31250", "38400", "57600"]
        self.conn_boards = ["ESP32", "ESP8266"]

        self.widget_tab = self.window.findChild(QTabWidget, 'tabWidget')
        self.widget_tab.setIconSize(QSize(36, 36))
        self.widget_tab.setTabIcon(0, QIcon('icons/icons8-automatic-64.png'))
        self.widget_tab.setTabIcon(1, QIcon('icons/icons8-bar-chart-50.png'))
        self.widget_tab.setTabIcon(2, QIcon('icons/icons8-menu-64.png'))
        self.widget_tab.setTabIcon(3, QIcon('icons/icons8-timeline-64.png'))
        self.widget_tab.setTabIcon(4, QIcon('icons/icons8-bluetooth-50.png'))
        self.widget_tab.setTabIcon(5, QIcon('icons/icons8-console-64.png'))

        self.lang_combo_box = self.window.findChild(QComboBox, 'lang_combo_box')
        self.lang_combo_box.addItem("English")
        self.lang_combo_box.addItem("Polski")
        self.lang_combo_box.currentTextChanged.connect(self.change_language)
        self.serial_port_box = self.window.findChild(QComboBox, 'serial_port_box')
        self.baud_rate_box = self.window.findChild(QComboBox, 'baud_rate_box')
        self.select_board_box = self.window.findChild(QComboBox, 'select_board_box')
        self.scan_time_edit = self.window.findChild(QTimeEdit, 'scan_time_edit')
        self.wifi_scan_box = self.window.findChild(QCheckBox, 'wifi_scan_box')
        self.blue_scan_box = self.window.findChild(QCheckBox, 'blue_scan_box')
        self.save_data_check = self.window.findChild(QCheckBox, 'save_data_check')
        self.connection_status_edit = self.window.findChild(QLineEdit, 'connection_status_edit')
        self.start_button = self.window.findChild(QPushButton, 'start_button')
        self.stop_button = self.window.findChild(QPushButton, 'stop_button')
        self.stop_button.setEnabled(False)
        self.vertical_wifi_layout = self.window.findChild(QVBoxLayout, 'verticalLayout_5')
        self.wifi_list_view = self.window.findChild(QListWidget, 'wifi_list_view')
        self.wifi_list_view.setIconSize(QSize(64, 64))
        self.vertical_timeline_layout = self.window.findChild(QVBoxLayout, 'verticalLayout_7')
        self.blue_list_view = self.window.findChild(QListWidget, 'blue_list_view')
        self.blue_list_view.setIconSize(QSize(64, 64))
        self.console_logging_check = self.window.findChild(QCheckBox, 'console_logging_check')
        self.console_autoscroll_check = self.window.findChild(QCheckBox, 'console_autoscroll_check')
        self.console_text_edit = self.window.findChild(QTextEdit, 'console_text_edit')

        self.select_board_box.activated[str].connect(self.change_board)

        #Settings tab
        for i in self.conn_baudrates:
            self.baud_rate_box.addItem(i)
        for i in self.conn_boards:
            self.select_board_box.addItem(i)
        self.connection_status_edit.setText('Not connected')
        self.connection_status_edit.setStyleSheet(
            "background: red; color: white; font-size: 14px; border-width: 1px; \
            border-style: solid; border-radius: 2px; border-color: red;")

        thread1 = ReadSerialPortsThread.ReadSerialPortsThread(self)
        thread1.add_serial_port.connect(lambda p: self.serial_port_box.addItem(p))
        thread1.remove_serial_port.connect(lambda p: self.serial_port_box.removeItem(
            self.serial_port_box.findText(p)))
        thread1.start()
        thread2 = MakeSerialConnection.MakeSerialConnection(self)
        thread4 = WriteToDatabase.WriteToDatabase(self)

        self.serial_port_box.currentTextChanged.connect(thread2.get_curr_port)
        self.baud_rate_box.activated[str].connect(thread2.get_curr_baud)
        self.select_board_box.activated[str].connect(thread2.get_curr_board)
        self.scan_time_edit.timeChanged.connect(thread2.get_curr_time)
        self.start_button.clicked.connect(thread2.start)
        self.stop_button.clicked.connect(thread2.stop_serial_communication)
        self.wifi_scan_box.clicked.connect(thread2.get_wifi_check)
        self.blue_scan_box.clicked.connect(thread2.get_blue_check)
        self.save_data_check.clicked.connect(thread2.enable_saving_to_db)
        self.save_data_check.clicked.connect(thread4.enable_saving_data_func)
        self.lang_combo_box.currentTextChanged.connect(lambda s: thread2.get_current_lang(s))

        thread2.baud_box_state.connect(lambda b: self.baud_rate_box.setEnabled(b))
        thread2.port_box_state.connect(lambda b: self.serial_port_box.setEnabled(b))
        thread2.board_box_state.connect(lambda b: self.select_board_box.setEnabled(b))
        thread2.time_edit_state.connect(lambda b: self.scan_time_edit.setEnabled(b))
        thread2.wifi_check_state.connect(lambda b: self.wifi_scan_box.setEnabled(b))
        thread2.blue_check_state.connect(lambda b: self.blue_scan_box.setEnabled(b))
        thread2.serial_port_placeholder.connect(lambda t: self.serial_port_box.addItem(t))
        thread2.serial_port_clear.connect(self.serial_port_box.clear)
        thread2.send_text_signal.connect(lambda t: self.console_text_edit.append(t))
        thread2.start_btn_state.connect(lambda b: self.start_button.setEnabled(b))
        thread2.stop_btn_state.connect(lambda b: self.stop_button.setEnabled(b))
        thread2.conn_stat_text.connect(lambda t: self.connection_status_edit.setText(t))
        thread2.conn_stat_style.connect(lambda s: self.connection_status_edit.setStyleSheet(s))

        #Wi-Fi Chart tab
        self.chart = QtCharts.QChart()
        self.axis_x = QtCharts.QValueAxis()
        self.axis_y = QtCharts.QValueAxis()

        self.line_series = QtCharts.QLineSeries()
        self.line_series.append(QPoint(0, 0))
        self.chart.setAxisX(self.axis_x, self.line_series)
        self.axis_x.setRange(2400, 2483)
        self.axis_x.setTickCount(10)
        self.axis_x.setMinorTickCount(4)
        self.axis_x.applyNiceNumbers()
        self.axis_x.setTitleText("Frequency [MHz]")
        self.chart.setAxisY(self.axis_y, self.line_series)
        self.axis_y.setRange(-100, -30)
        self.axis_y.applyNiceNumbers()
        self.axis_y.setTickCount(9)
        self.axis_y.setMinorTickCount(4)
        self.axis_y.setTitleText("RSSI [dBm]")
        self.chart.legend().setVisible(True)
        self.chart.legend().setAlignment(Qt.AlignRight)
        self.chart.setBackgroundRoundness(0)
        self.chart_view = QtCharts.QChartView(self.chart)
        self.chart_view.setRenderHint(QPainter.Antialiasing)
        self.vertical_wifi_layout.addWidget(self.chart_view)

        #WiFi List tab
        thread2.clear_wifi_list.connect(self.wifi_list_view.clear)
        thread2.append_wifi_list_item.connect(lambda i: self.wifi_list_view.addItem(i))
        thread2.append_wifi_timeline_data.connect(lambda d: self.append_data(d))
        thread2.save_wifi_timeline_data.connect(lambda t: thread4.update_db_file(t))
        thread2.clear_wifi_series.connect(self.chart.removeAllSeries)
        thread2.add_wifi_series.connect(lambda s: self.chart.addSeries(s))
        thread2.set_axis_x_series.connect(lambda s: self.chart.setAxisX(self.axis_x, s))
        thread2.set_axis_y_series.connect(lambda s: self.chart.setAxisY(self.axis_y, s))
        thread2.wifi_data_to_func.connect(lambda d: thread2.append_wifi_data(d))
        thread2.wifi_data_to_func.connect(lambda d: thread2.append_data_to_wifi_graph(d))
        thread2.wifi_data_to_func.connect(lambda d: thread2.append_data_to_wifi_timeline(d))
        thread2.blue_data_to_func.connect(lambda d: thread2.append_blue_data(d))

        #Wi-Fi Timeline tab
        self.wifi_channels_occupancy_array = []
        self.wifi_channels_timestamps = []
        self.deleted_empty_vals = False
        self.freeze_graph_bool_val = False
        self.last_item = 0
        self.graph_item_color = QColor(255, 195, 0)

        self.bars = QtDataVisualization.Q3DBars()
        self.column_axis = QtDataVisualization.QCategory3DAxis()
        self.column_axis.setTitle('Channels')
        self.column_axis.setTitleVisible(True)
        self.column_axis.setLabels(['Channel 1', 'Channel 2', 'Channel 3', 'Channel 4', 'Channel 5',
                                    'Channel 6', 'Channel 7', 'Channel 8', 'Channel 9', 'Channel 10',
                                    'Channel 11', 'Channel 12', 'Channel 13'])
        self.column_axis.setLabelAutoRotation(45)
        self.column_axis.setAutoAdjustRange(True)
        self.row_axis = QtDataVisualization.QCategory3DAxis()
        self.row_axis.setTitle('Timeline')
        self.row_axis.setTitleVisible(True)
        self.value_axis = QtDataVisualization.QValue3DAxis()
        self.value_axis.setTitle('RSSI [dBm]')
        self.value_axis.setTitleVisible(True)
        self.value_axis.setRange(-100, -10)

        self.bars.setRowAxis(self.row_axis)
        self.bars.setColumnAxis(self.column_axis)
        self.bars.setValueAxis(self.value_axis)
        self.bars.setBarSpacingRelative(False)
        self.bars.setFloorLevel(-100)

        self.series = QtDataVisualization.QBar3DSeries()
        self.array_data = [[]]
        self.series.dataProxy().addRows(self.data_to_bar_data_array(self.array_data))
        self.series.setBaseColor(self.graph_item_color)

        self.bars.setPrimarySeries(self.series)
        self.container = QWidget.createWindowContainer(self.bars)

        if not self.bars.hasContext():
            print("Couldn't initialize the OpenGL context")
            sys.exit(-1)

        camera = self.bars.scene().activeCamera()
        camera.setXRotation(-45.0)
        camera.setYRotation(22.5)

        geometry = QGuiApplication.primaryScreen().geometry()
        size = geometry.height() * 3 / 4
        self.container.setMinimumSize(size, size)
        self.container.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.container.setFocusPolicy(Qt.StrongFocus)
        self.append_data([-100, -80, -100, -80, -100, -80, -100, -80, -100, -80, -100, -80, -100])
        self.nav_layout_h = QHBoxLayout()
        self.freeze_check = QCheckBox()
        self.freeze_check.setText("Freeze")
        self.freeze_check.clicked.connect(self.enable_scrolling_data)
        self.freeze_check.stateChanged.connect(self.freeze_graph)
        self.prev_button = QPushButton()
        self.prev_button.setText("Previous")
        self.prev_button.setEnabled(False)
        self.prev_button.clicked.connect(self.previous_data)
        self.next_button = QPushButton()
        self.next_button.setText("Next")
        self.next_button.setEnabled(False)
        self.next_button.clicked.connect(self.next_data)
        self.nav_layout_h.addWidget(self.freeze_check)
        self.nav_layout_h.addWidget(self.prev_button)
        self.nav_layout_h.addWidget(self.next_button)

        self.load_data_check = QCheckBox()
        self.load_data_check.setText("Load archival data")
        self.load_data_check.clicked.connect(self.enable_load_data)
        self.load_data_combo = QComboBox()
        self.load_data_combo.addItem("No data found")
        self.load_data_combo.setEnabled(False)
        self.load_data_btn = QPushButton()
        self.load_data_btn.setText("Load")
        self.load_data_btn.setEnabled(False)
        self.nav_layout_h2 = QHBoxLayout()
        self.nav_layout_h2.addWidget(self.load_data_check)
        self.nav_layout_h2.addWidget(self.load_data_combo)
        self.nav_layout_h2.addWidget(self.load_data_btn)
        thread4.start()
        thread4.remove_defualt_item.connect(lambda: self.load_data_combo.clear())
        thread4.append_available_day.connect(lambda s: self.load_data_combo.addItem(s))
        thread4.send_data_from_database.connect(lambda t: self.append_data_from_database(t))
        self.load_data_combo.currentTextChanged.connect(lambda t: thread4.get_curr_table(t))
        self.load_data_btn.clicked.connect(thread4.load_data_button)

        self.vertical_timeline_layout.addWidget(self.container)
        self.vertical_timeline_layout.addLayout(self.nav_layout_h)
        self.vertical_timeline_layout.addLayout(self.nav_layout_h2)

        #Bluetooth tab
        thread2.clear_blue_list.connect(self.blue_list_view.clear)
        thread2.append_blue_list_item.connect(lambda i: self.blue_list_view.addItem(i))

        #Console tab
        self.console_autoscroll_check.stateChanged.connect(self.enable_auto_scroll)
        thread3 = WriteToFile.WriteToFile(self)
        self.console_logging_check.stateChanged.connect(thread3.enable_logging)
        thread2.send_text_signal.connect(lambda t: thread3.write_to_file(t))

        self.window.show()

    def change_board(self):
        """ Disable Bluetooth scan option if ESP8266 board is selected """
        print(self.select_board_box.currentText())
        if self.select_board_box.currentText() == "ESP8266":
            self.blue_scan_box.setEnabled(False)
        elif self.select_board_box.currentText() == "ESP32":
            self.blue_scan_box.setEnabled(True)

    def enable_auto_scroll(self):
        """ Enable scrolling in text console """
        if self.console_autoscroll_check.checkState() == Qt.Checked:
            self.console_text_edit.moveCursor(QTextCursor.End)
        else:
            self.console_text_edit.moveCursor(QTextCursor.Start)

    def freeze_graph(self, state):
        """ Stop showing live data in 3d Wi-Fi graph """
        if state == 2:
            self.freeze_graph_bool_val = True
        else:
            self.freeze_graph_bool_val = False

    def data_to_bar_data_row(self, data):
        """ DOCSTRING """
        return list(QtDataVisualization.QBarDataItem(d) for d in data)

    def data_to_bar_data_array(self, data):
        """ DOCSTRING """
        return list(self.data_to_bar_data_row(row) for row in data)

    def append_data(self, data):
        """ DOCSTRING """
        self.wifi_channels_occupancy_array.append(data)
        self.wifi_channels_timestamps.append(str(datetime.datetime.now()))
        self.update_graph()

    def update_graph(self):
        """ DOCSTRING """
        if len(self.wifi_channels_occupancy_array) < 10:
            missing_vals = 10 - len(self.wifi_channels_occupancy_array)
            for z in range(missing_vals):
                self.wifi_channels_occupancy_array.append(
                    [-100, -100, -100, -100, -100, -100, -100, -100, -100, -100, -100, -100, -100])
                self.wifi_channels_timestamps.append("")
            self.print_freshes_ten()

        elif len(self.wifi_channels_occupancy_array) > 20 and self.deleted_empty_vals is False:
            for y in range(self.wifi_channels_occupancy_array.count(
                    [-100, -100, -100, -100, -100, -100, -100, -100, -100, -100, -100, -100,
                     -100])):
                self.wifi_channels_occupancy_array.remove(
                    [-100, -100, -100, -100, -100, -100, -100, -100, -100, -100, -100, -100, -100])
                self.wifi_channels_timestamps.remove("")
                self.deleted_empty_vals = True
                self.print_freshes_ten()
        else:
            self.print_freshes_ten()

    def previous_data(self):
        """ DOCSTRING """
        if self.last_item < 9 and len(self.wifi_channels_occupancy_array) < 9:
            QMessageBox.warning(self.window, 'ISM 2.4GHz Scanner - Warning',
                                "To few information to rewind!", QMessageBox.Ok)
        elif self.last_item < 9:
            print('out of range')
            QMessageBox.warning(self.window, 'ISM 2.4GHz Scanner - Warning',
                                "No more data to rewind!", QMessageBox.Ok)
        else:
            temp_array = []
            temp_timestamp_array = []
            if self.last_item - 9 < 0:
                print('out of range')
                QMessageBox.warning(self.window, 'ISM 2.4GHz Scanner - Warning',
                                    "No more data to rewind!", QMessageBox.Ok)
            else:
                for x in range(self.last_item - 10, self.last_item - 1):
                    temp_array.append(self.wifi_channels_occupancy_array[x])
                    temp_timestamp_array.append(self.wifi_channels_timestamps[x])
                self.last_item = self.last_item - 9
                self.row_axis.setLabels(temp_timestamp_array)
                self.series.dataProxy().resetArray()
                self.series.dataProxy().addRows(self.data_to_bar_data_array(temp_array))

    def next_data(self):
        """ DOCSTRING """
        if self.last_item < 9 and len(self.wifi_channels_occupancy_array) < 9:
            QMessageBox.warning(self.window, 'ISM 2.4GHz Scanner - Warning',
                                "To few information to rewind!", QMessageBox.Ok)
        elif self.last_item > len(self.wifi_channels_occupancy_array):
            print('out of range')
            QMessageBox.warning(self.window, 'ISM 2.4GHz Scanner - Warning',
                                "No more data to rewind!", QMessageBox.Ok)
        else:
            temp_array = []
            temp_timestamp_array = []
            if self.last_item + 9 > len(self.wifi_channels_occupancy_array):
                print('out of range')
                QMessageBox.warning(self.window, 'ISM 2.4GHz Scanner - Warning',
                                    "No more data to rewind!", QMessageBox.Ok)
            else:
                for x in range(self.last_item + 1, self.last_item + 10):
                    temp_array.append(self.wifi_channels_occupancy_array[x])
                    temp_timestamp_array.append(self.wifi_channels_timestamps[x])

                self.last_item = self.last_item + 9
                self.row_axis.setLabels(temp_timestamp_array)
                self.series.dataProxy().resetArray()
                self.series.dataProxy().addRows(self.data_to_bar_data_array(temp_array))

    def print_freshes_ten(self):
        """ DOCSTRING """
        if self.freeze_graph_bool_val is False:
            i = 0
            temp_array = []
            temp_timestamp_array = []
            self.last_item = 0
            for x in range(len(self.wifi_channels_occupancy_array) - 1):
                if i < 10:
                    temp_array.append(self.wifi_channels_occupancy_array[len(
                        self.wifi_channels_occupancy_array) - x - 1])
                    temp_timestamp_array.append(self.wifi_channels_timestamps[len(
                        self.wifi_channels_timestamps) - x -1])
                    i += 1
                elif i == 10:
                    self.last_item = len(self.wifi_channels_occupancy_array) - 10
                    i += 1

            self.row_axis.setLabels(temp_timestamp_array)
            self.series.dataProxy().resetArray()
            self.series.dataProxy().addRows(self.data_to_bar_data_array(temp_array))

    def enable_scrolling_data(self, state):
        """ DOCSTRING """
        if state is True:
            self.prev_button.setEnabled(True)
            self.next_button.setEnabled(True)
        else:
            self.prev_button.setEnabled(False)
            self.next_button.setEnabled(False)

    def enable_load_data(self, state):
        """ DOCSTRING """
        if state is True:
            self.load_data_combo.setEnabled(True)
            if (self.load_data_combo.findText("No data found") == -1 or
                    self.load_data_combo.findText("Nie znaleziono danych")):
                self.load_data_btn.setEnabled(True)
        else:
            self.load_data_combo.setEnabled(False)
            self.load_data_btn.setEnabled(False)
            self.wifi_channels_occupancy_array = []
            self.wifi_channels_timestamps = []
            self.print_freshes_ten()

    def change_language(self, lang):
        """ DOCSTRING """
        if lang == "Polski":
            QCoreApplication.installTranslator(self.trans)
            self.axis_x.setTitleText("Częstotliwość [MHz]")
            self.freeze_check.setText("Zamróź")
            self.load_data_check.setText("Otwórz dane archiwalne")
            self.load_data_combo.removeItem(self.load_data_combo.findText("No data found"))
            self.load_data_combo.addItem("Nie znaleziono danych")
            self.load_data_btn.setText("Otwórz")
            self.next_button.setText("Następny")
            self.prev_button.setText("Poprzedni")
            self.column_axis.setTitle('Kanały')
            self.column_axis.setLabels(['Kanał 1', 'Kanał 2', 'Kanał 3', 'Kanał 4', 'Kanał 5',
                                        'Kanał 6', 'Kanał 7', 'Kanał 8', 'Kanał 9', 'Kanał 10',
                                        'Kanał 11', 'Kanał 12', 'Kanał 13'])
            self.row_axis.setTitle('Oś czasu')
            self.bars.setColumnAxis(self.column_axis)
            self.bars.setRowAxis(self.row_axis)
        else:
            QCoreApplication.removeTranslator(self.trans)
            self.axis_x.setTitleText("Frequency [MHz]")
            self.freeze_check.setText("Freeze")
            self.load_data_check.setText("Load archival data")
            self.load_data_combo.removeItem(self.load_data_combo.findText("Nie znaleziono danych"))
            self.load_data_combo.addItem("No data found")
            self.load_data_btn.setText("Load")
            self.next_button.setText("Next")
            self.prev_button.setText("Previous")
            self.column_axis.setTitle('Channels')
            self.column_axis.setLabels(['Channel 1', 'Channel 2', 'Channel 3', 'Channel 4',
                                        'Channel 5', 'Channel 6', 'Channel 7', 'Channel 8',
                                        'Channel 9', 'Channel 10', 'Channel 11', 'Channel 12',
                                        'Channel 13'])
            self.row_axis.setTitle('Timeline')
            self.bars.setColumnAxis(self.column_axis)
            self.bars.setRowAxis(self.row_axis)

    def append_data_from_database(self, data):
        """ DOCSTRING !!! """
        self.wifi_channels_occupancy_array = []
        self.wifi_channels_timestamps = []
        self.print_freshes_ten()

        for row in data:
            itm_nmbr = 0
            self.temp_db_array = []
            for item in row:
                if itm_nmbr == 1:
                    self.wifi_channels_timestamps.append("" + str(
                        self.load_data_combo.currentText()) + " " + item + "")
                elif itm_nmbr > 1:
                    self.temp_db_array.append(item)
                itm_nmbr += 1
            self.wifi_channels_occupancy_array.append(self.temp_db_array)
        self.print_freshes_ten()

if __name__ == '__main__':
    APP = QApplication(sys.argv)
    FORM = MainWindow('ism_scanner.ui')
    sys.exit(APP.exec_())
