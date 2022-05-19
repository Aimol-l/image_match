# This Python file uses the following encoding: utf-8
#! /usr/bin/python3
# coding = utf-8
import sys, os
import cv2 as cv
import numpy as np
from PyQt5.QtGui import QCursor, QPixmap, QImage
from PyQt5.QtWidgets import QApplication, QWidget, QMenu, QAction, QGraphicsScene, QMessageBox
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import Qt, pyqtSignal

# 界面文件
from Ui import Ui_Widget
from Ui import Img

def distence_euclidean(simple, feature):
    L = np.sqrt(np.sum((simple-feature)**2))
    return L


def distence_chi_square(simple, feature):
    L = 0
    for i in range(len(simple)):
        if simple[i]+feature[i] != 0:
            L += ((simple[i]-feature[i])**2)/(simple[i]+feature[i])
    return L
def distence_cos(simple, feature):
    try:
        dot = np.sum(simple*feature)
        simple_l2 = np.linalg.norm(simple, ord=2)
        feature_l2 = np.linalg.norm(feature, ord=2)
        L = dot/(simple_l2*feature_l2)
    except (ValueError, ArithmeticError):
        QMessageBox.warning('警告', '数值异常、算术异常之一！')
    except:
        QMessageBox.warning('警告', '发生异常，未知错误！')
    return L


class Child(QWidget, Img):
    def __init__(self, parent=None):
        super(Child, self).__init__(parent)
        self.setupUi(self)

    def get_data(self, path):
        s_path = path.split('|')
        self.setWindowTitle(s_path[0])
        image = cv.imread(s_path[0])
        self.setFixedSize(image.shape[1], image.shape[0])
        self.label_image.setGeometry(0, 0, image.shape[1], image.shape[0]);
        self.label_image.setPixmap(QPixmap(s_path[0]))


