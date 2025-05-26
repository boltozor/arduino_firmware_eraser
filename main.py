import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget,
    QTextEdit, QComboBox, QLabel, QHBoxLayout, QMessageBox
)
from PyQt5.QtCore import QThread, pyqtSignal
import serial.tools.list_ports

from dude_adapter import DudeAdapter


class WorkerThread(QThread):
    output = pyqtSignal(str)
    error = pyqtSignal(str)
    finished = pyqtSignal(int)

    def __init__(self, com_port, board_type):
        super().__init__()
        self.com_port = com_port
        self.board_type = board_type

    def run(self):
        adapter = DudeAdapter(self.com_port, self.board_type)
        code, out, err = adapter.erase_flash()

        if code == -1:
            self.error.emit(err)
        else:
            self.output.emit(out)
            if err:
                self.error.emit(err)
        self.finished.emit(code)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Arduino Flash Eraser")

        self.layout = QVBoxLayout()

        self.port_label = QLabel("Виберіть COM порт:")
        self.port_combo = QComboBox()
        self.refresh_ports()
        self.board_label = QLabel("Тип плати:")
        self.board_combo = QComboBox()
        self.board_combo.addItems(["uno", "nano", "pro_mini"])
        self.erase_button = QPushButton("Стерти прошивку")
        self.erase_button.clicked.connect(self.erase_firmware)

        self.log = QTextEdit()
        self.log.setReadOnly(True)

        self.refresh_button = QPushButton("Оновити список портів")
        self.refresh_button.clicked.connect(self.refresh_ports)

        port_layout = QHBoxLayout()
        port_layout.addWidget(self.port_label)
        port_layout.addWidget(self.port_combo)
        port_layout.addWidget(self.refresh_button)

        board_layout = QHBoxLayout()
        board_layout.addWidget(self.board_label)
        board_layout.addWidget(self.board_combo)

        self.layout.addLayout(port_layout)
        self.layout.addLayout(board_layout)
        self.layout.addWidget(self.erase_button)
        self.layout.addWidget(self.log)

        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(container)

    def refresh_ports(self):
        self.port_combo.clear()
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.port_combo.addItem(port.device)

    def erase_firmware(self):
        com_port = self.port_combo.currentText()
        board_type = self.board_combo.currentText()

        if not com_port:
            QMessageBox.warning(self, "Помилка", "Оберіть COM порт!")
            return

        self.log.append(f"Стираємо прошивку на {com_port} ({board_type}) ...")
        self.erase_button.setEnabled(False)

        self.thread = WorkerThread(com_port, board_type)
        self.thread.output.connect(self.on_output)
        self.thread.error.connect(self.on_error)
        self.thread.finished.connect(self.on_finished)
        self.thread.start()

    def on_output(self, text):
        self.log.append(text)

    def on_error(self, text):
        self.log.append(f"<span style='color:red;'>{text}</span>")

    def on_finished(self, code):
        self.log.append(f"Процес завершено з кодом: {code}")
        self.erase_button.setEnabled(True)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
