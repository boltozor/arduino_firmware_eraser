import subprocess


class DudeAdapter:
    def __init__(self, com_port, board_type='uno'):
        self.com_port = com_port
        self.board_type = board_type

        self.board_configs = {
            'uno': ('-patmega328p', '-carduino'),
            'nano': ('-patmega328p', '-carduino'),
            'pro_mini': ('-patmega328p', '-cminipro'),
        }

    def erase_flash(self):
        if self.com_port is None:
            raise ValueError("COM порт не вибрано")

        if self.board_type not in self.board_configs:
            raise ValueError("Невідомий тип плати")

        mcu, programmer = self.board_configs[self.board_type]

        cmd = [
            "avrdude",
            mcu,
            programmer,
            f"-P{self.com_port}",
            "-b115200",
            "-e"
        ]

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate()
            return process.returncode, stdout, stderr
        except FileNotFoundError:
            return -1, "", "avrdude не знайдений. Перевірте встановлення."
