from m5.objects import (
    BaseMinorCPU,
    Root,
)

# Never use `import *`
from .base_power_model import AbstractPowerModel
from .minor_mcpat_rf_power_model import MinorMcPATRfPower

# Only import things you need


class MinorMcPATDecodePower(AbstractPowerModel):
    # avoid the use of default values
    def __init__(self, minorcpu: BaseMinorCPU):
        super().__init__(minorcpu)
        # _rf isn't really needed since you have `_simobj`
        self.name = "Decode"
        self._rf = MinorMcPATRfPower(minorcpu, issue_width=4)

    def static_power(self) -> float:
        """Returns static power in Watts"""
        return 1.0

    def dynamic_power(self) -> float:
        energy = (
            self.hazard_det_energy()
            + self.ctrl_logic_energy()
            + self.imm_gen_energy()
        )
        print(
            f"{self.hazard_det_energy()} + {self.ctrl_logic_energy()} + {self.imm_gen_energy()}"
        )
        return self.convert_to_watts(energy) + self._rf.dynamic_power()

    def hazard_det_energy(self) -> float:
        return 0 * self.hazard_det_act_energy()

    def ctrl_logic_energy(self) -> float:
        return 0 * self.ctrl_logic_act_energy()

    def imm_gen_energy(self) -> float:
        return 0 * self.imm_gen_act_energy()

    def ctrl_logic_act_energy(self) -> float:
        return 1.0

    def hazard_det_act_energy(self) -> float:
        return 1.5

    def imm_gen_act_energy(self) -> float:
        return 1.0

    def mux_act_energy(self) -> float:
        return 2.0
