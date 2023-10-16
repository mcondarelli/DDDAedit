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
        vl = QtWidgets.QGridLayout()
        self.setLayout(vl)
        l1 = QtWidgets.QLabel('name')
        vl.addWidget(l1, 0, 0)
        self.name = QtWidgets.QLineEdit()
        self.name.setReadOnly(True)
        vl.addWidget(self.name, 0, 1)
        l1 = QtWidgets.QLabel('level')
        vl.addWidget(l1, 0, 2)
        self.level = QtWidgets.QSpinBox()
        self.level.setMinimum(1)
        self.level.setMaximum(200)
        vl.addWidget(self.level, 0, 3)
        self.vo = picwidgets.PicGrid(
            [[Pers.vocs[0], Pers.vocs[1], Pers.vocs[2]],
             [Pers.vocs[3], Pers.vocs[4], Pers.vocs[5]],
             [Pers.vocs[6], Pers.vocs[7], Pers.vocs[8]]
             ])
        self.vo.selec.connect(self.on_vocation_selec)
        vl.addWidget(self.vo, 1, 0, 2, 3)
        self.se = picwidgets.StarEditor(max_count=9)
        # se.setSizePolicy(QSizePolicy(QSizePolicy.Policy.MinimumExpanding,QSizePolicy.Policy.Minimum))
        self.se.editing_finished.connect(self.on_vocation_level)
        vl.addWidget(self.se, 1, 3)

    def set_data(self, data: DDDAfile.DDDAfile):
        self.data = data
        data.dataChanged.connect(lambda : self.setEnabled(self.data.valid))
        data.persChanged.connect(self.on_pers_changed)
        data.pnamChanged.connect(lambda v: self.name.setText(v))
        data.plevChanged.connect(lambda v: self.level.setValue(v))
        data.pvocChanged.connect(lambda v: self.vo.select(v))
        data.pvolChanged.connect(lambda v: self.se.set_stars(v))

    def on_pers_changed(self):
        # self.name.setText(self.data.pname)
        # self.level.setValue(self.data.plevel)
        pass

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
    mw = MainWindow()
    mw.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
