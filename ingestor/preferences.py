import sys
from PyQt5.QtWidgets import QMainWindow, QApplication, QDialog
from PyQt5 import uic

Ui_MainWindow, QtBaseClass = uic.loadUiType('preferences.ui')

class MyApp(QMainWindow):

    def __init__(self):
        super(MyApp, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
    def accept(self):
        self.close()
    	
    def reject(self):
        self.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())
    
    