""" DOCSTRING """
import datetime
import os
import sqlite3
from sqlite3 import Error

from PySide2.QtCore import QThread, QTimer, Signal


class WriteToDatabase(QThread):
    """ DOCSTRING """
    append_available_day = Signal(str)
    remove_defualt_item = Signal()
    send_data_from_database = Signal(list)

    def __init__(self, parent=None):
        super(WriteToDatabase, self).__init__(parent)
        self.database_folder_location = "user_data/database"
        self.database_default_name = "user_db.db"
        self.table_name = "`"+str(datetime.datetime.today().strftime('%Y_%m_%d'))+"`"
        self.enable_writing_to_db = False
        self.selected_table = ""

    def connect_to_database(self, file_name):
        """ Function which connect to database or create empty database file if file not exist. """
        try:
            connection = sqlite3.connect(file_name)
            return connection
        except Error as err_msg:
            print(err_msg)
        return None

    def create_table(self, connection, table_name):
        """ Function which create table in database """
        sql_table = """ CREATE TABLE IF NOT EXISTS {} (
                                        id integer PRIMARY KEY AUTOINCREMENT,
                                        time text,
                                        channel_1 integer,
                                        channel_2 integer,
                                        channel_3 integer,
                                        channel_4 integer,
                                        channel_5 integer,
                                        channel_6 integer,
                                        channel_7 integer,
                                        channel_8 integer,
                                        channel_9 integer,
                                        channel_10 integer,
                                        channel_11 integer,
                                        channel_12 integer,
                                        channel_13 integer
                                    ); """.format(table_name)
        try:
            sql_con = connection.cursor()
            sql_con.execute(sql_table)
        except Error as err_msg:
            print(err_msg)

    def insert_data_into_table(self, connection, table_name, items):
        """ DOCSTRING """
        sql_query = """ INSERT INTO {} (`time`,`channel_1`,`channel_2`,
                    `channel_3`,`channel_4`,`channel_5`,`channel_6`,`channel_7`,`channel_8`,
                    `channel_9`,`channel_10`,`channel_11`,`channel_12`,`channel_13`)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?) """.format(table_name)
        try:
            sql_con = connection
            sql_con.cursor().execute(sql_query, items)
            sql_con.commit()
        except Error as err_msg:
            print(err_msg)

    def enable_saving_data_func(self, state):
        """DOCSTRING"""
        if not os.path.exists(self.database_folder_location):
            os.makedirs(self.database_folder_location)
        if state is True:
            self.enable_writing_to_db = True
            sql_conn = self.connect_to_database("" + self.database_folder_location + "/" +
                                                self.database_default_name + "")
            if sql_conn is not None:
                self.create_table(sql_conn, str(self.table_name))
                self.run()

    def update_db_file(self, data):
        """DOCSTRING"""
        if self.enable_writing_to_db is True:
            sql_conn = self.connect_to_database("" + self.database_folder_location + "/" +
                                                self.database_default_name + "")
            if sql_conn is not None:
                if "`"+str(datetime.datetime.today().strftime('%Y_%m_%d'))+"`" != self.table_name:
                    self.create_table(sql_conn, "`" +
                                      str(datetime.datetime.today().strftime('%Y_%m_%d')) + "`")
                    self.table_name = "`"+ str(datetime.datetime.today().strftime('%Y_%m_%d')) +"`"
                    self.run()
                self.insert_data_into_table(sql_conn, str(self.table_name), data)

    def run(self):
        """ DOCSTRING """
        if self.enable_writing_to_db is True:
            sql_conn = self.connect_to_database("" + self.database_folder_location + "/" +
                                                self.database_default_name + "")
            if sql_conn is not None:
                cursor = sql_conn.cursor().execute(
                    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
                available_tables = (cursor.fetchall())
                self.remove_defualt_item.emit()
                for item in available_tables:
                    if "".join(item) != "sqlite_sequence":
                        self.append_available_day.emit(str("".join(item).replace("_", "-")))

    def get_curr_table(self, table_name):
        """ Get current table name """
        self.selected_table = "`"+str(table_name).replace("-", "_")+"`"

    def load_data_button(self):
        """ Read data from database """
        sql_conn = self.connect_to_database("" + self.database_folder_location + "/" +
                                            self.database_default_name + "")
        sql_query = """ SELECT * FROM {} ORDER BY `_rowid_` ASC """.format(self.selected_table)

        if sql_conn is not None:
            cursor = sql_conn.cursor().execute(sql_query)
            rows = cursor.fetchall()
            self.send_data_from_database.emit(rows)
