from m5.objects import (
    BaseMinorCPU,
    Root,
)

# Never use `import *`
from .base_power_model import AbstractPowerModel
from .mcpat_power_model import McPATPowerModel
from .minor_mcpat_rf_power_model import MinorMcPATRfPower

# Only import things you need


class MinorMcPATDecodePower(McPATPowerModel):
    # avoid the use of default values
    def __init__(self, minorcpu: BaseMinorCPU, xml_tree):
        super().__init__(minorcpu, xml_tree)
        # _rf isn't really needed since you have `_simobj`
        self.name = "Decode"
        self._rf = MinorMcPATRfPower(minorcpu, xml_tree)
        self._ib_read_ae = self.get_act_energy("InstBuffer", "Read")
        self._ib_write_ae = self.get_act_energy("InstBuffer", "Write")

    def static_power(self) -> float:
        """Returns static power in Watts"""
        return 1.0

    def dynamic_power(self) -> float:
        energy = self.inst_buffer_energy()
        print(f"Instruction Buffer Energy: {energy / 0.000033}")
        return self.convert_to_watts(energy) + self._rf.dynamic_power()

    def inst_buffer_energy(self) -> float:
        decoded_insts = self.get_stat("fetch2.totalInstructions")
        return (
            decoded_insts * self._ib_read_ae
            + decoded_insts * self._ib_write_ae
        )

    """

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
"""
