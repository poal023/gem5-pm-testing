from m5.objects import TournamentBP

from .base_power_model import AbstractPowerModel


class TournamentBPPower(AbstractPowerModel):
    def __init__(self, branch_pred: TournamentBP):
        super().__init__(branch_pred)
        self.name = "BP"
        self._btb_read_ae = 5.62534e-12
        self._btb_write_ae = 8.68454e-12

        self._glob_pred_read_ae = 2.81993e-12
        self._glob_pred_write_ae = 1.50057e-12

        self._l1_local_pred_read_ae = 1.59669e-13
        self._l1_local_pred_write_ae = 2.99057e-13

        self._l2_local_pred_read_ae = 1.22289e-13
        self._l2_local_pred_write_ae = 1.96004e-13

        self._chooser_pred_read_ae = 2.81993e-12
        self._chooser_pred_write_ae = 1.50057e-12

        self._ras_pred_read_ae = 3.36208e-13
        self._ras_pred_write_ae = 4.51353e-13

    def static_power(self) -> float:
        """Returns static power in Watts"""
        return 1.0

    def dynamic_power(self) -> float:
        """
        print(f"Total Energy: {self.total_btb_energy()} (BTB)\
                + {self.total_glob_pred_energy()} (global)\
                + {self.total_l1_local_pred_energy()} (l1 local)\
                + {self.total_l2_local_pred_energy()} (l2 local)\
                + {self.total_chooser_pred_energy()} (chooser)\
                + {self.total_ras_pred_energy()} (RAS) ")
        """
        energy = (
            self.total_btb_energy()
            + self.total_glob_pred_energy()
            + self.total_l1_local_pred_energy()
            + self.total_l2_local_pred_energy()
            + self.total_chooser_pred_energy()
            + self.total_ras_pred_energy()
        )
        return self.convert_to_watts(energy)

    def total_btb_energy(self) -> float:
        btb_reads = self.get_stat("BTBLookups")
        btb_writes = self.get_stat("BTBUpdates")
        return self._btb_read_ae * btb_reads + self._btb_write_ae * btb_writes

    def total_glob_pred_energy(self) -> float:
        predicts = self.get_stat("condPredicted")
        mispredicts = self.get_stat("condIncorrect")
        return (
            self._glob_pred_read_ae * predicts
            + self._glob_pred_write_ae * mispredicts
        )

    def total_l1_local_pred_energy(self) -> float:
        predicts = self.get_stat("condPredicted")
        mispredicts = self.get_stat("condIncorrect")
        return (
            self._l1_local_pred_read_ae * predicts
            + self._l1_local_pred_write_ae * mispredicts
        )

    def total_l2_local_pred_energy(self) -> float:
        predicts = self.get_stat("condPredicted")
        mispredicts = self.get_stat("condIncorrect")
        return (
            self._l2_local_pred_read_ae * predicts
            + self._l2_local_pred_write_ae * mispredicts
        )

    def total_chooser_pred_energy(self) -> float:
        predicts = self.get_stat("condPredicted")
        mispredicts = self.get_stat("condIncorrect")
        return (
            self._chooser_pred_read_ae * predicts
            + self._chooser_pred_write_ae * mispredicts
        )

    def total_ras_pred_energy(self) -> float:
        ras_rws = self.get_stat("numCallsReturns")
        return (
            self._ras_pred_read_ae * ras_rws
            + self._ras_pred_write_ae * ras_rws
        )
