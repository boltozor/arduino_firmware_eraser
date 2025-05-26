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

    def _execute_avrdude_command(self, cmd_args):
        cmd = ["avrdude"] + cmd_args
        try:
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            stdout, stderr = process.communicate()
            return process.returncode, stdout, stderr
        except FileNotFoundError:
            return -1, "", "avrdude не знайдений. Перевірте встановлення."

    def erase_flash(self):
        if not self.com_port:
            raise ValueError("COM порт не вибрано")
        if self.board_type not in self.board_configs:
            raise ValueError("Невідомий тип плати")

        mcu, programmer = self.board_configs[self.board_type]
        cmd_args = [mcu, programmer, f"-P{self.com_port}", "-b115200", "-e"]
        return self._execute_avrdude_command(cmd_args)

    def verify_connection(self):
        if not self.com_port:
            raise ValueError("COM порт не вибрано")
        if self.board_type not in self.board_configs:
            raise ValueError("Невідомий тип плати")

        mcu, programmer = self.board_configs[self.board_type]
        cmd_args = [mcu, programmer, f"-P{self.com_port}", "-b115200", "-v"]

        return_code, stdout, stderr = self._execute_avrdude_command(cmd_args)

        is_successful = (return_code == 0)
        primary_message = "Підключення успішне!" if is_successful else "Помилка підключення!"

        if not is_successful:
            if "avrdude не знайдений" in stderr:
                primary_message += f" ({stderr.strip()})"
            elif stderr:
                primary_message += f" (Деталі: {stderr.strip().splitlines()[-1]})"

        return is_successful, primary_message, stdout, stderr
