import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget,
    QTextEdit, QComboBox, QLabel, QHBoxLayout, QMessageBox
)
from PyQt5.QtCore import QThread, pyqtSignal, QTimer
import serial.tools.list_ports

from dude_adapter import DudeAdapter


class WorkerThread(QThread):
    output = pyqtSignal(str)
    error = pyqtSignal(str)
    finished = pyqtSignal(int)

    def __init__(self, com_port, board_type, task="erase"):
        super().__init__()
        self.com_port = com_port
        self.board_type = board_type
        self.task = task

    def run(self):
        try:
            adapter = DudeAdapter(self.com_port, self.board_type)

            if self.task == "erase":
                self.output.emit(
                    f"Запускаємо стирання прошивки на {self.com_port} ({self.board_type})...")
                code, out, err = adapter.erase_flash()
                if code == -1:
                    self.error.emit(err)
                else:
                    self.output.emit(out)
                    if err:
                        self.error.emit(err)
                self.finished.emit(code)

            elif self.task == "check":
                self.output.emit(
                    f"Перевіряємо підключення до {self.com_port} ({self.board_type})...")
                is_successful, primary_message, out, err = adapter.verify_connection()
                if is_successful:
                    self.output.emit(
                        f"<span style='color:green;'>{primary_message}</span>")
                    if out:
                        self.output.emit(out)
                    self.finished.emit(0)
                else:
                    self.error.emit(
                        f"<span style='color:red;'>{primary_message}</span>")
                    if err:
                        self.error.emit(err)
                    self.finished.emit(-1)
            else:
                self.error.emit("Невідоме завдання для потоку.")
                self.finished.emit(-1)

        except ValueError as e:
            self.error.emit(f"Помилка конфігурації: {e}")
            self.finished.emit(-1)
        except Exception as e:
            self.error.emit(f"Неочікувана помилка: {e}")
            self.finished.emit(-1)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Arduino Flash Eraser")
        self.setGeometry(100, 100, 600, 400)

        self.layout = QVBoxLayout()

        self.port_label = QLabel("Виберіть COM порт:")
        self.port_combo = QComboBox()
        port_layout = QHBoxLayout()
        port_layout.addWidget(self.port_label)
        port_layout.addWidget(self.port_combo)

        self.board_label = QLabel("Тип плати:")
        self.board_combo = QComboBox()
        self.board_combo.addItems(["uno", "nano", "pro_mini"])
        board_layout = QHBoxLayout()
        board_layout.addWidget(self.board_label)
        board_layout.addWidget(self.board_combo)

        self.erase_button = QPushButton("Стерти прошивку")
        self.erase_button.clicked.connect(self.erase_firmware)
        self.check_connection_button = QPushButton("Перевірити підключення")
        self.check_connection_button.clicked.connect(self.check_connection)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setPlaceholderText(
            "Логи операцій будуть відображатися тут...")

        self.layout.addLayout(port_layout)
        self.layout.addLayout(board_layout)
        self.layout.addWidget(self.erase_button)
        self.layout.addWidget(self.check_connection_button)
        self.layout.addWidget(self.log)

        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(container)

        self.thread = None

        self.port_refresh_timer = QTimer(self)
        self.port_refresh_timer.setInterval(5000)
        self.port_refresh_timer.timeout.connect(self.refresh_ports)
        self.port_refresh_timer.start()

        self.refresh_ports()

    def refresh_ports(self):
        current_ports = {self.port_combo.itemText(
            i) for i in range(self.port_combo.count())}
        new_ports_objects = serial.tools.list_ports.comports()
        new_ports_names = {port.device for port in new_ports_objects}

        if current_ports != new_ports_names:
            self.port_combo.clear()

            if not new_ports_objects:
                self.port_combo.addItem("Порти не знайдено")
                self.erase_button.setEnabled(False)
                self.check_connection_button.setEnabled(False)
                self.log.append(
                    "<span style='color:orange;'>Увага: COM порти не знайдено. Перевірте підключення пристроїв.</span>")
            else:
                for port in new_ports_objects:
                    self.port_combo.addItem(port.device)

                if len(new_ports_objects) == 1:
                    self.port_combo.setCurrentIndex(0)
                    self.log.append(
                        f"<span style='color:green;'>Автоматично вибрано порт: {new_ports_objects[0].device}</span>")
                else:
                    self.log.append(
                        "<span style='color:green;'>Список COM портів оновлено.</span>")

                self.erase_button.setEnabled(True)
                self.check_connection_button.setEnabled(True)

    def _start_worker_operation(self, task_type):
        com_port = self.port_combo.currentText()
        board_type = self.board_combo.currentText()

        if not com_port or com_port == "Порти не знайдено":
            QMessageBox.warning(self, "Помилка", "Оберіть COM порт!")
            return

        self.erase_button.setEnabled(False)
        self.check_connection_button.setEnabled(False)
        self.port_refresh_timer.stop()

        self.thread = WorkerThread(com_port, board_type, task=task_type)
        self.thread.output.connect(self.on_output)
        self.thread.error.connect(self.on_error)
        self.thread.finished.connect(self.on_finished)
        self.thread.start()

    def erase_firmware(self):
        self.log.clear()
        self._start_worker_operation("erase")

    def check_connection(self):
        self.log.clear()
        self._start_worker_operation("check")

    def on_output(self, text):
        self.log.append(text)

    def on_error(self, text):
        self.log.append(f"<span style='color:red;'>{text}</span>")

    def on_finished(self, code):
        self.log.append(f"Процес завершено з кодом: {code}")
        self.erase_button.setEnabled(True)
        self.check_connection_button.setEnabled(True)
        self.port_refresh_timer.start()
        self.thread = None


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
