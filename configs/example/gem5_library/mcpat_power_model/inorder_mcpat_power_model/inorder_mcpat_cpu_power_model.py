from m5.objects import (
    BaseCPU,
    PowerModel,
    PowerModelPyFunc,
)

from .inorder_mcpat_exec_power_model import InorderMcPATExecutePower
from .inorder_mcpat_fetch_power_model import InorderMcPATFetchPower
from .inorder_mcpat_lsu_power_model import InorderMcPATLsuPower
from .inorder_mcpat_mmu_power_model import InorderMcPATMmuPower


class InorderMcPATCpuPowerOn(PowerModelPyFunc):
    def __init__(self, cpu: BaseCPU, act_energies):
        """core must be a BaseCPU core"""
        super().__init__()
        self._fetch = InorderMcPATFetchPower(cpu, act_energies, 1.0, 0.9)
        self._lsu = InorderMcPATLsuPower(cpu, act_energies, 1.0, 0.71)
        self._mmu = InorderMcPATMmuPower(cpu, act_energies, 1.0, 0.71)
        self._exec = InorderMcPATExecutePower(cpu, act_energies, 1.0, 0.76)

        self.dyn = self.dynamic_power
        self.st = self.static_power

    def static_power(self):
        return 1.0

    def dynamic_power(self):
        # total = 0.0
        total = (
            self._fetch.dynamic_power()
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
        self._lsu.print_mcpat(indent)
        self._mmu.print_mcpat(indent)
        self._exec.print_mcpat(indent)
        print("*" * 80)


class InorderMcPATCpuPowerOff(PowerModelPyFunc):
    def __init__(self):
        super().__init__()
        self.dyn = lambda: 0.0
        self.st = lambda: 0.0


class InorderMcPATCpuPowerModel(PowerModel):
    def __init__(self, core, act_energies):
        super().__init__()
        # Choose a power model for every power state
        self.pm = [
            InorderMcPATCpuPowerOn(core, act_energies),  # ON
            InorderMcPATCpuPowerOff(),  # CLK_GATED
            InorderMcPATCpuPowerOff(),  # SRAM_RETENTION
            InorderMcPATCpuPowerOff(),  # OFF
        ]