class MyMainWindow(QWidget, Ui_Widget):
    signal_1 = pyqtSignal(str)

    def __init__(self, parent=None):
        super(MyMainWindow, self).__init__(parent)
        self.setupUi(self)
        self.distence_fun = '卡方'
        self.child_window = Child()
        # match按钮默认不可点击
        self.match.setEnabled(False)
        # 添加画布
        self.graphicsScene = QGraphicsScene()
        self.scene = QGraphicsScene()  # 创建画布
        self.image_matched.setScene(self.scene)
        self.image_matched.show()
        # 声明在image_list创建右键菜单
        self.image_list.setContextMenuPolicy(Qt.CustomContextMenu)
        # 信号
        self.signal_1.connect(self.child_window.get_data)
        self.match.clicked.connect(self.slot_match)
        self.chi_square.clicked.connect(lambda: self.btnstate(self.chi_square))
        self.euclidean.clicked.connect(lambda: self.btnstate(self.euclidean))
        self.cos.clicked.connect(lambda: self.btnstate(self.cos))
        self.image_list.customContextMenuRequested.connect(self.create_rightmenu)
        self.list_answer.itemDoubleClicked.connect(self.slot_show_image)
        self.image_list.itemDoubleClicked.connect(self.slot_add_to_match)

    def slot_show_image(self):
        index = self.list_answer.currentItem().text()
        image_path = dir_path + '/' + index
        self.signal_1.emit(image_path)
        self.child_window.show()

    def btnstate(self, bnt):
        if bnt.text() == '卡方':
            self.distence_fun = '卡方'
        elif bnt.text() == '欧氏':
            self.distence_fun = '欧氏'
        elif bnt.text() == '夹角余弦':
            self.distence_fun = '夹角余弦'

    def create_rightmenu(self):
        # 创建菜单对象
        self.list_menu = QMenu(self)
        # 添加子项目
        self.load_images = QAction('载入图片库文件夹', self)
        self.add_to_match = QAction('添加为匹配图片', self)
        self.clear = QAction('清空图片列表', self)
        # 添加子项目行为
        self.list_menu.addAction(self.load_images)
        self.list_menu.addAction(self.add_to_match)
        self.list_menu.addAction(self.clear)
        # slot函数
        self.load_images.triggered.connect(self.slot_load_images)
        self.clear.triggered.connect(self.slot_clear)
        self.actionfileopen.triggered.connect(self.slot_load_images)
        self.add_to_match.triggered.connect(self.slot_add_to_match)
        # 显示菜单
        self.list_menu.popup(QCursor.pos())

    def get_hist(self, image):
        B_hist = np.array(cv.calcHist(image, [0], None, [256], [0, 255]))
        G_hist = np.array(cv.calcHist(image, [1], None, [256], [0, 255]))
        R_hist = np.array(cv.calcHist(image, [2], None, [256], [0, 255]))
        hist = np.concatenate((R_hist, G_hist, B_hist), axis=0).T[0]
        return hist

    def slot_match(self):
        self.match.setEnabled(False)
        # 关闭单选框
        self.chi_square.setEnabled(False)
        self.euclidean.setEnabled(False)
        self.cos.setEnabled(False)
        self.list_answer.clear()
        # 样本图片的特征矩阵
        simple_hist = np.array(self.get_hist(cv.imread(image_path)))
        # 计算各个图片的特征与样本特征间的距离
        distence = []
        for i in range(self.image_list.count()):
            self.image_list.setCurrentRow(i)
            image = cv.imread(dir_path + '/' + self.image_list.currentItem().text())
            hist = self.get_hist(image)
            try:
                # 选择距离衡量算法
                if self.distence_fun == '卡方':
                    similarity = distence_chi_square(simple_hist, hist)
                elif self.distence_fun == '欧氏':
                    similarity = distence_euclidean(simple_hist, hist)
                elif self.distence_fun == '夹角余弦':
                    similarity = distence_cos(simple_hist, hist)
                currentitem = self.image_list.currentItem().text()
            except (ValueError, ArithmeticError):
                QMessageBox.warning(self, '警告', '数值异常、算术异常之一！')
            except:
                QMessageBox.warning(self, '警告', '发生异常，未知错误！')
                return
            distence.append([round(similarity, 3), i, currentitem])
            self.image_list.setCurrentRow(i)
            QApplication.processEvents()  # 刷新
        # 判断距离算法，cos和其他算法排序相反
        if self.distence_fun == '夹角余弦':
            destence = sorted(distence, key=lambda x: x[0], reverse=True)
        else:
            destence = sorted(distence, key=lambda x: x[0], reverse=False)
        # 添加到list中
        for index, d in enumerate(destence):
            self.list_answer.addItem(d[2]+'|'+str(d[0]))
            # QApplication.processEvents()  # 刷新
        # 启用单选框
        self.chi_square.setEnabled(True)
        self.euclidean.setEnabled(True)
        self.cos.setEnabled(True)
        self.match.setEnabled(True)

    def slot_add_to_match(self):
        try:
            index = self.image_list.currentItem().text()
            _translate = QtCore.QCoreApplication.translate
            self.groupBox_match.setTitle(_translate("Widget", "样本图片: "+index))
            global image_path
            image_path = dir_path + '/' + index
            image = cv.imread(image_path)
            image_resize = cv.resize(image, dsize=(271, 251))
            cvimg = cv.cvtColor(image_resize, cv.COLOR_BGR2RGB)
            frame = QImage(cvimg, cvimg.shape[1], cvimg.shape[0], cvimg.shape[1]*3, QImage.Format_RGB888)
            self.scene.clear()  # 先清空上次的残留
            self.pix = QPixmap.fromImage(frame)
            self.scene.addPixmap(self.pix)
            self.match.setEnabled(True)
        except:
            QMessageBox.warning(self, '警告', '发生异常，或许是没有选择图片？')

    def slot_load_images(self):  # load_images槽函数，加载库图片
        # 先清空
        self.image_list.clear()
        global dir_path
        dir_path = QtWidgets.QFileDialog.getExistingDirectory(self, "选择文件夹", '/home/aimol/图片/')
        _translate = QtCore.QCoreApplication.translate
        if dir_path != '':
            for file in os.listdir(dir_path):
                # 过滤文件夹
                if not os.path.isdir(file):
                    strlist = file.split('/')
                    file_type = strlist[-1].split('.')
                    # 过滤jpg和png图片
                    if file_type[-1] == 'png' or file_type[-1] == 'jpg':
                        self.image_list.addItem(strlist[-1])
            self.groupBox_image.setTitle(_translate("Widget", "匹配库图片,共：{}张".format(str(self.image_list.count()))))
        else:
            QMessageBox.warning(self, '警告', '发生异常，或许是没有选择文件夹？')
            self.groupBox_image.setTitle(_translate("Widget", "匹配库图片,共：error!"))

    def slot_clear(self):
        self.match.setEnabled(False)
        _translate = QtCore.QCoreApplication.translate
        self.groupBox_image.setTitle(_translate("Widget", "匹配库图片,共：0张"))
        self.image_list.clear()


if __name__ == "__main__":
    # 适配2k高分辨率屏幕
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
    app = QApplication(sys.argv)
    myWin = MyMainWindow()
    myWin.show()
    sys.exit(app.exec_())
