#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan  9 09:45:27 2017

@author: pavel
"""
import sys
from PyQt5 import QtGui, QtCore, QtWidgets

from PyQt5.QtWidgets import QWidget, QApplication, QMainWindow, QGraphicsView, QGraphicsItem, QMenu, QAction
from PyQt5.QtGui import QPainter, QColor, QIcon
#from PyQt5.QtCore import QPoint, QRectF
from PyQt5 import uic

import file_scanner
import program_info
from utils import in_range, pretty_size
from file_manager import open_folder
from stack import Stack


import time

MAX_BYTE = 255
QT_ANGLE_MULT = 16 # qt measures angles in (degrees / 16)

CHART_MAX_LAYERS = 10
CHART_LAYER_WIDTH = 50
CHART_ZOOM_FACTOR = 1.2
CHART_MAX_ANGLE = 360
CHART_MIN_ANGLE = 1

WHEEL_SCALING_FACTOR = 240.0


def filling_color(layer, start_angle, span_angle):
    # greater layer => darker
    # larger angle => brighter
    
    r = MAX_BYTE - in_range(int(span_angle * MAX_BYTE / CHART_MAX_ANGLE), 0, MAX_BYTE)
    g = in_range(int((CHART_MAX_LAYERS - layer) * MAX_BYTE / CHART_MAX_LAYERS), 0, MAX_BYTE)
    b = MAX_BYTE - in_range(int(start_angle * MAX_BYTE / CHART_MAX_ANGLE), 0, MAX_BYTE)
    
    #print(layer, start_angle, span_angle, r, g, b)
    return QtGui.QColor(r, g, b)
    
def files_to_sectors(root):
    root_level = root.level
    total_size = root.size if root.size > 1 else 1    
        
    queue = [(0, CHART_MAX_ANGLE, root)] #start_angle, span_angle, obj
    #bfs
    while len(queue) > 0:
        start_angle, span_angle, elm = queue.pop(0)
        level = elm.level - root_level
        
        if level > CHART_MAX_LAYERS:
            break
        
        if span_angle > CHART_MIN_ANGLE:
            yield elm, level, start_angle, span_angle        
        
        
        #add children    
        #print(elm.name)
        for child in elm.children:
            child_span = child.size / total_size * CHART_MAX_ANGLE
            queue.append((start_angle, child_span, child))
            start_angle += child_span       

def tooltip_text(elm):
    return "<b>{name}</b> <br>{size}".format(name = elm.path(),
                                             size=pretty_size(elm.size))
def central_text(elm):
    return "<center><b>{size}</b></center>".format(size=pretty_size(elm.size))


class MyWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MyWindow, self).__init__()
        self.path = None
        self.resize(640, 480)

        self.setWindowTitle('Select Path')
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)

        self.frame = MyFrame(self)
        self.setCentralWidget(self.frame)

        self.initUI()
                
        self.show()

    def initUI(self):
        menubar = self.menuBar()

        fileMenu = menubar.addMenu('&File')
        editMenu = menubar.addMenu('&Edit')
        viewMenu = menubar.addMenu('&View')
        helpMenu = menubar.addMenu('&Help')

        self.addMenuAction(fileMenu, '&Open', self.dirOpenEvent, 'Ctrl+O', 'Open directory')
        self.addMenuAction(fileMenu, 'E&xit', self.close, 'Ctrl+Q', 'Exit application')

        self.addMenuAction(editMenu, '&Back', self.goBackEvent, 'Ctrl+Z', 'Go back')
        self.addMenuAction(editMenu, '&Forward', self.goForwardEvent, 'Ctrl+Shift+Z', 'Go forward')
        self.addMenuAction(editMenu, '&Origin', self.goOriginEvent, None, 'Go to initial directory')
        self.addMenuAction(editMenu, '&Rescan', self.rescanEvent, None, 'Scan again')

        self.addMenuAction(viewMenu, 'Zoom i&n', self.zoomInEvent, 'Ctrl++', 'Zoom in')
        self.addMenuAction(viewMenu, 'Zoom o&ut', self.zoomOutEvent, 'Ctrl+-', 'Zoom out')
        self.addMenuAction(viewMenu, 'Reset zoom', self.zoomResetEvent, None, 'Reset zoom')

        self.addMenuAction(helpMenu, '&About', self.aboutEvent, None, 'About program')


    def addMenuAction(self, menu, name, func, shortcut = None, tip = None):
        action = QAction(name, self)
        action.triggered.connect(func)

        if shortcut is not None:
            action.setShortcut(shortcut)
        if tip is not None:
            action.setStatusTip(tip)

        menu.addAction(action)
        
    """
    def mouseReleaseEvent(self, event):
        print("View: mouseReleaseEvent")
        super(MyWindow, self).mouseReleaseEvent(event)
    """

    def dirOpenEvent(self, event):
        path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select", self.path)

        if (path is not None) and (path != ""):
            self.scan_path(str(path))

    def rescanEvent(self, event):
        if self.path is not None:
            self.scan_path(self.path)

    def goBackEvent(self, event):
        self.frame.draw_stack_back()
    def goForwardEvent(self, event):
        self.frame.draw_stack_forward()
    def goOriginEvent(self, event):
        self.frame.draw_origin()

    def zoomInEvent(self, event):
        self.frame.zoom(1)
    def zoomOutEvent(self, event):
        self.frame.zoom(-1)
    def zoomResetEvent(self, event):
        self.frame.zoom_reset()

    def aboutEvent(self, event):
        template = "<b>{name}</b><br>ver. {ver}<br><br>Author: {author}" \
                   "<br>e-mail: <a href=\"mailto:{email}\">{email}</a><br><br>"
        QtWidgets.QMessageBox.about(self, "About Program", template.format(name = program_info.PROGRAM_NAME,
                                                                           ver = program_info.PROGRAM_VER,
                                                                           author = program_info.AUTHOR_NAME,
                                                                           email = program_info.AUTHOR_EMAIL))
        #esponse = QtWidgets.QMessageBox.aboutQt(self, "About Qt")

    def scan_path(self, path):
        def on_progress(scan_path):
            self.statusBar().showMessage('Scanning ' + scan_path)

        def on_result(root_element):
            self.setWindowTitle(self.path)
            self.frame.reset_stack()
            self.frame.draw_new(root_element)
            self.statusBar().showMessage('Ready')

        self.path = path

        # create Worker
        self.scanner = Scanner(self.path, on_progress, on_result)
        self.scanner.start()




class Scanner(QtCore.QObject):
    finished = QtCore.pyqtSignal()
    progress = QtCore.pyqtSignal(str)
    result = QtCore.pyqtSignal(object)

    def __init__(self, scan_path, on_progress, on_result, parent = None):
        super(Scanner, self).__init__(parent)
        self.scan_path = scan_path

        # Create Thread
        self.thread = QtCore.QThread()

        #Connect Worker`s Signals to Form method slots to post data.
        self.progress.connect(on_progress)
        self.result.connect(on_result)


    @QtCore.pyqtSlot()
    def scan(self): # A slot takes no params
        root = file_scanner.scan(self.scan_path,
                                 on_progress = lambda x: self.progress.emit(str(x)),
                                 on_error=     lambda x: self.progress.emit(str(x)))

        self.result.emit(root)
        self.finished.emit()

    def start(self):
        # Move the Worker object to the Thread object
        self.moveToThread(self.thread)
        # Connect Worker Signals to the Thread slots
        self.finished.connect(self.thread.quit)
        # Connect Thread started signal to Worker operational slot method
        self.thread.started.connect(self.scan)
        #Start the thread
        self.thread.start()


class MyFrame(QtWidgets.QGraphicsView):
    def __init__( self, parent = None ):
        super(MyFrame, self).__init__(parent)

        if parent is not None:
            self.setGeometry(parent.frameGeometry())
            
       
        self.setScene(QtWidgets.QGraphicsScene())
        self.scene().setSceneRect(0, 0, CHART_LAYER_WIDTH * CHART_MAX_LAYERS, CHART_LAYER_WIDTH * CHART_MAX_LAYERS)
        #self.fitInView( self.scene().sceneRect(), QtCore.Qt.KeepAspectRatio )
        #self.fitInView( self.scene().itemsBoundingRect(), QtCore.Qt.KeepAspectRatio )
        self.pen = QtGui.QPen(QtGui.QColor(QtCore.Qt.black))
        self.setAcceptDrops(True)
        #self.setMouseTracking(True)


        self.scale_factor = 1.0
        self.elements_stack = Stack()


        #self.scene().setAcceptedMouseButtons(0)

    def mousePressEvent(self, event):
        print("frame mouse press", event)
        self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
        super(MyFrame, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        print("frame mouse release", event)
        self.setDragMode(QtWidgets.QGraphicsView.NoDrag)
        super(MyFrame, self).mouseReleaseEvent(event)

    #def mouseMoveEvent(self, event):
        #print("frame move", event)

    def reset_stack(self):
        self.elements_stack.clear()

    def draw_new(self, elm):
        self.elements_stack.add(elm)
        self._draw_diagram(elm)

    def draw_origin(self):
        elm = self.elements_stack.full_back()
        self._draw_diagram(elm)

    def redraw(self):
        elm = self.elements_stack.get_current()
        self._draw_diagram(elm)

    def draw_stack_back(self):
        elm = self.elements_stack.go_back()
        self._draw_diagram(elm)

    def draw_stack_forward(self):
        elm = self.elements_stack.go_forward()
        self._draw_diagram(elm)

        
    def _draw_diagram(self, root):
        if root is not None:
            self.scene().clear()
            squares = {}

            #print(root.name, root.level)

            for (elm, level, start_angle, span_angle) in files_to_sectors(root):
                if level not in squares:
                    squares[level] = MySquare(self.scene(), (level + 1) * CHART_LAYER_WIDTH)

                #print(elm.name)
                is_central = (level == 0)

                item = MyEllipse(self, elm, squares.get(level), central = is_central)
                item.setSpanAngle(int(span_angle * QT_ANGLE_MULT))
                item.setStartAngle(int(start_angle * QT_ANGLE_MULT))
                item.setZValue(CHART_MAX_LAYERS - level) # large => higher

                item.setPen(self.pen)
                item.setBrush(filling_color(level, start_angle, span_angle))

                if is_central:
                    text = MyText(elm, squares.get(level))
                    text.setZValue(CHART_MAX_LAYERS + 1)
                    self.scene().addItem(text)

                self.scene().addItem(item)
                self.scene().update()
                QtWidgets.QApplication.processEvents()
                #time.sleep(0.1) # nice animation
        
    def zoom(self, steps):
        factor = pow(CHART_ZOOM_FACTOR, steps)
        self.scale_factor *= factor
        self.scale(factor, factor)

    def zoom_reset(self):
        factor = 1/self.scale_factor
        self.scale_factor = 1.0
        self.scale(factor, factor)
        
    def wheelEvent(self, event):        
        if event.angleDelta() is not None:
            angle = event.angleDelta().x() + event.angleDelta().y()
            self.zoom(angle / WHEEL_SCALING_FACTOR)
        event.accept()

class MySquare(QtCore.QRectF):
    def __init__(self, scene, side):
        self.scene = scene
        
        width = scene.width()
        height = scene.height()
        
        center_x = width // 2
        center_y = height // 2
        
        half_side = side // 2
        
        left_x = center_x - half_side
        top_y = center_y - half_side
        
        super(MySquare, self).__init__(left_x, top_y, side, side)

class MyText(QtWidgets.QGraphicsTextItem):
    def __init__(self, element, rect, *args, **kwargs):
        super(MyText, self).__init__(*args, **kwargs)
        self.setHtml(central_text(element))
        self.setTextWidth(min(rect.width(), self.boundingRect().width()))

        #match centers of self and parent rectangle
        rect_cx, rect_cy  = rect.center().x(), rect.center().y()
        self.setX(rect_cx - (self.boundingRect().width() // 2) )
        self.setY(rect_cy - (self.boundingRect().height() // 2) )

        
class MyEllipse(QtWidgets.QGraphicsEllipseItem):    
    def __init__(self, frame, element, *args, central = False, **kwargs):
        super(MyEllipse, self).__init__(*args, **kwargs)

        self.frame = frame
        self.element = element
        self.central = central
        #self.setAcceptHoverEvents(True)
        
        self.setToolTip(tooltip_text(element))
        
        self.setEnabled(True)
        #self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)
        #self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, False)
        #self.setFlag(QtWidgets.QGraphicsItem.ItemIsFocusable, True)


    def mouseDoubleClickEvent(self, event):
        print("double click", event, self.central)

        if self.central and self.element.parent is not None: # double click on center -> go to parent
            self.frame.draw_new(self.element.parent)
        else: #double click on sector -> go to sector
            self.frame.draw_new(self.element)


    def contextMenuEvent(self, event):
        print("context", event)
        menu = QtWidgets.QMenu()
        menu.setTitle(str(self.element.path()))

        fmanager_action = menu.addAction("File Manager")
        menu.addSeparator()
        delete_action = menu.addAction("Delete")

        fmanager_action.triggered.connect(self.elmFileManagerEvent)
        delete_action.triggered.connect(self.elmDeleteEvent)


        menu.exec(event.screenPos())
        return event.accept()

    def elmFileManagerEvent(self, event):
        open_folder(self.element.path())


    def elmDeleteEvent(self, event):
        type_ = "file" if self.element.is_file else "directory"
        fpath = self.element.path()
        message = "<b>Delete {type_}</b><br>{fpath} <b>?</b>".format(type_ = type_,
                                                                   fpath = fpath)

        response = QtWidgets.QMessageBox.question(self.frame, "Message",
                     message, QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Cancel)

        if response == QtWidgets.QMessageBox.Ok:
            if self.central:
                #create copy of list that will be changed
                children = [child for child in self.element.children]
                for child in children:
                    child.delete()
            else:
                self.element.delete()

            self.frame.redraw()
            #event.accept()
        #else:
            #print("no")
            #event.ignore()

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MyWindow()


    window.show()
    if len(sys.argv) == 2:
        window.scan_path(sys.argv[1])

    sys.exit(app.exec_())



