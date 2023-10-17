import sys
from typing import Optional

from PyQt6 import uic, QtWidgets, QtCore, QtGui

import DDDAfile
import picwidgets


class Pers(QtWidgets.QWidget):
    vocs = ['resources/DDicon_fighter.webp',
            'resources/DDicon_strider.webp',
            'resources/DDicon_mage.webp',
            'resources/DDicon_assassin.webp',
            'resources/DDicon_magicarcher.webp',
            'resources/DDicon_magicknight.webp',
            'resources/DDicon_warrior.webp',
            'resources/DDicon_ranger.webp',
            'resources/DDicon_sorcerer.webp']

    def __init__(self, parent=None):
        super().__init__(parent)
        self.data: Optional[DDDAfile.DDDAfile] = None
        self.item_data: Optional[DDDAfile.ItemData] = None
        # self.items = None

        self.name: Optional[QtWidgets.QLineEdit] = None
        self.level: Optional[QtWidgets.QSpinBox] = None
        self.vo: Optional[picwidgets.PicGrid] = None
        self.se: Optional[picwidgets.StarEditor] = None
        self.items: Optional[QtWidgets.QTableWidget] = None
        uic.loadUi("Pers.ui", self)
        header = self.items.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)

        self.vo.set_data(
            [[Pers.vocs[0], Pers.vocs[1], Pers.vocs[2]],
             [Pers.vocs[3], Pers.vocs[4], Pers.vocs[5]],
             [Pers.vocs[6], Pers.vocs[7], Pers.vocs[8]]
             ])
        self.vo.selec.connect(self.on_vocation_selec)
        # self.se.set_stars(9, 1)
        self.se.editing_finished.connect(self.on_vocation_level)

    def set_data(self, data: DDDAfile.DDDAfile):
        self.data = data
        data.dataChanged.connect(self.on_data_changed)
        data.persChanged.connect(self.on_pers_changed)
        data.pnamChanged.connect(lambda v: self.name.setText(v))
        data.plevChanged.connect(lambda v: self.level.setValue(v))
        data.pvocChanged.connect(lambda v: self.vo.select(v))
        data.pvolChanged.connect(lambda v: self.se.set_stars(v))

    def on_data_changed(self, data):
        self.item_data = DDDAfile.ItemData(data)
        self.setEnabled(self.data.valid)

    def on_pers_changed(self, pers):
        items = self.item_data.get_pers_items(pers)
        self.items.setRowCount(len(items))
        for r, item in enumerate(items):
            it = QtWidgets.QTableWidgetItem(str(item['item']['id']))
            it.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
            self.items.setItem(r, 0, it)
            self.items.setItem(r, 1, QtWidgets.QTableWidgetItem(item['item']['name']))
            self.items.setItem(r, 2, QtWidgets.QTableWidgetItem(item['item']['type']))
            it = QtWidgets.QTableWidgetItem(str(item['num']))
            it.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
            self.items.setItem(r, 3, it)

    def set_pers(self, pers):
        name = ''
        for chx in pers.findall('.//array[@name="(u8*)mNameStr"]/u8'):
            chv = chx.get('value')
            chi = int(chv)
            if chi > 0:
                name += chr(chi)
        self.name.setText(name or '???')
        levx = pers.find(".//u8[@name='mLevel']")
        if levx is not None:
            levv = levx.get('value')
            levi = int(levv)
            self.level.setValue(levi)

        vocx = pers.find(".//u8[@name='mJob']")
        if vocx is not None:
            voc = int(vocx.get('value'))
            print(voc)
            self.vo.select(voc)

    def on_vocation_selec(self, param):
        print(param)

    def on_vocation_level(self, level):
        print(level)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dddasav: Optional[QtWidgets.QLineEdit] = None
        self.xml: Optional[QtWidgets.QPlainTextEdit] = None
        self.main: Optional[QtWidgets.QWidget] = None
        self.pers: Optional[QtWidgets.QComboBox] = None
        self.pers_commit: Optional[QtWidgets.QPushButton] = None
        self.vocations: Optional[Pers] = None
        self.items: Optional[QtWidgets.QTableWidget]
        self.actionOpen: Optional[QtGui.QAction] = None
        self.actionSave: Optional[QtGui.QAction] = None
        self.actionSavex: Optional[QtGui.QAction] = None
        uic.loadUi("DDDAedit.ui", self)
        self.data = DDDAfile.DDDAfile(self)
        self.vocations.set_data(self.data)

        self.actionOpen.triggered.connect(self.on_open_triggered)
        self.actionSavex.triggered.connect(self.on_savex_triggered)

        self.edit_action = QtGui.QAction(QtGui.QIcon.fromTheme("text-editor"), 'Edit...')
        self.edit_action.triggered.connect(self.on_dddasav_edit)

        self.load_action = QtGui.QAction(QtGui.QIcon.fromTheme("document-open"), 'Open...')
        self.load_action.triggered.connect(self.on_dddasav_load)

        self.dddasav.setPlaceholderText('Find your save file')
        self.dddasav.addAction(self.edit_action, QtWidgets.QLineEdit.ActionPosition.TrailingPosition)

        self.settings = QtCore.QSettings("MCondarelli", "DDDAsav")
        file = self.settings.value('file/savefile')
        if file:
            self.dddasav.setText(file)
            QtWidgets.QApplication.processEvents()
            self.on_dddasav_load()

    def on_dddasav_edit(self):
        qfd = QtWidgets.QFileDialog()
        qfd.setFileMode(QtWidgets.QFileDialog.FileMode.ExistingFile)
        qfd.setNameFilter("Savefiles (*.sav)")
        if qfd.exec():
            self.dddasav.setText(qfd.selectedFiles()[0])
        self.dddasav.removeAction(self.load_action)
        if self.dddasav.text():
            self.dddasav.addAction(self.load_action, QtWidgets.QLineEdit.ActionPosition.TrailingPosition)
            self.settings.setValue('file/savefile', self.dddasav.text())

    def on_open_triggered(self):
        if not self.dddasav.text():
            self.on_dddasav_edit()
        if self.dddasav.text():
            self.on_dddasav_load()

    def on_dddasav_load(self):
        self.data.fname = self.dddasav.text()
        self.xml.setPlainText(self.data.pretty)
        self.unsetCursor()
        self.main.setEnabled(True)
        self.actionSavex.setEnabled(True)

    @QtCore.pyqtSlot()
    def on_savex_triggered(self):
        # dic = xmltodict.parse(self.xml.toPlainText())
        # self.xml.setPlainText(pprint.pformat(dic, 4))
        if self.data:
            self.data.savex()

    @QtCore.pyqtSlot(str)
    def on_pers_currentTextChanged(self, txt):
        self.data.pers = txt


def main():
    app = QtWidgets.QApplication(sys.argv)
    pixmap = QtGui.QPixmap('resources/dark-arisen.jpg')
    splash = QtWidgets.QSplashScreen(pixmap)
    splash.show()
    app.processEvents()
    mw = MainWindow()
    mw.show()
    splash.finish(mw)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
