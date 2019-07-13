#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import time
import requests

from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor

from PyQt5.QtWidgets import ( QApplication, QWidget, QMainWindow,
                              QProgressBar, QPushButton,
                              QDesktopWidget, QFileDialog, QMessageBox )
                              
from PyQt5.QtCore import QThread, QObject, pyqtSignal
from PyQt5 import QtGui

class UploaderThread(QThread):
    '''
    Uploads a file using requests and requests_toolbelt's multipart encoder,
    emits upload progress values while uploading
    '''
    UPLOAD_URL = 'https://transfer.sh/'
    # send current progress value
    upload_signal = pyqtSignal(int)
    # set up maximum ProgressBar value
    setup_progressbar_signal = pyqtSignal(int)
    # send upload result (HTTP code and text)
    upload_result_signal = pyqtSignal(int, str)
    
    def __init__(self, parent=None, file_path=''):
        super(UploaderThread, self).__init__(parent)
        self.file_path = file_path
     
    def __del__(self):
        self.wait()
    
    def callback(self, monitor):
        self.upload_signal.emit(monitor.bytes_read)
        
    def run(self):
        multipart_encoder = MultipartEncoder({
            'file': (self.file_path.split('/')[-1], 
                     open(self.file_path, 'rb'), 'text/plain'),})
        self.setup_progressbar_signal.emit(multipart_encoder.len)
        monitor = MultipartEncoderMonitor(multipart_encoder, self.callback)
        r = requests.post(self.UPLOAD_URL, data=monitor,
                          headers={'Content-Type': monitor.content_type})
        self.upload_result_signal.emit(r.status_code, r.text)        

class App(QMainWindow):
    
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.btn = QPushButton('Select file...', self)
        self.btn.move(100, 5)
        self.btn.clicked.connect(self.pickFileDialog)
        
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setGeometry(25, 40, 250, 25)

        self.resize(300, 100)
        self.center_window()
        self.setWindowTitle('File uploader')
        
        self.show()
    
    def center_window(self):
        frameGm = self.frameGeometry()
        centerPoint = QDesktopWidget().availableGeometry().center()
        frameGm.moveCenter(centerPoint)
        self.move(frameGm.topLeft())
        
    def upload_finished(self):
        self.statusBar().showMessage('')
        self.btn.setEnabled(True)
        
    def upload_result(self, code, text):
        if code == 200:
            QMessageBox.information(self, 'Done', 'Your link: ' + text)
        else:
            QMessageBox.warning(self, 'Error', text)
    
    def setup_progressbar(self, value):
        self.progress_bar.setMinimum(0)        
        self.progress_bar.setMaximum(value)
        
    def update_progressbar(self, value):       
        self.progress_bar.setValue(value)

    def pickFileDialog(self):
        file_path = QFileDialog.getOpenFileName(self, 'Select file', '.')[0]
        if not file_path: return
        self.btn.setEnabled(False)
        self.statusBar().showMessage('File: ' + str(file_path))
        
        self.thread = UploaderThread(self, file_path)
        self.thread.upload_signal.connect(self.update_progressbar)
        self.thread.setup_progressbar_signal.connect(self.setup_progressbar)
        self.thread.upload_result_signal.connect(self.upload_result)
        self.thread.finished.connect(self.upload_finished)  
              
        self.thread.start()

if __name__ == '__main__':
    app = QApplication([])
    uploader_app = App()
    sys.exit(app.exec_())
