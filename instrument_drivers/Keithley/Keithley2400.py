from typing import Unpack

from qcodes import Parameter
from qcodes.instrument import VisaInstrumentKWArgs, InstrumentModule
from qcodes.instrument_drivers.Keithley.Keithley_2400 import Keithley2400 as Keithley2400Base
from qcodes.validators import Enum


class Beeper(InstrumentModule):
    def __init__(self, parent: 'Keithley2400', name: str):
        super().__init__(parent, name)

    def beep(self, freq: float = None, duration: float = None):
        """
        Emit a sound beep with a frequency between 65 Hz and 2 MHz
        and a duration between 0 and 7.9 seconds.
        """
        if freq is None or duration is None:
            raise ValueError("Both 'freq' and 'duration' must be provided")
        if not (65 <= freq <= 2e6):
            raise ValueError("Frequency must be between 65 Hz and 2 MHz")
        if not (0 <= duration <= 7.9):
            raise ValueError("Duration must be between 0 and 7.9 seconds")
        self.parent.write(f":SYSTem:BEEPer {freq},{duration}")

    def success(self):
        self.beep(800, 1)


class Keithley2400(Keithley2400Base):
    def __init__(self, name: str, address: str, **kwargs: "Unpack[VisaInstrumentKWArgs]"):
        super().__init__(name, address, **kwargs)

        # Add the beeper submodule for audible feedback
        self.add_submodule('beeper', Beeper(self, 'beeper'))

        # Parameter to select front or rear panel input/output terminals
        # val_mapping allows pythonic inputs 'front'/'rear' to map to SCPI 'FRONt'/'REAR'
        self.add_parameter(
            'route_terminals',
            label='Input/Output Terminals',
            parameter_class=Parameter,
            docstring='Select front or rear panel input/output jacks.',
            get_cmd=':ROUTe:TERMinals?',
            set_cmd=':ROUTe:TERMinals {value}',
            vals=Enum('front', 'rear'),
            val_mapping={
                'front': 'FRONt',
                'rear': 'REAR'
            }
        )
