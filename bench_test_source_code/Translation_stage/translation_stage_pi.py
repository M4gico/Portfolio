"""
Classe de gestion de la platine de translation du banc EMMI
"""
import time
from copy import deepcopy
from typing import Union

from serial import Serial
import serial
from toolbox3.geometry.point import Point3D
from toolbox3.instrumentation.generic.generic import Generic
import logging

from Scripts.utils import LoggingClass

logger = logging.getLogger()

class TranslationStageError(Exception):
    pass


"""
For send command to specific axis, the doc tell "<command> <AxisID> <value>"
To do this, use instead this syntax to communicate with axis X, Y and Z : "<AxisID> <command> 1 <value>"
"""
class TranslationPi(Serial, Generic, LoggingClass):

    #region Serial communication
    def write(self, msg: str):
        msg += '\n'
        self.logger.debug(f"write => {msg.encode()}")
        #ERROR#
        try:
            super().write(msg.encode('ascii'))
        except:
            print(f"{msg=}")
            raise TranslationStageError(f"Message error: {msg=}")

    def read_until(self, terminator=serial.LF, size=None):
        resp = super().read_until(terminator, size)
        self.logger.debug(f"read <= {resp}")
        # print(f"read <= {resp}")
        try:
            return_value = resp.decode('ascii').strip('\n')
        except:
            error = self.ask("ERR?")
            raise TranslationStageError(f"return value error: {resp=}, error code: {error=}")
        return return_value

    def write_ask(self, msg: str):
        """
        Create a seperate write method to put a mutex for ask and write method independently
        """
        msg += '\n'
        self.logger.debug(f"write => {msg.encode()}")
        try:
            super().write(msg.encode('ascii'))
        except Exception as e:
            raise TranslationStageError(f"Message error: {msg=}, error: {e}")


    def ask(self, msg: str, data_size_received=None) -> str:
        self.write_ask(msg)
        return self.read_until(serial.LF, data_size_received)

    #endregion

    def __init__(self, **kwargs):
        Serial.__init__(self, **kwargs)
        Generic.__init__(self)
        LoggingClass.__init__(self)

        # position infos
        pos_min = [self.ask(f"{axis} TMN? 1") for axis in range(1, 4)]
        self._pos_min = [float(i.split('=')[-1]) for i in pos_min]
        self.__physical_limit_min = deepcopy(self._pos_min)
        pos_max = [self.ask(f"{axis} TMX? 1") for axis in range(1, 4)]
        self._pos_max = [float(i.split('=')[-1]) for i in pos_max]
        self.__physical_limit_max = deepcopy(self._pos_max)

        # Put initial speed
        self.speed = 20
        self.acceleration = 400

        self.joystick_activation = False
        self.is_joystick_init = False
        self.is_axis_init = False

    def get_limit_min(self, axis):
        return self._pos_min[axis - 1]

    def set_limit_min(self, axis, lim_min):
        if not self.__physical_limit_min[axis - 1] <= lim_min <= self.__physical_limit_max[axis - 1]:
            raise ValueError("Limit is out of physical boundaries")
        self._pos_min[axis - 1] = lim_min

    def get_limit_max(self, axis):
        return self._pos_max[axis - 1]

    def set_limit_max(self, axis, lim_max):
        if not self.__physical_limit_min[axis - 1] <= lim_max <= self.__physical_limit_max[axis - 1]:
            raise ValueError("Limit is out of physical boundaries")
        self._pos_max[axis - 1] = lim_max

    def init_joystick(self):
        """
        Initialisation of the joystick.
        """
        self.write(f"JAX 1 1 1")  # Set Joystick for each axis
        self.ask(f"1 JAX?")  # Get Joystick Activation Status
        self.write(f"JAX 1 2")  # Set Joystick for each axis
        self.ask(f"2 JAX? 1 1")  # Get Joystick Activation Status
        self.write(f"JAX 1 3")  # Set Joystick for each axis
        self.ask(f"3 JAX? 1 1")  # Get Joystick Activation Status
        self.is_joystick_init = True

    def init_axis(self):
        """
        Initialisation of the axis
        """
        for i in range(1, 4):
            self._init_axis(i)
            print(f"init axis {i=}")
            self.logger.debug(f"init axis {i=}")

        self.is_axis_init = True

    def _init_axis(self, axis: int):
        """
        Initialization : Activation of the motor and reference movement for the chosen axis.
        :param axis : X = 1, Y = 2, Z = 3
        """
        self.write(f"{axis} SVO 1 1")  # Motor ON
        motor = self.ask(f"{axis} SVO? 1")  # Get motor state
        if motor[6] != '1':
            raise TranslationStageError(f"Motor {axis} OFF!")
        self.write(f"{axis} FNL 1")  # Referencing move to the negative limit (0)
        ref = self.ask(f"{axis} FRF? 1")  # Get Referencing Result
        if ref[6] != '0':
            raise TranslationStageError(f"Axis {axis} not referenced")

    def info(self) -> str:
        """
        :return: Serial numbers of the 3 axis.
        """
        sn = {"axis" + str(num): self.ask(f'{num} *IDN?') for num in range(1, 4)}
        return "1:\t{axis1}\n2:\t{axis2}\n3:\t{axis3}".format(**sn)

    def get_position(self) -> Point3D:
        """
        :return: Actual position of the axis.
        """
        pos = [self.ask(f"{axis} POS? 1") for axis in range(1, 4)]
        pos = [float(i.split('=')[-1]) for i in pos]
        pos = Point3D(*pos)
        return pos

    def is_any_axis_moving(self) -> bool:
        """
        Check if any axis moving
        :return: true: at least one axis moving - false: no axis moving
        """
        check_value = [True, True, True]

        for i in range(0, 3):
            check_value[i] = self.is_axis_moving(i+1)

        # If all axis stop moving, return false
        return not all(x == False for x in check_value)

    def is_axis_moving(self, axis) -> bool:
        """
        Ask if at least one of the axis is moving.
        :return: true: axis moving - false: no axis moving
        """
        if axis not in (1, 2, 3) :
            self.logger.error("ERROR: Wrong axis to check")
            return
        mvt = self.ask(f"{axis} SRG? 1 1")  # Query Status Register Value
        mvt = mvt.split('=0x')[-1]
        mvt = int(mvt, base=16) >> 13 & 1
        return not mvt == 0

    def set_origin(self):
        """
        Actual position become the origin axis
        """
        self.write('DFH')

    def joystick(self, on_off: Union[bool, int]):
        """
        Activate or deactivate the use of the joystick
        :param on_off: true : joystick ON  -  false : joystick off
        """
        self.joystick_activation = bool(on_off)

        on_off = int(on_off)
        for axis in range(1, 4):
            self.write(f"{axis} JON 1 {on_off}")  # Set Joystick for each axis
            j = self.ask(f"{axis} JON? 1")  # Get Joystick Activation Status
            if j[-1] != str(int(on_off)):
                raise TranslationStageError(f"Joystick {axis} deactivated")

    def move_relative(self, pos: Point3D) -> bool:
        """
        Move to a relative position
        :param pos: Wished Position :(x,y,z)
        """
        act_pos = self.get_position()
        for i in range(1, 4):
            if not (self._pos_min[i - 1]-act_pos[i-1]) <= pos[i - 1] <= (self._pos_max[i - 1]-act_pos[i-1]):
                self.logger.error(f"Position {i} out of range")
                return False
            self.write(f"{i} MVR 1 {pos[i - 1]}")  # Move relative instruction for each axis
        return True

    def move_absolute(self, pos: Point3D):
        """
        Move to an absolute position
        :param pos: Wished Position :(x,y,z)
        :return: Final Position after the movements
        """
        for i in range(1, 4):
            if not self._pos_min[i - 1] <= pos[i - 1] <= self._pos_max[i - 1]:  # error if the position is out of range
                raise ValueError("Position out of range")
            self.write(f"{i} MOV 1 {pos[i - 1]}")  # move absolute instruction for each axis

    @property
    def acceleration(self):
        return self.ask(f"1 ACC? 1")

    @acceleration.setter
    def acceleration(self, value: float):
        """
        :param value: Value of the acceleration of axis, max = 400
        """
        for i in range(1, 4):
            self.write(f"{i} ACC 1 {value}")  # Change value
            acceleration_value = self.ask(f"{i} ACC? 1")  # Get the value
            self.logger.debug(f"acceleration:: axis: {i}, value: {acceleration_value}")

    @property
    def speed(self):
        return self.ask(f"1 VEL? 1")

    @speed.setter
    def speed(self, value: float):
        """
        :param value: Value of the speed of axis, max = 20
        """
        for i in range(1, 4):
            self.write(f"{i} VEL 1 {value}")  # Change value
            velocity_value = self.ask(f"{i} VEL? 1")  # Get value
            self.logger.debug(f"speed:: axis: {i}, value: {velocity_value}")

    def stop(self):
        self.write("STOP")


if __name__ == "__main__":
    pi = TranslationPi(port="COM4", baudrate=115200)
    # pi.init_axis()
    # print(pi.init_axis())
#     time.sleep(3)
#     print(pi.get_position())
#     position = Point3D(40, 40, 40)
#     print(pi.joystick(0))
#     print(pi.stop())
#     print(pi.init_joystick())
#     print(pi.joystick(0))
#     print(pi.get_position())
#     print(pi.move_absolute(position))
#     position = Point3D(52, 30, 35.5)
#     print(pi.move_absolute(position))
#     print(pi.get_position())
#     print(pi._is_moving())
