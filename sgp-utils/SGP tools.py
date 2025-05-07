import sys
import subprocess
from PyQt5.QtWidgets import QApplication, QDialog, QVBoxLayout, QPushButton, QWidget, \
    QLabel, QHBoxLayout


class HelpDialog(QDialog):
    def __init__(self, help_text):
        super().__init__()
        self.initUI(help_text)

    def initUI(self, help_text):
        # self.setWindowTitle('Help')
        layout = QVBoxLayout()

        # Help text
        label = QLabel(help_text)
        layout.addWidget(label)

        self.setLayout(layout)


class AppDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('SGP Tools')
        layout = QVBoxLayout()

        # Dictionary of executables and their respective button labels and help texts
        executables = [
            ("Parse absolute data - QA version",
             "python C:\\sgp-utils\\sgp-utils\\fg5_parse_qa.py",
             "This program parses absolute data (...project.txt files) in the specified " \
             "directory. It generates an Excel file with formulas that check the polar \n"
             "motion, laser calibration, and other values " \
             "for \naccuracy."),
            ("Parse absolute data - CSV output",
             "python C:\\sgp-utils\\sgp-utils\\fg5_parse.py",
             "This program parses absolute data (...project.txt files). in the specified " 
             "directory. It generates a .csv file with the important information."),
            ("Laser drift correction",
             "python C:\\sgp-utils\\sgp-utils\\fg5_update_laser.py",
             "This program applies a laser drift correction to the .project.txt files in the chosen \n" \
             ' directory. The original .project.txt file is backed up as a \".original.txt\" file and a \n' \
             "comment is added to the .project.txt file to indicate the gravity value was adjusted."),
            ("Ingestor", "C:\\Path\\To\\Your\\Executable4.exe",
             "Help text for Executable 4."),
            # ("Executable 5", "C:\\Path\\To\\Your\\Executable5.exe",
            #  "Help text for Executable 5."),
        ]

        for label, path, help_text in executables:
            h_layout = QHBoxLayout()  # Horizontal layout for button and help button

            button = QPushButton(label)
            button.setFixedWidth(250)  # Set fixed width for the main buttons
            button.clicked.connect(lambda checked, p=path: self.run_executable(p))

            help_button = QPushButton("?")
            help_button.setFixedWidth(20)  # Set fixed width for the help button
            help_button.clicked.connect(
                lambda checked, ht=help_text: self.show_help(ht))

            h_layout.addWidget(button)
            h_layout.addWidget(help_button)

            layout.addLayout(h_layout)

        self.setLayout(layout)

    def run_executable(self, path):
        try:
            subprocess.Popen(path)
        except Exception as e:
            print(f"Error launching {path}: {e}")

    def show_help(self, help_text):
        help_dialog = HelpDialog(help_text)
        help_dialog.exec_()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    dialog = AppDialog()
    dialog.exec_()
