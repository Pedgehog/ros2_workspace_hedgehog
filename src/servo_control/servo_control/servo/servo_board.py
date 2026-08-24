# FORM TDK

import serial
import serial.tools.list_ports
import logging
import time
import threading
from queue import Queue


class ServoBoardInterface(threading.Thread):
    cmd_terminator = ";"
    response_terminator = "#"
    board_hid = "servo_board"

    def __init__(
        self, port, baudrate=115200, timeout=1, bytesize=8, parity="N", stopbits=1
    ):
        super().__init__()
        self.ser = serial.Serial(
            port,
            baudrate=baudrate,
            timeout=timeout,
            bytesize=bytesize,
            parity=parity,
            stopbits=stopbits,
        )
        time.sleep(1.7)
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.request_queue = Queue()
        self.dist_data_queue = Queue()
        self.running = True
        self.streamout = False
        self.serial_connect()
        self.start()

    def _check_hid(self):
        is_hid = False
        if self.ser.is_open:
            self.logger.info("serial open.")
            self.ser.reset_input_buffer()
            self.ser.write("hid;".encode())
            self.logger.info("Request hid.")
            time.sleep(0.01)
            response = self.ser.readline()
            response = [self._bytes_str(line) for line in response]
            hid_response = ""
            if len(response) > 2:
                self.logger.info("hid response: {}".format(response[1].strip()))
                hid_response = response[1]
                if self.board_hid in response[1]:
                    is_hid = True
        return is_hid, hid_response  # type: ignore

    def serial_close(self):
        if self.ser.is_open:
            self.ser.close()

    def serial_connect(self):
        if self.ser.is_open:
            self.logger.info("connected to Servo board....")

    def start_reading(self):
        self.running = True

    def stop_reading(self):
        self.running = False

    def _bytes_str(self, d):
        return d if type(d) is str else "".join([chr(b) for b in d])

    def _str_bytes(self, s):
        return s.encode("ascii")

    def serial_write(self, s):
        if not s:
            return
        try:
            self.ser.flush()
            self.ser.reset_input_buffer()
            self.ser.write(self._str_bytes(s + self.cmd_terminator))
        except:
            pass

    def serial_read(self):
        s = self.ser.readline()
        if not s:
            return None
        return s.decode("utf-8", errors="ignore").strip()

    def get_data(self):
        data = ""
        while True:
            res = self.serial_read()
            if res is None:
                break
            data = data + res
            if self.cmd_terminator in res:
                self.dist_data_queue.put(data)
                break

    def move_servo(self, servo_idx: int, angle: float):
        self.request_queue.put(f"move {servo_idx} {angle}")

    def sweep_servo(self, servo_idx: int, start_angle: float, target_angle):
        self.request_queue.put(f"sweep {servo_idx} {start_angle} {target_angle}")

    def get_servo_pose(self, servo_idx: int):
        self.request_queue.put(f"get {servo_idx}")

    def reset_servo_pose(self, servo_idx: int):
        self.request_queue.put(f"reset {servo_idx}")

    def run(self):
        while self.running:
            try:
                if not self.request_queue.empty():
                    request_ = self.request_queue.get()
                    if len(request_) > 1:
                        self.serial_write(request_)
                        time.sleep(0.01)
            except Exception as e:
                print(f"Error reading from serial: {e}")

    def send_cmd_to_board(self, cmd: str):
        self.request_queue.put(cmd)

    def get_servo_data(self):
        if not self.dist_data_queue.empty():
            return self.dist_data_queue.get()
        else:
            return None

    def thread_close(self):
        self.stop_reading()
        self.serial_close()
        self.join()

    def get_servo_angle_blocking(self, servo_idx: int, timeout=1.0):
        if self.ser.is_open:
            self.ser.reset_input_buffer()

        self.serial_write(f"get {servo_idx}")

        t_start = time.time()
        while time.time() - t_start < timeout:
            res = self.serial_read()
            if res:
                res = res.strip()
                if res.endswith("#") or res.startswith("#"):
                    value_str = res[:-1]
                    try:
                        return int(value_str)
                    except ValueError:
                        self.logger.warning(
                            f"Unexpected non-integer response from servo {servo_idx}: {value_str}"
                        )
            time.sleep(0.02)
        self.logger.warning(f"Timeout waiting for servo {servo_idx}")
        return None
