import time

import numpy as np
import functools
import ctypes
from ctypes import *
import typing
from Scripts.utils import LoggingClass
import os
from typing import Optional


class RaptorNinox640IIError(Exception):
    pass

class RaptorNinox640II(LoggingClass):

    #region Serial communication
    def serial_config(self):
        """
        Serial configuration for communication-> xclib.
        """
        err = self.xclib.pxd_serialConfigure(1, 0, c_double(115200), 8, 0, 1, 0, 0, 0)
        if err != 0:
            raise RaptorNinox640IIError(f"Error at serial config: {err}, {self._get_error()}")

    def _serial_read(self, length_answer: int) -> list:
        """
        Read data send by the camera
        Should not be used as is: use self.serial_ask instead.
        :param length_answer: length of the data expected according to the datasheet
        :return: Answer sent in hex ( for the ack/sum verification ).
        """
        read_buffer = np.zeros(length_answer, dtype=np.uint8)
        length = 0
        data = []
        i = 0
        # Waiting for data of the length in parameter
        while len(data) < length_answer:
            i += 1
            if i > 1000:
                time.sleep(0.1)
                self.logger.error("Stuck in serial read, {}".format(hex(x) for x in data))
            # Put data send by the camera into read_buffer and return the length of bytes of data read
            length = self.xclib.pxd_serialRead(1, 0, read_buffer.ctypes.data_as(ctypes.POINTER(ctypes.c_char)),
                                            len(read_buffer))
            data += list(read_buffer[:length])
        if length < 0:
            raise RaptorNinox640IIError(f"Error at serial read: {self._get_error()}")
        else:
            self.logger.debug(f"read <= {data}")
            return data

    def _serial_write(self, data: list) -> list:
        """
        Send the command to the camera.
        Should not be used as is: use self.serial_ask instead.
        :param data: Command to send.
        :return: Command sent in hex( for the ack/sum verification ).
        """
        data_ack = data + [0x50]
        data_ack_sum = data_ack + [functools.reduce(int.__xor__, data_ack)] #TODO: Error a comprendre
        err = self.xclib.pxd_serialWrite(1, 0, bytes(data_ack_sum), len(data_ack_sum))
        if err < 0:
            raise RaptorNinox640IIError(f"Error at serial write: {err}, {self._get_error()}")
        else:
            self.logger.debug(f"write => {data_ack_sum}")
            return data_ack_sum

    def _serial_ask(self, data: list, length_answer: Optional[int] = None) -> list:
        """
        Send a command and give the output back (write + read fct).
        Verification of the ack + sum at the end of the transmission.
        :param data: Command to send to the camera.
        :param length_answer: length of the data expected according to the datasheet
        :return: Answer in hex sent by the camera.
        """
        sent_data = self._serial_write(data)
        read_data = self._serial_read(length_answer)
        # Checksum of the data received
        for x in range(1, len(read_data)):
            if read_data[-x] == '0':
                x += 1
            elif read_data[-x] == sent_data[-1]:
                return read_data
            else:
                data_hex = list(map(hex, read_data))
                self.logger.error(f"Error at check sum: {hex(read_data[-x])}, list of data: {data_hex}, "
                                            f"Error: {self._get_error()}")
                raise RaptorNinox640IIError(f"Error at check sum: {hex(read_data[-x])}, list of data: {data_hex}, "
                                            f"Error: {self._get_error()}")

    def serial_set(self, data: list, length_answer: Optional[int] = 2):
        """
        Set the value of an attribute of the camera
        :param data: Command to send to the camera.
        :param length_answer: Length of the data that will be returned
        By default, length is 2 bytes for set command
        """
        return self._serial_ask(data, length_answer)

    def serial_get(self, data: list, length_answer):
        """
        Get the value of an attribute of the camera
        :param data: Command to send to the camera.
        :param length_answer: length of the data expected according to the datasheet
        Generally, data send is [data, 0x50, 0xE3]
        """
        return self._serial_ask(data, length_answer)

    #endregion

    def __init__(self):
        """
        Import the library & Connect with the camera.
        """
        LoggingClass.__init__(self)
        self.last_command = None  # Stock the last command send

        # Attribute for the Set Point Temperature Calibration
        self.constant_tec_get = 0
        self.slope_tec_get = 0
        self.constant_tec_set = 0
        self.slope_tec_set = 0

        self.xclib = WinDLL(os.path.join(os.path.dirname(__file__), "xclibw64.dll"))  # dll for the camera
        self._connect()
        self.serial_config()  # serial config xclib
        x = 0
        while x != '1':  # poll this command until the fpga has booted successfully
            # Not use serial ask because the sumcheck mode is not yet implemented
            # It implemented with this communication
            self._serial_write([0x49])
            status = self._serial_read(2)
            self.logger.debug("Get system status")
            # Above byte bit 2 = 1 indicates FPGA booted
            x = (bin(status[0]))[-3]
        # Set system status : bit 5 = 0 to enable external comm
        self.serial_set([0x4F, 0x73])
        self.logger.debug("Set system status")
        self.manufacturer_data()
        self.auto_exposure = 0

        self.width = 640
        self.height = 512

    def __del__(self):
        """
        Deconnection.
        """
        ret = self.xclib.pxd_PIXCIclose()
        if ret not in (0, -25):
            raise RaptorNinox640IIError("Error at disconnection:", self._get_error())

    def _get_error(self) -> c_char:
        """
        Print additional information about the cause of failure.
        """
        err_buf = create_string_buffer(500)
        err = self.xclib.pxd_mesgFaultText(1, err_buf, 500)
        if err == 1:
            return err_buf.value.decode("utf8")

    def _connect(self):
        """
        Connection.
        """
        ret = self.xclib.pxd_PIXCIopen(None, None, b"raptor_ninox_640.fmt")
        if ret != 0:
            ret = self.xclib.pxd_PIXCIopen(None, None, b"..\\raptor_ninox_640.fmt")
        error = self.xclib.pxd_mesgErrorCode(ret)
        if ret != 0:
            raise RaptorNinox640IIError("Error at connection:", self._get_error())

    def manufacturer_data(self):
        """
        Get manufacturer's data / later used information like ADC and DAC values
        """
        self.logger.debug("Ask for manufacturer data")
        self.serial_set([0x53, 0xAE, 0x05, 0x01, 0x00, 0x00, 0x02, 0x00])
        man_data = self.serial_get([0x53, 0xAF, 0x12], 20)

        # Need to turn in hexa to concatene 2 bytes with little endian method
        man_data_hex = [hex(x)[2:] for x in man_data]

        #region Calculation of DAC and ADC values

        ADC_0 = int((man_data_hex[11] + man_data_hex[10]), 16)
        ADC_4 = int((man_data_hex[13] + man_data_hex[12]), 16)

        DAC_0 = int((man_data_hex[15] + man_data_hex[14]), 16)
        DAC_4 = int((man_data_hex[17] + man_data_hex[16]), 16)

        if ADC_0 == ADC_4 or DAC_0 == DAC_4:
            self.logger.error(f"Error during reading of manufacturer data: {man_data_hex=}")

        #endregion

        # region Calculation of slope and constant for tec

        # Calculate the slope of the Set Point Temperature Calibration for get value
        self.slope_tec_get = (-40) / (ADC_0 - ADC_4)  # Equal m in the datasheet
        # Calculate the constant of the Set Point Temperature Calibration for get value
        self.constant_tec_get = 40 - (self.slope_tec_get * ADC_4)  # Equal c in the datasheet

        # Calculate the slope of the Set Point Temperature Calibration for set value
        self.slope_tec_set = (-40) / (DAC_0 - DAC_4)  # Equal m in the datasheet
        # Calculate the constant of the Set Point Temperature Calibration for get value
        self.constant_tec_set = 40 - (self.slope_tec_set * DAC_4)  # Equal c in the datasheet

        #endregion

        sn = (int(man_data_hex[1], 16) << 8 | int(man_data_hex[0], 16))
        build_date = f"{int(man_data_hex[2], 16)} / {int(man_data_hex[3], 16)} / {int(man_data_hex[4], 16)}"

        # Data for capturing picture
        self.xdim = self.xclib.pxd_imageXdims()
        self.ydim = self.xclib.pxd_imageYdims()
        bit_per_pixel = self.xclib.pxd_imageCdim() * self.xclib.pxd_imageBdim()

        self.data_manufacturer = [sn, build_date, ADC_0, ADC_4, DAC_0, DAC_4, bit_per_pixel,
                self.xdim, self.ydim]
        return self.data_manufacturer

    def information(self):
        """
        Get Information - Only to display it later.
        """
        # get system status
        sys = self.serial_get([0x49], 3)
        status = "{0:08b}".format(sys[0])

        FPGA_booted_success = status[-3]
        FPGA_not_in_reset = status[-2]
        comm_to_EPROM = status[-1]

        # get micro version
        mic = self.serial_get([0x56], 4)
        micro_version = f"v{mic[0]}.{mic[1]}"
        # get fpga version
        self.serial_set([0x53, 0xE0, 0x01, 0x7E])
        v1 = self.serial_get([0x53, 0xE1, 0x01], 3)
        self.serial_set([0x53, 0xE0, 0x01, 0x7F])
        v2 = self.serial_get([0x53, 0xE1, 0x01],3)
        fpga_version = f"v{v1[0]}.{v2[0]}"

        info = [FPGA_booted_success, FPGA_not_in_reset, comm_to_EPROM,
                micro_version, fpga_version]
        return info

    def capture_img(self) -> np.ndarray:
        """
        Capture image into buffer 1 and into self.last_img
        :return: raw image data in an array
        """
        # Capturing a single image
        error = self.xclib.pxd_doSnap(1, 1, 0)
        if error > 0:
            raise RaptorNinox640IIError("Error at capture image:", self._get_error())

        # Create dimension of the picture
        self.last_img = np.zeros(self.xdim*self.ydim).astype(np.uint16)

        cx = 0  # x of the upper left corner
        cy = 0  # y of the upper left corner

        # Write the value of the new image into last_image variable in a grey shade
        error = self.xclib.pxd_readushort(1, 1, cx, cy, -1, -1,
                                          self.last_img.ctypes.data_as(ctypes.POINTER(ctypes.c_ushort)),
                                          self.xdim*self.ydim, b"Grey")
        if error < 0:
            raise RaptorNinox640IIError("Error at saving data -> buffer", self._get_error())

        # Put 2 dimensional array for height x width
        self.last_img =  self.last_img.reshape(self.width, self.height)
        # Put the array into 16 bits value
        self.last_img = self.last_img * 4

        return self.last_img

    def save_bmp(self):
        """
        Save the picture that was in the buffer in a format bmp
        """
        name = b'img_cam.bmp'
        err = self.xclib.pxd_saveBmp(1, name, 1, 0, 0, -1, -1, 0, 0)
        if err < 0:
            raise RaptorNinox640IIError("Error at saving image:", self._get_error())

    def micro_reset(self):
        self.serial_set([0x55, 0x99, 0x66, 0x11], 0)

    def get_fpga_status(self):
        self.serial_set([0x53, 0xE0, 0x01, 0x00])
        state = self.serial_get([0x53, 0xE1, 0x01], 3)
        state = (bin(state[0])[2:]).zfill(8)
        self.fan_enable = state[-3]
        self.auto_expo_enable = state[-2]
        self.tec_enable = state[-1]
        self.horiz_flip_cap = state[0]
        self.invert_cap = state[1]

    #region Setter and getter of the attributes

    @property
    def fan(self) -> int:
        self.get_fpga_status()
        return 1 if self.fan_enable == '1' else 0

    @fan.setter
    def fan(self, fan_state: typing.Union[int, bool]):
        fan_state = int(fan_state)
        self.get_fpga_status()
        init = (self.horiz_flip_cap, self.invert_cap, 0, 0, 0, fan_state, self.auto_expo_enable, self.tec_enable)
        init = "0x{:02x}".format(int("".join(str(ele) for ele in init), 2))
        self.serial_set([0x53, 0xE0, 0x02, 0x00, int(init, 16)])

    @property
    def tec_activation(self) -> int:
        self.get_fpga_status()
        return 1 if self.tec_enable == '1' else 0

    @tec_activation.setter
    def tec_activation(self, tec_state: typing.Union[int, bool]):
        tec_state = int(tec_state)
        self.get_fpga_status()
        init = (self.horiz_flip_cap, self.invert_cap, 0, 0, 0, self.fan_enable, self.auto_expo_enable, tec_state)
        init = "0x{:02x}".format(int("".join(str(ele) for ele in init), 2))
        self.serial_set([0x53, 0xE0, 0x02, 0x00, int(init, 16)])

    @property
    def tec(self) -> float:
        """
        :return: ThermoElectric Cooler Setpoint
        """
        self.serial_set([0x53, 0xE0, 0x01, 0xFB])
        msb = self.serial_get([0x53, 0xE1, 0x01], 3)
        self.serial_set([0x53, 0xE0, 0x01, 0xFA])
        lsb = self.serial_get([0x53, 0xE1, 0x01], 3)
        tec = (self.slope_tec_get * (msb[0] << 8 | lsb[0])) + self.constant_tec_get
        return tec

    @tec.setter
    def tec(self, tec_val: float):
        """
        Set TEC Value
        """
        val = (tec_val - self.constant_tec_set) / self.slope_tec_set
        tec = '0x{:04x}'.format(int(val))
        self.serial_set([0x53, 0xE0, 0x02, 0xFB, int(tec[2:4], 16)])
        self.serial_set([0x53, 0xE0, 0x02, 0xFA, int(tec[4:6], 16)])

    @property
    def temp(self):
        """
        :return: Sensor Temperature CDD Cooler
        """
        self.serial_set([0x53, 0xE0, 0x01, 0x6E])
        temp1 = self.serial_get([0x53, 0xE1, 0x01], 3)
        self.serial_set([0x53, 0xE0, 0x01, 0x6F])
        temp2 = self.serial_get([0x53, 0xE1, 0x01], 3)
        temp = self.slope_tec_get * (temp1[0] << 8 | temp2[0]) + self.constant_tec_get  # from adc values
        return temp

    @property
    def temp_pcb(self):
        """
        :return: Sensor Temperature PCB
        """
        self.serial_set([0x53, 0xE0, 0x01, 0x70])
        msb = self.serial_get([0x53, 0xE1, 0x01], 3)
        self.serial_set([0x53, 0xE0, 0x01, 0x71])
        lsb = self.serial_get([0x53, 0xE1, 0x01], 3)
        temp_pcb = ((msb[0] & 0b1111) << 8 | lsb[0])
        left_part = -2 ** 12 + (temp_pcb >> 4) & 0b111_1111_1111 if (temp_pcb >> 11) else temp_pcb >> 4
        right_part = (temp_pcb & 0b1111) * 1 / 16
        return left_part + right_part

    @property
    def gain(self):
        """
        :return: 1 = High Gain  0 = Low Gain
        """
        self.serial_set([0x53, 0xE0, 0x01, 0xF2])
        state = self.serial_get([0x53, 0xE1, 0x01], 3)
        state = (bin(state[0])[2:]).zfill(8)
        return 1 if state[-2] and state[-3] == '1' else 0

    @gain.setter
    def gain(self, state):
        """
        Set gain: 1 = High Gain  0 = Low Gain
        """
        self.serial_set([0x53, 0xE0, 0x02, 0xF2, 0x06]) if state else self.serial_set([0x53, 0xE0, 0x02, 0xF2, 0x00])

    @property
    def digital_gain(self):
        """
        Return the value of the digital gain
        According to the datasheet of the camera, the digital gain is a different parameter than gain
        :return: Value of the digital gain of the camera. Max value: 65535, min value: 0
        """
        self.serial_set([0x53, 0xE0, 0x01, 0xC6])
        gain_msb = self.serial_get([0x53, 0xE1, 0x01], 3)[0]
        self.serial_set([0x53, 0xE0, 0x01, 0xC7])
        gain_lsb = self.serial_get([0x53, 0xE1, 0x01], 3)[0]

        print(gain_msb << 8 | gain_lsb)

        return gain_msb << 8 | gain_lsb

    @digital_gain.setter
    def digital_gain(self, value):
        """
        Set digital gain of the camera
        According to the datasheet of the camera, the digital gain is a different parameter than gain
        :param value: Max value: 65535, min value: 0
        """
        if value > 65535 or value < 0:
            self.logger.error("Wrong value to digital gain setter")
            return

        self.serial_set([0x53, 0xE0, 0x02, 0xC6, (value >> 8) & 0xFF])
        self.serial_set([0x53, 0xE0, 0x02, 0xC7, value & 0xFF])

    @property
    def auto_level(self) -> int:
        self.serial_set([0x53, 0xE0, 0x01, 0x23])
        msb = self.serial_get([0x53, 0xE1, 0x01], 3)
        self.serial_set([0x53, 0xE0, 0x01, 0x24])
        lsb = self.serial_get([0x53, 0xE1, 0x01], 3)
        auto_level = (msb[0] << 8 | lsb[0]) >> 2
        return auto_level

    @auto_level.setter
    def auto_level(self, value: int):
        # Max value of the auto level is 0x3FFF = 16383
        if value > 16383:
            value = 16383
            self.logger.error("Value of auto level too high")

        auto_level = '{0:014b}'.format(value)
        lsb = f"{auto_level[8:14]}00"
        self.serial_set([0x53, 0xE0, 0x02, 0x23, int(auto_level[0:8], 2)])  # Send MM bits
        self.serial_set([0x53, 0xE0, 0x02, 0x24, int(lsb, 2)])  # Send LL bits

    @property
    def exposure(self) -> int:
        """
        :return: Time of exposure in seconds
        min = 500ns
        """
        self.serial_set([0x53, 0xE0, 0x01, 0xEE])  # msb
        msb = self.serial_get([0x53, 0xE1, 0x01], 3)
        self.serial_set([0x53, 0xE0, 0x01, 0xEF])  # mid upper bit
        midu = self.serial_get([0x53, 0xE1, 0x01], 3)
        self.serial_set([0x53, 0xE0, 0x01, 0xF0])  # mid low bit
        midl = self.serial_get([0x53, 0xE1, 0x01], 3)
        self.serial_set([0x53, 0xE0, 0x01, 0xF1])  # lsb
        lsb = self.serial_get([0x53, 0xE1, 0x01], 3)

        value = msb[0] << 24 | midu[0] << 16 | midl[0] << 8 | lsb[0]
        return value

    @exposure.setter
    def exposure(self, exp: float):
        """
        :param exp: exposition value in seconds between 500ns and 26.8s
        """
        if not (500e-9 < exp < 26.8):
            self.logger.error("Wrong value or unit for the exposure value send")
            return

        # Divide to find 1 count
        # multiply by 4e7 = divide by 25e-9, 1 count
        exp = int(exp*40_000_000)
        exp = "0x{:08x}".format(exp)
        self.serial_set([0x53, 0xE0, 0x02, 0xEE, int(exp[2:4], 16)])  # msb
        self.serial_set([0x53, 0xE0, 0x02, 0xEF, int(exp[4:6], 16)])  # midu
        self.serial_set([0x53, 0xE0, 0x02, 0xF0, int(exp[6:8], 16)])  # midl
        self.serial_set([0x53, 0xE0, 0x02, 0xF1, int(exp[8:10], 16)])  # lsb

    @property
    def auto_exposure(self) -> int:
        self.get_fpga_status()
        return 1 if self.auto_expo_enable == '1' else 0

    @auto_exposure.setter
    def auto_exposure(self, au_exp_state: int):
        self.get_fpga_status()
        init = (self.horiz_flip_cap, self.invert_cap, 0, 0, 0, self.fan_enable, au_exp_state, self.tec_enable)
        init = "0x{:02x}".format(int("".join(str(ele) for ele in init), 2))
        self.serial_set([0x53, 0xE0, 0x02, 0x00, int(init, 16)])

    @property
    def invert_video(self) -> int:
        self.get_fpga_status()
        return 1 if self.invert_cap == '1' else 0

    @invert_video.setter
    def invert_video(self, invert_state: int):
        self.get_fpga_status()
        init = (self.horiz_flip_cap, invert_state, 0, 0, 0, self.fan_enable, self.auto_expo_enable, self.tec_enable)
        init = "0x{:02x}".format(int("".join(str(ele) for ele in init), 2))
        self.serial_set([0x53, 0xE0, 0x02, 0x00, int(init, 16)])

    @property
    def horiz_flip(self) -> int:
        self.get_fpga_status()
        return 1 if self.horiz_flip_cap == '1' else 0

    @horiz_flip.setter
    def horiz_flip(self, horiz_flip_state: int):
        self.get_fpga_status()
        init = (horiz_flip_state, self.invert_cap, 0, 0, 0, self.fan_enable, self.auto_expo_enable, self.tec_enable)
        init = "0x{:02x}".format(int("".join(str(ele) for ele in init), 2))
        self.serial_set([0x53, 0xE0, 0x02, 0x00, int(init, 16)])

    #endregion

if __name__ == '__main__':
    pass
    # cam = RaptorNinox640II()
    # cam.fan = 0
    # cam.tec_activation = 1
    # print(f"{cam.tec}")
    # cam.tec = -15
    # print(f"{cam.temp}")
    # print(f"{cam.temp_pcb}")
    # print(f"{cam.gain=}")
    # cam.gain = 1
    # print(f"{cam.gain=}")
    # print(f"{cam.exposure}")
    # cam.exposure = 1500e-6
    # print(f"{cam.exposure}")
    # print(f"{cam.invert}")
    # cam.invert = 1
    # print(f"{cam.invert}")
    # print(f"{cam.horiz_flip}")
    # cam.horiz_flip = 1
    # print(f"{cam.horiz_flip}")
    #
    # cam.auto_level = 1564
    # print(f"{cam.auto_level=}")
    # cam.auto_level = 2
    # print(f"{cam.auto_level=}")



