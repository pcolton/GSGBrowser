import importlib
import sys
import os
import math

from PIL import Image
from PySide2 import QtCore, QtUiTools, QtWidgets, QtGui
from toolutils import safe_reload

from PySide2.QtGui import QPainter, QFontMetrics
from PySide2.QtWidgets import QLineEdit, QPushButton, QHBoxLayout, QLabel

#from: https://stackoverflow.com/a/11764662
class MyLabel(QLabel):

    def __init__(self, parent=None, w=0):
        super(MyLabel, self).__init__(parent)
        self.w = w
        
    def paintEvent( self, event ):
        painter = QPainter(self)

        metrics = QFontMetrics(self.font())
        elided  = metrics.elidedText(self.text(), QtCore.Qt.ElideRight, self.w)

        painter.drawText(self.rect(), self.alignment(), elided)

 
# from: https://stackoverflow.com/a/5556310     
class ImgWidget2(QtWidgets.QWidget):

    def __init__(self, parent=None, imagePath=None, w=0, h=0):
        super(ImgWidget2, self).__init__(parent)
        self.pic = QtGui.QPixmap(imagePath)
        self.pic = self.pic.scaled(w,h)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)

        painter.drawPixmap(0, 0, self.pic)
        
class MainWindow(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
    
        self.myWidth = 0
        
        # Load the interface layout from the .ui file.
        ui_file_path = "C:\\Users\\paul\\Development\\GSGBrowser\\form.ui"
        loader = QtUiTools.QUiLoader()
        ui_file = QtCore.QFile(ui_file_path)
        ui_file.open(QtCore.QFile.ReadOnly)
        
        # grab widgets
        self.mainWidget = loader.load(ui_file)
        self.table = self.mainWidget.table_items
        self.zoom = self.mainWidget.zoom
        self.percent = self.mainWidget.percent

        # event handlers
        self.mainWidget.btn_explore.clicked.connect(self.explore)
        self.mainWidget.btn_import.clicked.connect(self.gsg_import)
        self.zoom.valueChanged.connect(self.ui_update)

        # place our main widget onto the root 'window'
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(self.mainWidget)
        self.setLayout(self.layout)
        
        self.ui_update()

        self.table.setCornerButtonEnabled(0)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setVisible(False)
        
        bgColor = self.table.backgroundRole()
        palette = self.table.palette().color(bgColor)
        red = palette.red()
        green = palette.green()
        blue = palette.blue()
        css = "QTableWidget  { gridline-color: rgb(" + str(red) + "," + str(green) + "," + str(blue) + ");  } "
        self.table.setStyleSheet(css)
        
    def resizeEvent(self, event):
        self.myWidth = event.size().width()
        self.ui_update()
        QtWidgets.QMainWindow.resizeEvent(self, event)
        
    def explore(self):
        path = self.mainWidget.tf_path.text()
    
        selection = hou.ui.selectFile(
            start_directory = path, 
            title = "Choose GSG download directory",
            file_type = hou.fileType.Directory)
    
        self.mainWidget.tf_path.setText(selection)
        self.ui_update()
    
    def gsg_import(self):
    
        items = self.table.selectedItems()
    
        allPaths = []
        for i in items:
            fullPath = i.data(QtCore.Qt.UserRole)
            allPaths.append(fullPath)
    
        path = " ; ".join(allPaths)

        try:
            import greyscalegorilla_houdini_importer
            importlib.reload(greyscalegorilla_houdini_importer)
            greyscalegorilla_houdini_importer.import_greyscalegorilla_material(paths_str=path)
        
        except ModuleNotFoundError as e:
            hou.ui.displayMessage("Set the \"sys.path.append\" argument inside the greyscalegorilla.shelf file to point to the repository directory!")
    
    def ui_update(self):
        path = self.mainWidget.tf_path.text()
        mult = self.zoom.value() / 100
        self.percent.setText(str(self.zoom.value()) +"%")
        
        previews = []
    
        # Find all the preview images
        for item in os.scandir(path):
            if item.is_dir():
                itemPath = os.path.join(path, item)
                for file in os.scandir(itemPath):
                    if file.is_file() and file.name.endswith('_preview.jpg'):
                        previews.append(file)
    
        thumbCount = len(previews)
 
        columns = 0
        
        if self.myWidth > 0:
            columns = int((self.myWidth - (512 * mult / 3)) / (512 * mult))
        
        if columns == 0:
            columns = 4
            
        rows = math.ceil(thumbCount / columns)
        
        self.table.setRowCount(rows)
        self.table.setColumnCount(columns)
    
        count = 0
        for x in previews:
            name = x.name
            tooltip = name.split('_')[-2]

            col = count % columns
            row = int(count / columns)

            count += 1
            length = int(512 * mult)
            
            cell = QtWidgets.QWidget()
            layout = QtWidgets.QHBoxLayout()
            img = ImgWidget2(None, x.path, length, length)
            img.setFixedSize(QtCore.QSize(length, length))
            layout.addWidget(img)
            cell.setLayout(layout)
            
            topCell = QtWidgets.QWidget()
            layout = QtWidgets.QVBoxLayout()
            layout.addWidget(cell)
            label = MyLabel(tooltip, length)
            label.setAlignment(QtCore.Qt.AlignCenter)
            layout.addWidget(label)
            topCell.setLayout(layout)
            
            self.table.setCellWidget(row, col, topCell)
            self.table.setColumnWidth(col, length)
            
            cell.setGeometry(QtCore.QRect(0, 0, length, length))

            header = self.table.horizontalHeader()
            header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
            header.setMaximumSectionSize(length + 100)

            header = self.table.verticalHeader()
            header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
            header.setMinimumSectionSize(0)
            header.setMaximumSectionSize(length + 100)

