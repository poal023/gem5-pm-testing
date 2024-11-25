from m5.objects import BaseMinorCPU

from .base_power_model import AbstractPowerModel
from .mcpat_power_model import McPATPowerModel


class MinorMcPATAluPower(McPATPowerModel):
    def __init__(self, minorcpu: BaseMinorCPU, xmltree):
        super().__init__(minorcpu, xmltree)
        self.name = "McPATMinorAluPower"
        self._cpu = minorcpu
        self._int_access_energy = 6.22113e-12
        self._fp_access_energy = 1.86634e-11
        self._mul_access_energy = 1.24423e-11
        """
        Note that for vec access energy I'm using
        McPAT's access energy for Mul/Div ops.
        I suspect this is actually larger, but this
        is a placeholder. Surprisingly, McPAT doesn't
        actually account for SIMD insts individually.
        Assuming they lump SIMD w/ the rest of M/D ops?
        """
        self._vec_access_energy = 1.24423e-11

    def static_power(self) -> float:
        # no need for documentation if you're overriding the base class
        return 1.0

    def dynamic_power(self) -> float:
        committed_insts = self._cpu.resolveStat(
            "commitStats0.committedInstType"
        )
        print(
            f"{self.int_energy(committed_insts)} +\
              {self.fp_energy(committed_insts)} +\
              {self.mul_energy(committed_insts)}"
        )
        energy = (
            self.int_energy(committed_insts)
            + self.fp_energy(committed_insts)
            + self.mul_energy(committed_insts)
        )
        return self.convert_to_watts(energy)

    def int_energy(self, committed_insts) -> float:
        int_accesses = self.get_stat("executeStats0.numIntAluAccesses")
        """ Note: below is used to sort btwn mult/non-mult insts """
        # committed_insts =\
        #        self._cpu.resolveStat("commitStats0.committedInstType")
        return (int_accesses) * self._int_access_energy

    def fp_energy(self, committed_insts) -> float:
        fp_accesses = self.get_stat("executeStats0.numFpAluAccesses")
        fp_mults = committed_insts.value[
            committed_insts.subnames.index("FloatMult")
        ]
        fp_maccs = committed_insts.value[
            committed_insts.subnames.index("FloatMultAcc")
        ]
        fp_divs = committed_insts.value[
            committed_insts.subnames.index("FloatDiv")
        ]
        return fp_accesses * self._fp_access_energy

    def mul_energy(self, committed_insts) -> float:
        fp_mults = committed_insts.value[
            committed_insts.subnames.index("FloatMult")
        ]
        fp_maccs = committed_insts.value[
            committed_insts.subnames.index("FloatMultAcc")
        ]
        fp_divs = committed_insts.value[
            committed_insts.subnames.index("FloatDiv")
        ]
        print(fp_mults + fp_maccs + fp_divs)
        return (fp_mults + fp_maccs + fp_divs) * self._mul_access_energy


"""
    def vec_energy(self, committed_insts) -> float:
        vec_accesses = self.get_stat("executeStats0.numVecAluAccesses")
        return vec_accesses * self._vec_access_energy
"""
