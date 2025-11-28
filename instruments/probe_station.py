import time
from typing import Optional, Literal

import numpy as np
from numpy.typing import NDArray

from ..instrument_drivers.Keithley.Keithley2182A import Keithley2182A
from ..instrument_drivers.Keithley.Keithley2400 import Keithley2400


class ProbeStation:
    """
    Class to perform I-V sweeps in 2-wire or 4-wire mode using a source-meter
    and optionally a separate voltmeter.

    Modes:
      - '4wire': uses dedicated voltmeter for voltage measurement
      - '2wire': uses source-meter for both voltage and current

    Automatically selects 4-wire if a voltmeter instance is provided.
    """
    def __init__(
        self,
        source: Keithley2400,
        voltmeter: Optional[Keithley2182A] = None
    ) -> None:
        self._source = source
        self._voltmeter = voltmeter
        # auto-select mode based on voltmeter presence
        self.mode: Literal['2wire', '4wire'] = (
            '4wire' if self._voltmeter is not None else '2wire'
        )

        self._delay = 0.01

        # default settings
        self.nplc(1)
        self._source.terminals('rear')
        self._source.write(':SENSe:RESistance:MODE MAN') # probably can be deleted
        self._source.mode('VOLT')
        self._source.rangev(210e-3)
        self._source.volt(0.03)
        self._source.output(True)

    def set_mode(self, mode: Literal['2wire', '4wire']) -> None:
        """
        Switch between 2-wire and 4-wire measurement modes.

        Raises if selecting 4-wire without a voltmeter.
        """
        if mode not in ('2wire', '4wire'):
            raise ValueError("Mode must be '2wire' or '4wire'")
        if mode == '4wire' and not self._voltmeter:
            raise RuntimeError("Cannot enable 4-wire mode without a voltmeter instrument")
        self.mode = mode

    def _measure_cv_4_wire(self) -> tuple[float, float, float]:
        """
        Perform a single 4-wire measurement: trigger both instruments,
        read voltage from voltmeter, current from source-meter,
        and source-meter's own voltage measurement.
        Returns (voltage_voltmeter, current, voltage_source).
        """
        # initiate measurements
        self._source.write('INIT')
        time.sleep(self._delay)
        self._voltmeter.write('INIT')
        # voltmeter reading
        voltage_voltmeter = float(self._voltmeter.ask('FETC?'))
        # source-meter returns '<voltage>,<current>'
        resp = self._source.ask('FETC?').split(',')
        voltage_source = float(resp[0])
        current = float(resp[1])
        return voltage_voltmeter, current, voltage_source


    def _measure_cv_2_wire(self) -> tuple[float, float]:
        """
        Perform a single 2-wire measurement: trigger source-meter,
        read both voltage and current from its response.
        Returns (voltage, current).
        """
        self._source.write('INIT')
        resp = self._source.ask('FETC?').split(',')
        voltage = float(resp[0])
        current = float(resp[1])
        return voltage, current

    def measure_cvc(
            self,
            voltages: NDArray[float]
    ) -> tuple[NDArray[float], NDArray[float], NDArray[float] | None]:
        """
        Sweep a list of setpoint voltages, measure each point in the
        selected mode, and return arrays of measured voltages and currents.

        For 4-wire mode, also returns the source-meter's voltage readings.

        Returns:
          - 2-wire: (meas_v, meas_i, None)
          - 4-wire: (meas_v_voltmeter, meas_i, meas_v_source)
        """
        meas_v: list[float] = []
        meas_i: list[float] = []
        meas_v_source: list[float] = []  # only used in 4-wire
        for v_set in voltages:
            self._source.volt(v_set)
            if self.mode == '4wire':
                v_voltm, i, v_src = self._measure_cv_4_wire()
                meas_v.append(v_voltm)
                meas_i.append(i)
                meas_v_source.append(v_src)
            else:
                v, i = self._measure_cv_2_wire()
                meas_v.append(v)
                meas_i.append(i)
        v_arr = np.array(meas_v)
        i_arr = np.array(meas_i)
        if self.mode == '4wire':
            return v_arr, i_arr, np.array(meas_v_source)
        else:
            return v_arr, i_arr, None

    def nplc(self, value: int) -> None:
        """
        Set integration time (NPLC) on both instruments if available.
        """
        self._source.nplcv(value)
        if self._voltmeter:
            self._voltmeter.nplc(value)
