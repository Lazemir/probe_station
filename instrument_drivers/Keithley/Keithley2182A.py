from typing import Any

from qcodes.instrument import InstrumentModule
from qcodes.instrument.visa import VisaInstrument, VisaInstrumentKWArgs
from qcodes import Parameter
from qcodes.utils.validators import Numbers, Bool
from qcodes.validators import Enum


class FilterModule(InstrumentModule):
    """
    Subsystem for analog and digital filtering settings.
    """
    def __init__(self, parent: 'Keithley2182A', name: str) -> None:
        super().__init__(parent, name)
        # Digital filter enable/disable
        self.state = self.add_parameter(
            'state',
            label='Digital Filter Enable',
            get_cmd='SENS:VOLT:DFIL:STATe?',
            set_cmd='SENS:VOLT:DFIL:STATe {}',
            vals=Bool(),
            val_mapping={True: 'ON', False: 'OFF'},
            get_parser=lambda v: v.strip().upper() == 'ON',
            docstring='Enable or disable the digital filter.'
        )
        # Digital filter type
        self.type = self.add_parameter(
            'type',
            label='Digital Filter Type',
            get_cmd='SENS:VOLT:DFIL:TCON?',
            set_cmd='SENS:VOLT:DFIL:TCON {}',
            vals=Enum('MOVing', 'REPeat'),
            val_mapping={'moving': 'MOVing', 'repeat': 'REPeat'},
            get_parser=lambda v: v.strip(),
            docstring='Select digital filter type: MOVing or REPeat.'
        )
        # Digital filter sample count
        self.count = self.add_parameter(
            'count',
            label='Digital Filter Sample Count',
            get_cmd='SENS:VOLT:DFIL:COUNT?',
            set_cmd='SENS:VOLT:DFIL:COUNT {}',
            vals=Numbers(min_value=1, max_value=100),
            get_parser=int,
            docstring='Number of samples for digital averaging filter.'
        )
        # Digital filter window percent
        self.window = self.add_parameter(
            'window',
            label='Digital Filter Window',
            unit='%',
            get_cmd='SENS:VOLT:DFIL:WINDOW?',
            set_cmd='SENS:VOLT:DFIL:WINDOW {}',
            set_parser=lambda v: 'NONE' if v is None else str(v),
            get_parser=lambda v: None if v.strip().upper() == 'NONE' else float(v),
            docstring=('Digital filter window as percent of range ' 
                       '(0.01–10%), or None to disable (NONE).')
        )
        # Analog low-pass filter
        self.analog = self.add_parameter(
            'analog',
            label='Analog Low-pass Filter',
            get_cmd='SENS:VOLT:LPAS?',
            set_cmd='SENS:VOLT:LPAS {}',
            vals=Bool(),
            val_mapping={True: 'ON', False: 'OFF'},
            get_parser=lambda v: v.strip().upper() == 'ON',
            docstring='Enable or disable the analog low-pass filter.'
        )

        # Default settings
        self.state(True)
        self.count(1)


class Keithley2182A(VisaInstrument):
    """
    QCoDeS driver for Keithley 2182A nanovoltmeter.

    Provides parameters for:
      - Single voltage measurement
      - Range and autorange
      - Integration time (NPLC)
      - Filtering subsystem
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
        # self.write('SENS:VOLT:DFIL:TCON REP')
        # self.write('SENS:VOLT:DFIL ON')

        # Voltage reading
        self.add_parameter(
            'read',
            label='Voltage',
            unit='V',
            get_cmd='READ?',
            get_parser=float,
            docstring='Perform a single voltage measurement.'
        )

        self.add_parameter(
            'fetch',
            label='Voltage',
            unit='V',
            get_cmd='FETC?',
            get_parser=float,
            docstring='Fetch a single voltage measurement result.'
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
            set_cmd='SENS:VOLT:NPLC {:f}',
            vals=Numbers(min_value=0.01, max_value=50),
            get_parser=float,
            set_parser=float,
            docstring='Number of power line cycles for integration time.'
        )

        # Add filter subsystem
        self.filter: FilterModule
        self.add_submodule('filter', FilterModule(self, 'filter'))

        self.connect_message()

    def init(self):
        self.write('INIT')
