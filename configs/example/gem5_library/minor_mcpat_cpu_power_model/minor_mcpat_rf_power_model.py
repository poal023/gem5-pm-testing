from m5.objects import BaseMinorCPU

# Never use `import *`
from .base_power_model import AbstractPowerModel
from .mcpat_power_model import McPATPowerModel

# Only import things you need


class MinorMcPATRfPower(McPATPowerModel):
    # avoid the use of default values
    def __init__(self, minorcpu: BaseMinorCPU, xml_tree):
        super().__init__(minorcpu, xml_tree)
        # _rf isn't really needed since you have `_simobj`
        self.name = "RF"
        self._int_rf_read_ae = self.get_act_energy("IntRegFile", "Read")
        self._fp_rf_read_ae = self.get_act_energy("FPRegFile", "Read")

        self._int_rf_write_ae = self.get_act_energy("IntRegFile", "Write")
        self._fp_rf_write_ae = self.get_act_energy("FPRegFile", "Write")

    def static_power(self) -> float:
        """Returns static power in Watts"""
        return 1.0

    def dynamic_power(self) -> float:
        energy = self.int_energy() + self.fp_energy() + self.misc_energy()
        print(
            f"{self.int_energy()} + {self.fp_energy()} + {self.misc_energy()}"
        )
        return self.convert_to_watts(energy)

    def int_energy(self) -> float:
        # reads = self.get_stat("numIntRegReads")
        # writes = self.get_stat("numIntRegWrites")
        reads = self.get_stat("executeStats0.numIntRegReads")
        writes = self.get_stat("executeStats0.numIntRegWrites")
        return reads * self._int_rf_read_ae + writes * self._int_rf_write_ae

    def fp_energy(self) -> float:
        # reads = self.get_stat("numFpRegReads")
        # writes = self.get_stat("numFpRegWrites")
        reads = self.get_stat("executeStats0.numFpRegReads")
        writes = self.get_stat("executeStats0.numFpRegWrites")

        return reads * self._fp_rf_read_ae + writes * self._fp_rf_write_ae

    def misc_energy(self) -> float:
        # reads = self.get_stat("numMiscRegReads")
        # writes = self.get_stat("numMiscRegWrites")
        reads = self.get_stat("executeStats0.numMiscRegReads")
        writes = self.get_stat("executeStats0.numMiscRegWrites")

        return reads * 0.0 + writes * 0.0
