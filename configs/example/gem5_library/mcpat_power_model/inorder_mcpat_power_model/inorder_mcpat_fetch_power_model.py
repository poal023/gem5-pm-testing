from m5.objects import (
    BaseCPU,
    BranchPredictor,
    Root,
)

# Never use `import *`
from .base_power_model import AbstractPowerModel
from .inorder_mcpat_decode_power_model import InorderMcPATDecodePower
from .mcpat_btb_power_model import McPATBtbPower
from .mcpat_power_model import McPATPowerModel
from .mcpat_tournament_bp_power_model import McPATTournamentBPPower


class InorderMcPATFetchPower(McPATPowerModel):
    # avoid the use of default values
    def __init__(
        self, cpu: BaseCPU, act_energies, pipeline_act_factor, ifu_act_factor
    ):
        super().__init__(cpu, act_energies)
        self.name = "InorderMcPATFetchPower"

        """ Below is to ensure that our PM doesn't panic if user hasn't given a BP """
        self._has_predictor = False
        for desc in self._simobj.descendants():
            if isinstance(desc, BranchPredictor):
                self._has_predictor = True

        self._bp = McPATTournamentBPPower(
            cpu, act_energies, self._has_predictor
        )
        self._btb = McPATBtbPower(cpu, act_energies, self._has_predictor)
        self._decode = InorderMcPATDecodePower(cpu, act_energies)

        """ The Activity Factor of the Inst. Fetch Unit (default: 0.9): """
        self._ifu_act_factor = ifu_act_factor

        """ The Activity Factor of the Pipeline itself (default: 1.0): """
        self._pipeline_act_factor = pipeline_act_factor

        """ Number of Pipeline Stages for any Inorder CPU in McPAT: """
        self._num_units = 4.0

        """ The number of pipelines our CPU has (assume 1): """
        self._num_pipelines = 1.0

    def print_mcpat(self, indent):

        total_power = (
            self._decode.dynamic_power()
            + self._btb.dynamic_power()
            + self._bp.dynamic_power()
            + self.convert_to_watts(self.pipeline_energy())
        )
        print(" " * indent + f"Instruction Fetch Unit")
        print(" " * (indent + 2) + f"Runtime Dynamic = {total_power} W\n")
        self._btb.print_mcpat(indent + 4)
        self._bp.print_mcpat(indent + 4)
        self._decode.print_mcpat(indent + 4)

    def static_power(self) -> float:
        """Returns static power in Watts"""
        return 1.0

    def dynamic_power(self) -> float:
        total_power = (
            self._decode.dynamic_power()
            + self._btb.dynamic_power()
            + self._bp.dynamic_power()
            + self.convert_to_watts(self.pipeline_energy())
        )
        return total_power

    def pipeline_energy(self) -> float:
        cycles = self.get_stat(
            "numCycles"
        ).total  # total number of cycles, idle or not
        rtp_pipeline_coe = (
            cycles * self._ifu_act_factor * self._pipeline_act_factor
        )
        total_pipeline_cost = (
            rtp_pipeline_coe * self._num_pipelines / self._num_units
        )
        return total_pipeline_cost * self._act_energies["Pipeline"]
