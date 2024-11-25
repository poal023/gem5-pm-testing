from m5.objects import (
    BaseMinorCPU,
    BaseO3CPU,
    PowerModel,
    PowerModelPyFunc,
)

from .minor_mcpat_decode_power_model import MinorMcPATDecodePower
from .minor_mcpat_exec_power_model import MinorMcPATExecutePower
from .minor_mcpat_fetch_power_model import MinorMcPATFetchPower
from .tournament_bp_power_model import TournamentBPPower

"""
Is there a way include "Base_PowerModel as a class to derive from?
Main reason is to limit the amount of fns we override/redefine
"""


class MinorMcPATCpuPowerOn(PowerModelPyFunc):
    """Power model for an MinorCPU"""

    def __init__(self, core, xml_tree):
        """core must be an MinorCPU core"""
        super().__init__()
        self._fetch = MinorMcPATFetchPower(core, xml_tree)
        self._decode = MinorMcPATDecodePower(core, xml_tree)
        self._exec = MinorMcPATExecutePower(core, xml_tree)
        self._fetch_act_factor = 0.9
        # according to McPAT, this is rt ipc / peak ipc,
        # if this value is <= 1(?)
        self._pipeline_act_factor = 1.0
        # self._mem = MinorMemoryPower(core)

        self.dyn = self.dynamic_power
        self.st = self.static_power

    def static_power(self):
        """Returns static power in Watts"""
        return 1.0

    def dynamic_power(self):
        """Returns dynamic power in Watts"""
        total = 0.0
        for part in [self._exec, self._decode, self._fetch]:
            # Note: There may be side effects of calling this function
            # (e.g., remembering the last value of the stat). So, I would
            # only call it once
            power = part.dynamic_power()
            print(f"{part.name} dynamic power is: {power}")
            total += power

        return total


class MinorMcPATCpuPowerOff(PowerModelPyFunc):
    def __init__(self):
        super().__init__()
        self.dyn = lambda: 0.0
        self.st = lambda: 0.0


class MinorMcPATCpuPowerModel(PowerModel):
    def __init__(self, core, xml_tree):
        super().__init__()
        # Choose a power model for every power state
        self.pm = [
            MinorMcPATCpuPowerOn(core, xml_tree),  # ON
            MinorMcPATCpuPowerOff(),  # CLK_GATED
            MinorMcPATCpuPowerOff(),  # SRAM_RETENTION
            MinorMcPATCpuPowerOff(),  # OFF
        ]
