# -*- coding: utf-8 -*-

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QMessageBox, QDialog, QWidget

import config
from build_retrieval_model import load_index_in_disk, find_passages_for_query, Page, Index


class Ui_MainWindow():
    _ADMIN_LEVEL = 3
    _access_level = 0
    _level_dict = {0: "访客", 1: "学生", 2: "老师", 3: "管理员"}
    _password_dict = {0: "000", 1: "111", 2: "222", 3: "333"}
    handled_passages_dict, invert_index = load_index_in_disk(config.HANDLED_PASSAGES_FILE_PATH, config.INDEX_FILE_PATH,
                                                             config.PASSAGES_CONFIG_PATH)

    def access_click(self, value, window):
        password = self.text_edit.toPlainText()
        if self._password_dict[value] == password or value == 0:
            self._access_level = value
            QMessageBox.information(window, "密码正确", "您的身份是" + self._level_dict[value], QMessageBox.Yes)
        else:
            self._access_level = 0
            QMessageBox.information(window, "密码错误", "请检查你输入的密码", QMessageBox.Yes)

    def search_click(self):
        query = self.text_edit.toPlainText()
        results_with_score = find_passages_for_query(query=query, handled_passages_dict=self.handled_passages_dict,
                                                     invert_index=self.invert_index)
        results = []
        for result_with_score in results_with_score:
            temp_result = self.handled_passages_dict[result_with_score[0]]
            if temp_result.id < (self._access_level + 1) * 300 or self._access_level == self._ADMIN_LEVEL:
                results.append(temp_result)
        header_labels = ["id", "内容"]
        table_model = QStandardItemModel(len(results), len(header_labels))
        table_model.setHorizontalHeaderLabels(header_labels)
        for row_ind, row_result in enumerate(results):
            id_item = QStandardItem(str(row_result.id))
            text_item = QStandardItem("\n".join(row_result.text))
            table_model.setItem(row_ind, 0, id_item)
            table_model.setItem(row_ind, 1, text_item)
        self.table_view.setModel(table_model)
        self.table_view.horizontalHeader().setStretchLastSection(True)

    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 600)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.teacher_button = QtWidgets.QPushButton(self.centralwidget)
        self.teacher_button.setGeometry(QtCore.QRect(80, 0, 93, 28))
        self.teacher_button.setObjectName("teacher_button")
        self.teacher_button.clicked.connect(lambda: self.access_click(2, window=MainWindow))
        self.student_button = QtWidgets.QPushButton(self.centralwidget)
        self.student_button.setGeometry(QtCore.QRect(260, 0, 93, 28))
        self.student_button.setObjectName("student_button")
        self.student_button.clicked.connect(lambda: self.access_click(1, window=MainWindow))
        self.admin_button = QtWidgets.QPushButton(self.centralwidget)
        self.admin_button.setGeometry(QtCore.QRect(430, 0, 93, 28))
        self.admin_button.setObjectName("admin_button")
        self.admin_button.clicked.connect(lambda: self.access_click(3, window=MainWindow))
        self.guest_button = QtWidgets.QPushButton(self.centralwidget)
        self.guest_button.setGeometry(QtCore.QRect(570, 0, 93, 28))
        self.guest_button.setObjectName("guest_button")
        self.guest_button.clicked.connect(lambda: self.access_click(0, window=MainWindow))
        self.search_button = QtWidgets.QPushButton(self.centralwidget)
        self.search_button.setGeometry(QtCore.QRect(500, 80, 93, 28))
        self.search_button.setObjectName("search_button")
        self.search_button.clicked.connect(self.search_click)
        self.table_view = QtWidgets.QTableView(self.centralwidget)
        self.table_view.setGeometry(QtCore.QRect(30, 130, 721, 421))
        self.table_view.setObjectName("tableView")
        self.text_edit = QtWidgets.QTextEdit(self.centralwidget)
        self.text_edit.setGeometry(QtCore.QRect(310, 80, 131, 31))
        self.text_edit.setObjectName("textEdit")
        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "研究生院检索系统"))
        MainWindow.setWhatsThis(_translate("MainWindow", "<html><head/><body><p><br/></p></body></html>"))
        self.teacher_button.setText(_translate("MainWindow", "老师"))
        self.student_button.setText(_translate("MainWindow", "学生"))
        self.admin_button.setText(_translate("MainWindow", "管理员"))
        self.guest_button.setText(_translate("MainWindow", "访客"))
        self.search_button.setText(_translate("MainWindow", "确认检索"))


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    main_window = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(main_window)
    main_window.show()
    sys.exit(app.exec_())
