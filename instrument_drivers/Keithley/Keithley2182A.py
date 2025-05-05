from typing import Any
from qcodes.instrument.visa import VisaInstrument, VisaInstrumentKWArgs
from qcodes import Parameter
from qcodes.utils.validators import Numbers, Bool


class Keithley2182A(VisaInstrument):
    """
    QCoDeS driver for a generic voltmeter using SCPI commands.

    Provides parameters for:
      - Single voltage measurement
      - Range and autorange
      - Integration time (NPLC)
      - Digital filtering (count, window)
      - Analog low-pass filter
    """
    def __init__(
        self,
        name: str,
        address: str,
        terminator: str = '\n',
        **kwargs: VisaInstrumentKWArgs
    ):
        super().__init__(name, address, terminator=terminator, **kwargs)
        # Reset and basic configuration
        self.write('*CLS')
        self.write('CONF:VOLT')
        self.write('SENS:CHAN 1')
        self.write('SENS:VOLT:DFIL:TCON REP')
        self.write('SENS:VOLT:DFIL ON')

        # Voltage reading
        self.add_parameter(
            'voltage',
            label='Voltage',
            unit='V',
            get_cmd='INIT;FETC?',
            get_parser=float,
            docstring='Perform a single voltage measurement.'
        )

        # Fixed measurement range
        self.add_parameter(
            'range',
            label='Range',
            unit='V',
            get_cmd='SENS:VOLT:RANG?',
            set_cmd='SENS:VOLT:RANG {:f}',
            vals=Numbers(min_value=0, max_value=1e6),
            get_parser=float,
            docstring='Set or query the measurement range.'
        )

        # Autorange on/off
        self.add_parameter(
            'autorange',
            label='Autorange',
            get_cmd='SENS:VOLT:RANG:AUTO?',
            set_cmd='SENS:VOLT:RANG:AUTO {:s}',
            vals=Bool(),
            val_mapping={True: 'ON', False: 'OFF'},
            get_parser=lambda v: v.strip().upper() == 'ON',
            docstring='Enable or disable autoranging.'
        )

        # Integration time in power line cycles
        self.add_parameter(
            'nplc',
            label='Integration Time (NPLC)',
            get_cmd='SENS:VOLT:NPLC?',
            set_cmd='SENS:VOLT:NPLC {:d}',
            vals=Numbers(min_value=0.001, max_value=100),
            get_parser=float,
            docstring='Number of power line cycles for integration time.'
        )

        # Digital filter: sample count
        self.add_parameter(
            'averaging_count',
            label='Digital Filter Sample Count',
            get_cmd='SENS:VOLT:DFIL:COUNT?',
            set_cmd='SENS:VOLT:DFIL:COUNT {:d}',
            vals=Numbers(min_value=1, max_value=1e6),
            get_parser=int,
            docstring='Number of samples for digital averaging filter.'
        )

        # Digital filter: window size
        self.add_parameter(
            'averaging_window',
            label='Digital Filter Window',
            unit='V',
            get_cmd='SENS:VOLT:DFIL:WINDOW?',
            set_cmd='SENS:VOLT:DFIL:WINDOW {:f}',
            vals=Numbers(min_value=0.0, max_value=1e3),
            get_parser=float,
            docstring='Window size for digital averaging filter.'
        )

        # Analog low-pass filter on/off
        self.add_parameter(
            'analog_filter',
            label='Analog Low-pass Filter',
            get_cmd='SENS:VOLT:LPAS?',
            set_cmd='SENS:VOLT:LPAS {:s}',
            vals=Bool(),
            val_mapping={True: 'ON', False: 'OFF'},
            get_parser=lambda v: v.strip().upper() == 'ON',
            docstring='Enable or disable the analog low-pass filter.'
        )

        self.connect_message()

    def read(self) -> float:
        """
        Convenience method to read voltage.
        """
        return self.voltage()

