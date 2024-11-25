from m5.objects import (
    BaseMinorCPU,
    Root,
)

# Never use `import *`
from .base_power_model import AbstractPowerModel
from .mcpat_power_model import McPATPowerModel
from .minor_mcpat_alu_power_model import MinorMcPATAluPower

# Only import things you need


class MinorMcPATExecutePower(McPATPowerModel):
    # avoid the use of default values
    def __init__(self, minorcpu: BaseMinorCPU, xml_tree):
        super().__init__(minorcpu, xml_tree)
        # _rf isn't really needed since you have `_simobj`
        self.name = "Execute"
        self._alu = MinorMcPATAluPower(minorcpu, xml_tree)

    def static_power(self) -> float:
        """Returns static power in Watts"""
        return 1.0

    def dynamic_power(self) -> float:
        energy = 0.0
        return self._alu.dynamic_power()

    """ Below, need to use R1 and R2 registers in the pipeline for ALUs"""

    def total_mux_energy(self) -> float:
        r1_accesses = 0
        r2_accesses = 0
        return (
            r1_accesses * self.mux_act_energy()
            + r2_accesses * self.mux_act_energy()
        )

    def fwd_unit_energy(self) -> float:
        return 0 * self.fwd_unit_act_energy()

    def fwd_unit_act_energy(self) -> float:
        return 4.0

    def mux_act_energy(self) -> float:
        return 2.0
