from m5.objects import TournamentBP

# from .base_power_model import AbstractPowerModel
from .mcpat_power_model import McPATPowerModel


class TournamentBPPower(McPATPowerModel):
    def __init__(self, branch_pred: TournamentBP, xml_tree):
        super().__init__(branch_pred, xml_tree)
        self.name = "BP"
        self._btb_read_ae = self.get_act_energy("BTB", "Read")
        self._btb_write_ae = self.get_act_energy("BTB", "Write")

        self._glob_pred_read_ae = self.get_act_energy("GlobalPred", "Read")
        self._glob_pred_write_ae = self.get_act_energy("GlobalPred", "Write")

        self._l1_local_pred_read_ae = self.get_act_energy("L1Pred", "Read")
        self._l1_local_pred_write_ae = self.get_act_energy("L1Pred", "Write")

        self._l2_local_pred_read_ae = self.get_act_energy("L2Pred", "Read")
        self._l2_local_pred_write_ae = self.get_act_energy("L2Pred", "Write")

        self._chooser_pred_read_ae = self.get_act_energy("PredChooser", "Read")
        self._chooser_pred_write_ae = self.get_act_energy(
            "PredChooser", "Write"
        )

        self._ras_pred_read_ae = self.get_act_energy("RAS", "Read")
        self._ras_pred_write_ae = self.get_act_energy("RAS", "Write")

    def static_power(self) -> float:
        """Returns static power in Watts"""
        return 1.0

    def dynamic_power(self) -> float:
        energy = (
            self.total_btb_energy()
            + self.total_glob_pred_energy()
            + self.total_l1_local_pred_energy()
            + self.total_l2_local_pred_energy()
            + self.total_chooser_pred_energy()
            + self.total_ras_pred_energy()
        )
        """
        print(f"Total Energy: {self.total_btb_energy()} (BTB)\
                + {self.total_glob_pred_energy()} (global)\
                + {self.total_l1_local_pred_energy()} (l1 local)\
                + {self.total_l2_local_pred_energy()} (l2 local)\
                + {self.total_chooser_pred_energy()} (chooser)\
                + {self.total_ras_pred_energy()} (RAS)\
                = {energy} ({self.convert_to_watts(energy)} W)")
        """

        return self.convert_to_watts(energy)

    def total_btb_energy(self) -> float:
        btb_reads = self.get_stat("branchPred.BTBLookups")
        btb_writes = self.get_stat("branchPred.BTBUpdates")
        return self._btb_read_ae * btb_reads + self._btb_write_ae * btb_writes

    def total_glob_pred_energy(self) -> float:
        predicts = self.get_stat("branchPred.condPredicted")
        mispredicts = self.get_stat("branchPred.condIncorrect")
        return (
            self._glob_pred_read_ae * predicts
            + self._glob_pred_write_ae * mispredicts
        )

    def total_l1_local_pred_energy(self) -> float:
        predicts = self.get_stat("branchPred.condPredicted")
        mispredicts = self.get_stat("branchPred.condIncorrect")
        return (
            self._l1_local_pred_read_ae * predicts
            + self._l1_local_pred_write_ae * mispredicts
        )

    def total_l2_local_pred_energy(self) -> float:
        predicts = self.get_stat("branchPred.condPredicted")
        mispredicts = self.get_stat("branchPred.condIncorrect")
        return (
            self._l2_local_pred_read_ae * predicts
            + self._l2_local_pred_write_ae * mispredicts
        )

    def total_chooser_pred_energy(self) -> float:
        predicts = self.get_stat("branchPred.condPredicted")
        mispredicts = self.get_stat("branchPred.condIncorrect")
        return (
            self._chooser_pred_read_ae * predicts
            + self._chooser_pred_write_ae * mispredicts
        )

    def total_ras_pred_energy(self) -> float:
        ras_rws = self.get_stat("commitStats0.numCallsReturns")
        return (
            self._ras_pred_read_ae * ras_rws
            + self._ras_pred_write_ae * ras_rws
        )
