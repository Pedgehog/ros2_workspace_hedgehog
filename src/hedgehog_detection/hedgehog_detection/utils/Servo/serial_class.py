# ----------------------------------------------
# Copyright (C) TDk Electronics GmbH & CO OG, https://tdk.com/
# author:  Naresh Chowdary Chitturi, naresh.chitturi@tdk.com
# ----------------------------------------------

# FROM TDK

from ast import Try
import re

import serial
import serial.tools.list_ports
import queue
import timeit
import time

import json
import io


# Global reader settings

max_uint8 = 0xFF
max_uint16 = 0xFFFF
max_uint32 = 0xFFFFFFFFFF


def str_bytes(s):
    """
    Convert string to ASCII bytes array
    """
    return s.encode("ascii")


# Convert bytes to string
def bytes_str(d):
    """
    Convert bytes array to string
    """
    return d if type(d) is str else "".join([chr(b) for b in d])


class SensorBoardSerialInterface(object):
    """
    Demo baord serial port interface
    Should be moved to a thread!

    """

    res_terminator = "#"

    line_end = ";"

    def __init__(self):
        super().__init__()
        self.ser = serial.Serial()
        self.ser.baudrate = 115200
        self.ser.parity = "N"
        self.ser.bytesize = 8
        self.ser.stopbits = 1
        self.ser.timeout = 2
        # self.ser.write_timeout = self.ser.timeout
        # self.ser.xonxoff = True

        self.running = True
        self.connected = False
        self.reader_com = ""
        self.stop_req = False

        self.quick_repeat = False
        self.continous_loop = False
        self.data_in = []
        self._frame_start = False
        self._frame_end = False
        self.run_meas = False
        self.distance_val = []
        self._distance_val = []

    def get_serial_baudrate(self):
        return self.ser.baudrate

    def set_serial_baudrate(self, baud_rate):
        self.ser.baudrate = baud_rate
        # print("baud rate: {}".format(self.ser.baudrate))

    def stop(self):
        """
        Set flag to stop worker loop
        """
        self.stop_req = True
        self._frame_start = False
        self._frame_end = False

    def set_baudrate(self, baudrate: int):
        """
        change the baudrate with demo board
        """
        self.ser.reset_input_buffer()
        self.ser.write(f"com {baudrate} ;".encode())
        time.sleep(0.001)
        res = self.ser.readline()
        res = bytes_str(res)
        print(f"res: {res}")
        if res:
            self.serial_baudrate = baudrate
            self.ser.reset_input_buffer()
            self.ser.write("hid ;".encode())
            print("sent hid...")
            time.sleep(0.001)
            # response = self.ser.readline()
            response = self.ser.read_until("#".encode())
            response = bytes_str(response)
            print("response: {}".format(response))

    def _time_delay(self, delay: int):
        """Time delay in ms

        Parameters
        ----------
        delay : int
            delay [ms]
        """
        if not delay:
            return
        start_time = timeit.default_timer()
        delay_timeout = delay / 1000
        while timeit.default_timer() < start_time + delay_timeout:
            time.sleep(0.001)

    @property
    def distance_val(self):
        return self._distance_val

    @distance_val.setter
    def distance_val(self, val):
        self._distance_val = val

    def serial_write(self, s):
        if not s:
            return
        try:
            # print("write line: " + s)
            # print("line end : {s} {}".format(s))
            self.ser.flush()
            self.ser.reset_input_buffer()
            self.ser.write(str_bytes(s + " " + self.line_end))  # line_end
        except:
            pass
        # send data to terminal
        # self.sig_serial.emit(s, True)

    def _serial_read(self):
        s = self.ser.readline()
        str_s = bytes_str(s)
        # self.sig_serial.emit(str_s, False)

        return str_s

    def serial_read(self) -> str:
        s = self.ser.readline()
        str_s = bytes_str(s)
        # print(str_s)
        if len(str_s) > 0:
            # print("readline: " + str_s.replace('\n', ''))
            # multiline support
            n = 0
            if "ACK" and "LINES" in str_s:
                n = int(str_s.split(";")[-1])
                for i in range(n):
                    s = self.ser.readline()
                    str_s = bytes_str(s)
        # return str_s.replace("\n", "")
        return str_s

    def serial_read_rest(self):
        s = bytearray()
        while self.ser.in_waiting:
            data = self.serial_read()
            s.extend(data.encode("ascii", errors="ignore"))
        return bytes_str(s)

    def parse_response(self, s: str):
        fields = s.split(";")
        return fields[0], fields[1:]

    def get_serial_port(self):
        port_ids = []
        device_info = []
        comports = sorted(serial.tools.list_ports.comports())
        for comport in comports:
            port_ids.append(comport.device)
            device_info.append(comport.description.split(" ")[-2])
            print(
                "[adl_reader] comport: {} description:{} ".format(
                    comport.device, comport.description.split(" ")[-2]
                )
            )
        # print("[adl_reader] comports: {}".format(port_ids))

    def _check_hid(self, hid_res: str):
        is_hid = False
        hid_response = ""
        if self.ser.is_open:
            print("serial open.")
            self.ser.reset_input_buffer()
            self.ser.write("hid;".encode())
            print("sent hid.")
            time.sleep(0.01)
            # response = self.ser.read_until("#".encode())
            response = self.ser.readlines()
            print("response : {}".format(response))
            response = [bytes_str(line) for line in response]
            hid_response = ""
            if len(response) > 2:
                print("response: {}".format(response[1]))
                hid_response = response[1]
                if hid_res in response[1]:
                    is_hid = True
        return is_hid, hid_response

    def serial_close(self):
        self.run_meas = False
        if self.ser.is_open:
            self.ser.close()

    def serial_connect(self, port_name: str):
        comm_port = port_name
        self.is_ussm_board_found = False
        self.ser.port = comm_port
        self.ser.open()
        hid_check, board_info = self._check_hid("TDK_USSM")
        if hid_check:
            self.is_ussm_board_found = True
            # self.get_logger().info("connected to TDK USSM Sensor Board")
            print("connected to TDK USSM Sensor Board")
        if not self.is_ussm_board_found:
            self.ser.close()

    # @staticmethod
    # def testmethod(val:str):
    #    print("got string ----> {}".format(val))

    # Todo: move to functions
    """
    def serial_connect(self, comm_port:str, hid_res:str):
        self.ports = []
        board_info = ""
        #self.testmethod(comm_port)
        if self.connected:
                self.ser.close()
        #comports = sorted(serial.tools.list_ports.comports())       
        #print(comports)
        #self.sig_comports.emit(comports)
        if comm_port == "hid;":
            try:
                #comports = sorted(serial.tools.list_ports.comports())
                comports = self.serial_list_devices()
                #print(comports)
                #self.sig_comports.emit(comports)
                is_reader_found = False
                nooftrials = 3

                for port in comports:
                    self.ser.port = port.device
                    self.ser.open()    
                    for i in range (nooftrials): # needed sometimes; with zcs firmware hid is recieved only in second attempt
                        hid_check, board_info = self._check_hid(hid_res)
                        if hid_check: 
                           self.ports.append(comm_port) 
                           is_reader_found =  True
                           break
                        #else:
                        #    self.ser.close()
                    if is_reader_found:
                        break
                    else:
                        self.ser.close()
                time.sleep(0.0011)
            except:
                if self.ser.is_open:
                    self.ser.close()
                pass
        else:
            try:                
                self.ser.port = comm_port
                self.ser.open()    
                hid_status, board_info = self._check_hid()   
                if hid_status :
                    self.ports.append(comm_port) 
                else:
                    self.ser.close()
                    self.connected = self.ser.is_open
                    #self.sig_com_status.emit(self.connected, self.reader_com)
                    #self.sig_com_warning.emit("{} is not TDK USSM board".format(comm_port), 'critical')
            except:
                pass
            if not self.ports:
                return

        if not self.ser.is_open:
            #self.sig_com_warning.emit(f"Could not find {hid_res}!\nMake sure that {hid_res} is connected to the PC.", 'critical')
            pass
        #elif len(self.ports) > 1:
        #    self.sig_com_warning.emit(f"Multiple readers found.\nOpened {self.ser.port}.", 'warning')

        self.connected = self.ser.is_open
        self.reader_com = self.ser.port
        #self.sig_com_status.emit(self.connected, self.reader_com)
        print("[serial] board_info:{}".format(board_info))
        #self.sig_board_info.emit(board_info)
    """

    def serial_list_devices(self):
        ports_list = []
        all_ports = serial.tools.list_ports.comports()
        # print("Found the following ports:")
        for port in all_ports:
            # print(str(port) + " HWID: " + str(port.hwid) + " PID: " + str(port.description))
            if "USB" in port.hwid:
                ports_list.append(port)
        return ports_list

    def read_data(self):
        """
        read data from the sensor_baord until response termination is reached
        and send it via signal for connected slot.
        """
        self.run_meas = True
        while self.run_meas:
            res = self.serial_read()
            if not res:
                break
            if res.endswith("#"):
                break
            res = res.split(" ")
            res = [int(val) for val in res if val.isdigit()]
            print("res: {}".format(res))
            self._distance_val = res
            time.sleep(0.1)


# Program entry when running this script directly
if __name__ == "__main__":
    my_reader = SensorBoardSerialInterface()
    print(my_reader.serial_list_devices())
