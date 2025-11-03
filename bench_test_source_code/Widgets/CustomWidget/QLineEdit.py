import re
from collections import OrderedDict
from decimal import Decimal
from typing import Optional

from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QValidator
from PyQt6.QtWidgets import QDoubleSpinBox, QAbstractSpinBox, QWidget


# Made by SMR
class ValueWithUnitInputWidget(QDoubleSpinBox):
    """
    DoubleSpinBox enhanced with units prefixes (micro, mega, etc.)

    Decimals are used in this class to get rid of float approximation problems.
    """

    SI_PREFIXES = OrderedDict([
        ('p', -12),
        ('n', -9),
        ('u', -6),
        ('m', -3),
        ('', 0),
        ('k', 3),
        ('M', 6),
        ('G', 9)
    ])

    def __init__(self,
                 parent: Optional[QWidget],
                 unit: 'str',
                 min_: Optional[int] = None,
                 max_: Optional[int] = None,
                 step: Optional[Decimal] = None):
        """
        Constructor.
        :param parent: parent widget
        :param unit: suffix of DoubleSpinBox (for example: 's' for seconds)
        :param min_: minimum value
        :param max_: maximum value
        :param step: minimal step, resolution of the value
        """
        QDoubleSpinBox.__init__(self, parent)

        self._unit = unit
        self._step = step or Decimal("0.0000005")  # Initially the step is set at 500ns
        self.__REGEXP = rf'([+|-]?\d+(,\d+)?)([a-zA-Z]?)({self._unit})'

        self.setSuffix(self._unit)
        self.setDecimals(12)
        self.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)

        if min_:
            self.setMinimum(min_)
        if max_:
            self.setMaximum(max_)
        self.setSingleStep(float(self._step))

        self.textChanged.connect(self.text_changed_handler)

    def text_changed_handler(self):
        """
        Changes color of text regarding whether it is a valid IP address or not
        """
        color = 'red' if not self.hasAcceptableInput() else 'black'
        self.setStyleSheet(f"color: {color}")

    def _parse_text(self, text: str) -> tuple[str, str, str]:
        """
        Parses the given text
        :param text: text to parse
        :return: number, si_prefix and unit parts of the string
        """
        text = text.replace(' ', '')

        number, _, si_prefix, unit = re.search(self.__REGEXP, text).groups()
        return number, si_prefix, unit

    def validate(self, text: str, pos: int) -> (QValidator.State, str, int):
        """
        Checks the current text and validates it or not
        :param text: text to check
        :param pos: cursor position
        :return: validation status, new text, new cursor position
        """
        try:
            number, si_prefix, unit = self._parse_text(text)
        except AttributeError:
            return QValidator.State.Intermediate, text, pos

        # refuse bad prefixes
        if si_prefix not in self.SI_PREFIXES.keys():
            return QValidator.State.Invalid, f"{number} {si_prefix}{unit}", pos

        return QValidator.State.Acceptable, f"{number} {si_prefix}{unit}", pos

    def valueFromText(self, text: str) -> float:
        """
        Gets the value from the given text
        :param text: text to parse
        :return: float value
        """
        number, si_prefix, unit = self._parse_text(text)
        number = number.replace(',', '.')

        return float(Decimal(number) * Decimal(10 ** self.SI_PREFIXES[si_prefix]))



    def textFromValue(self, v: float) -> str:
        """
        Constructs a text for the given value
        :param v: value to work on
        :return: text that is acceptable in this widget
        """
        # handle trivial corner case
        if v == 0:
            return "0,000"

        # enumerate all prefixes to pick the best one (not to express 1.0 as "1000000000 ns")
        take_it = False
        for idx, item in enumerate(self.SI_PREFIXES.items()):
            letter, exp = item[0], item[1]

            if exp != 0:
                tmp = Decimal(str(v)) / Decimal(f"1e{exp}")
                tmp = tmp.quantize(self._step / Decimal(f"1e{exp}"))
            else:
                tmp = Decimal(str(v)).quantize(self._step)

            if take_it or idx == len(self.SI_PREFIXES) - 1 or tmp < 1000:
                res = f"{tmp:.3f} {letter}"
                return res.replace('.', ',')

            if int(tmp) % 1000 == 0:
                continue

            take_it = True
