import sys
from typing import Optional

from PyQt6 import uic
from PyQt6.QtCore import pyqtSlot, QSettings, Qt
from PyQt6.QtGui import QAction, QIcon, QCursor, QPixmap
from PyQt6.QtWidgets import QMainWindow, QLineEdit, QPlainTextEdit, QComboBox, QPushButton, QTableWidget, \
    QApplication, QFileDialog, QSplashScreen, QTabWidget, QTableWidgetItem, QHeaderView

import DDDAwrapper
import Storage
from Pers import Pers


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dddasav: Optional[QLineEdit] = None
        self.xml: Optional[QPlainTextEdit] = None
        self.main: Optional[QTabWidget] = None
        self.pers: Optional[QComboBox] = None
        self.pers_commit: Optional[QPushButton] = None
        self.person: Optional[Pers] = None
        self.items: Optional[QTableWidget]
        self.actionOpen: Optional[QAction] = None
        self.actionSave: Optional[QAction] = None
        self.actionSavex: Optional[QAction] = None
        self.storage: Optional[Storage.Storage] = None
        self.diffs: Optional[QTableWidget] = None
        uic.loadUi("DDDAedit.ui", self)
        self.wrapper = DDDAwrapper.DDDAwrapper(self)
        self.wrapper.data_changed.connect(self.on_wrapper_data_changed)
        self.diffs.setHorizontalHeaderLabels(['Line', 'Original', 'Current'])
        self.diffs.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.diffs.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.diffs.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

        self.actionOpen.triggered.connect(self.on_open_triggered)
        self.actionSavex.triggered.connect(self.on_savex_triggered)
        self.actionSave.triggered.connect(self.on_save_triggered)

        self.edit_action = QAction(QIcon.fromTheme("text-editor"), 'Edit...')
        self.edit_action.triggered.connect(self.on_dddasav_edit)

        self.load_action = QAction(QIcon.fromTheme("document-open"), 'Open...')
        self.load_action.triggered.connect(self.on_dddasav_load)

        self.dddasav.setPlaceholderText('Find your save file')
        self.dddasav.addAction(self.edit_action, QLineEdit.ActionPosition.TrailingPosition)

        self.settings = QSettings("MCondarelli", "DDDAsav")
        file = self.settings.value('file/savefile')
        if file:
            self.dddasav.setText(file)
            QApplication.processEvents()
            self.on_dddasav_load()

    def on_main_currentChanged(self, index: int):
        if self.main.currentWidget().objectName() == 'tab_diff':
            self.diffs.clear()
            self.diffs.setColumnCount(3)
            self.diffs.setRowCount(0)

            def callback(line: int, old:str , new:str ):
                n = self.diffs.rowCount()
                self.diffs.setRowCount(n + 1)
                self.diffs.setItem(n, 0, QTableWidgetItem(str(line)))
                self.diffs.setItem(n, 1, QTableWidgetItem(old))
                self.diffs.setItem(n, 2, QTableWidgetItem(new))

            self.setCursor(QCursor(Qt.CursorShape.WaitCursor))
            self.wrapper.compute_diff_table(callback)
            self.unsetCursor()

    def on_dddasav_edit(self):
        qfd = QFileDialog()
        qfd.setFileMode(QFileDialog.FileMode.ExistingFile)
        qfd.setNameFilter("Savefiles (*.sav)")
        if qfd.exec():
            self.dddasav.setText(qfd.selectedFiles()[0])
        self.dddasav.removeAction(self.load_action)
        if self.dddasav.text():
            self.dddasav.addAction(self.load_action, QLineEdit.ActionPosition.TrailingPosition)
            self.settings.setValue('file/savefile', self.dddasav.text())

    def on_open_triggered(self):
        if not self.dddasav.text():
            self.on_dddasav_edit()
        if self.dddasav.text():
            self.on_dddasav_load()

    def on_dddasav_load(self):
        self.person.setEnabled(False)
        self.pers.setCurrentIndex(-1)
        self.setCursor(QCursor(Qt.CursorShape.WaitCursor))
        try:
            self.wrapper.from_file(self.dddasav.text())
            self.main.setEnabled(True)
            self.actionSavex.setEnabled(True)
        except ValueError as e:
            print(f'ERROR: {e}')
            self.main.setEnabled(False)
            self.actionSavex.setEnabled(False)
        self.unsetCursor()

    @pyqtSlot()
    def on_savex_triggered(self):
        # dic = xmltodict.parse(self.xml.toPlainText())
        # self.xml.setPlainText(pprint.pformat(dic, 4))
        if self.wrapper:
            self.wrapper.to_xml_file(self.dddasav.text())

    @pyqtSlot()
    def on_save_triggered(self):
        if self.wrapper:
            self.wrapper.to_file()

    @pyqtSlot(str)
    def on_pers_currentTextChanged(self, txt):
        self.person.set_data(self.wrapper.persons[txt])

    @pyqtSlot(int)
    def on_pers_currentIndexChanged(self, idx):
        self.person.setEnabled(idx >= 0)

    @pyqtSlot()
    def on_wrapper_data_changed(self):
        if self.wrapper is not None:
            self.storage.set_storage_model(self.wrapper)
            self.main.setEnabled(True)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    pixmap = QPixmap('resources/dark-arisen.jpg')
    splash = QSplashScreen(pixmap)
    splash.show()
    app.processEvents()
    mw = MainWindow()
    mw.resize(1200, 1000)
    mw.show()
    splash.finish(mw)
    sys.exit(app.exec())
