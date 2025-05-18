from m5.objects import (
    BaseO3CPU,
    PowerModel,
    PowerModelPyFunc,
)

from .o3_mcpat_exec_power_model import O3McPATExecutePower
from .o3_mcpat_fetch_power_model import O3McPATFetchPower
from .o3_mcpat_lsu_power_model import O3McPATLsuPower
from .o3_mcpat_mmu_power_model import O3McPATMmuPower
from .o3_mcpat_renaming_unit_power_model import O3McPATRenamingUnitPower


class O3McPATCpuPowerOn(PowerModelPyFunc):
    def __init__(self, cpu: BaseO3CPU, act_energies):
        """core must be a BaseO3CPU core"""
        super().__init__()
        self._fetch = O3McPATFetchPower(cpu, act_energies, 1.0, 0.9)
        self._rnu = O3McPATRenamingUnitPower(cpu, act_energies, 1.0)
        self._lsu = O3McPATLsuPower(cpu, act_energies, 1.0, 0.71)
        self._mmu = O3McPATMmuPower(cpu, act_energies, 1.0, 0.71)
        self._exec = O3McPATExecutePower(cpu, act_energies, 1.0, 0.76)

        self.dyn = self.dynamic_power
        self.st = self.static_power

    def static_power(self):
        return 1.0

    def dynamic_power(self):
        # total = 0.0
        total = (
            self._fetch.dynamic_power()
            + self._rnu.dynamic_power()
            + self._lsu.dynamic_power()
            + self._mmu.dynamic_power()
            + self._exec.dynamic_power()
        )
        self.print_mcpat(6, total)
        return total

    def print_mcpat(self, indent, total):
        print("*" * 80)
        print("Core:")
        print(" " * indent + f"Runtime Dynamic = {total}\n")
        self._fetch.print_mcpat(indent)
        self._rnu.print_mcpat(indent)
        self._lsu.print_mcpat(indent)
        self._mmu.print_mcpat(indent)
        self._exec.print_mcpat(indent)
        print("*" * 80)


class O3McPATCpuPowerOff(PowerModelPyFunc):
    def __init__(self):
        super().__init__()
        self.dyn = lambda: 0.0
        self.st = lambda: 0.0


class O3McPATCpuPowerModel(PowerModel):
    def __init__(self, core, act_energies):
        super().__init__()
        # Choose a power model for every power state
        self.pm = [
            O3McPATCpuPowerOn(core, act_energies),  # ON
            O3McPATCpuPowerOff(),  # CLK_GATED
            O3McPATCpuPowerOff(),  # SRAM_RETENTION
            O3McPATCpuPowerOff(),  # OFF
        ]
