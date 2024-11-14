from m5.objects import (
    BaseMinorCPU,
    Root,
)

# Never use `import *`
from .base_power_model import AbstractPowerModel
from .tournament_bp_power_model import TournamentBPPower

# Only import things you need


class MinorMcPATFetchPower(AbstractPowerModel):
    # avoid the use of default values
    def __init__(self, minorcpu: BaseMinorCPU, xml_tree):
        super().__init__(minorcpu)
        # _rf isn't really needed since you have `_simobj`
        self.name = "Fetch"
        self._bp = TournamentBPPower(minorcpu, xml_tree)

    def static_power(self) -> float:
        """Returns static power in Watts"""
        return 1.0

    def dynamic_power(self) -> float:
        """Get the energy for branch/non-branches and Fetch1/Fetch2
        pipelines"""
        energy = self.inst_energy() + self.branch_energy()
        print(f"{self.inst_energy()} + {self.branch_energy()}")
        return self.convert_to_watts(energy) + self._bp.dynamic_power()

    def branch_energy(self) -> float:
        branches = self.get_stat("numBranches")
        return (
            branches * self.mux_act_energy()
            + branches * self.incr_act_energy()
        )

    def inst_energy(self) -> float:
        branches = self.get_stat("numBranches")
        non_branch_insts = (
            Root.getInstance().resolveStat("simInsts").total - branches
        )
        return non_branch_insts * self.incr_act_energy()

    def incr_act_energy(self) -> float:
        return 3.5

    def mux_act_energy(self) -> float:
        return 2.0
