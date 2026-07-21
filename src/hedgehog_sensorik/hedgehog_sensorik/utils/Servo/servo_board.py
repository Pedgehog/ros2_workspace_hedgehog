# serial_interface.py
# FROM TDK
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
        # self.comm_port = port
        time.sleep(1.7)
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.request_queue = Queue()
        self.dist_data_queue = Queue()
        self.running = True
        self.streamout = False
        self.serial_connect()
        # time.sleep(5)
        self.start()

    def _check_hid(self):
        is_hid = False
        hid_response = ""
        if self.ser.is_open:
            self.logger.info("serial open.")
            self.ser.reset_input_buffer()
            self.ser.write("hid;".encode())
            self.logger.info("Request hid.")
            time.sleep(0.01)
            # response = self.ser.read_until("#".encode())
            response = self.ser.readline()
            # self.logger.info("hid response : {}".format(response))
            response = [self._bytes_str(line) for line in response]
            hid_response = ""
            if len(response) > 2:
                self.logger.info("hid response: {}".format(response[1].strip()))
                hid_response = response[1]
                if self.board_hid in response[1]:
                    is_hid = True
        return is_hid, hid_response

    def serial_close(self):
        if self.ser.is_open:
            self.ser.close()

    def serial_connect(self):
        self.is_ussm_board_found = False
        # self.ser.port = self.comm_port
        # self.ser.open()
        if self.ser.is_open:
            self.logger.info("connected to Servo board....")
        # hid_check, board_info = self._check_hid()
        # if hid_check:
        #    self.is_ussm_board_found =  True
        #    #self.get_logger().info("connected to TDK USSM Sensor Board")
        #    self.logger.info("connected to TDK USSM Sensor Board")
        # if not self.is_ussm_board_found:
        #    self.ser.close()

    def start_reading(self):
        self.running = True
        # self.start()

    def stop_reading(self):
        self.running = False

    # Convert bytes to string
    def _bytes_str(self, d):
        """
        Convert bytes array to string
        """
        return d if type(d) is str else "".join([chr(b) for b in d])

    def _str_bytes(self, s):
        """
        Convert string to ASCII bytes array
        """
        return s.encode("ascii")

    def serial_write(self, s):
        if not s:
            return
        try:
            # print("write line: " + s)
            # print("line end : {s} {}".format(s))
            self.ser.flush()
            self.ser.reset_input_buffer()
            # print("sending cmd:{}".format(s))
            self.ser.write(self._str_bytes(s + self.cmd_terminator))  # line_end
        except:
            pass

    def serial_read(self):
        s = self.ser.readline()
        if not s:  # timeout expired, no data
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
        # print("[servo cmd] idx:{}, angle: {}".format(servo_idx,angle))
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
                        # print("sending cmd request:", request_)
                        time.sleep(0.01)
                        # print("[before read from board]")
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
        """
        Request current servo angle and wait for response.
        Expects Arduino to reply like '123#'.
        """
        # Clear any old data
        if self.ser.is_open:
            self.ser.reset_input_buffer()

        # Send command
        self.serial_write(f"get {servo_idx}")

        t_start = time.time()
        while time.time() - t_start < timeout:
            res = self.serial_read()
            if res:
                res = res.strip()  # remove whitespace/newlines
                if res.endswith("#") or res.startswith("#"):
                    value_str = res[:-1]  # remove trailing '#'
                    try:
                        return int(value_str)
                    except ValueError:
                        self.logger.warning(
                            f"Unexpected non-integer response from servo {servo_idx}: {value_str}"
                        )
            time.sleep(0.02)  # tiny wait for board to respond

        self.logger.warning(f"Timeout waiting for servo {servo_idx}")
        return None
