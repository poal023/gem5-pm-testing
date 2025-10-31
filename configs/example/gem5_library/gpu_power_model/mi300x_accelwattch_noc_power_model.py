from math import ceil

from m5.objects import (
    Root,
    Shader,
)

# from gem5.prebuilt.viper.viper_garnet_network import GarnetDoubleCrossbar
from gem5.prebuilt.viper.viper_network import SimpleDoubleCrossbar

from .accelwattch_base_power_model import (
    AccelwattchBasePowerModel,
)

""" Note that this is also referred to as SQC """


class MI300XAccelwattchNoCPower(AccelwattchBasePowerModel):
    def __init__(self, gpu: Shader, act_energies, scaling_factors, interval):
        super().__init__(gpu, act_energies, scaling_factors, interval)
        self.name = "MI300XAccelwattchNoCPower"
        self._ruby_gpu = None
        self._net_type = None

    def dynamic_power(self) -> float:
        self._network = self._simobj._parent.gpu_caches.ruby_gpu.network
        self._net_type = type(self._network)
        energy = self.noc_access_energy()
        return self.convert_to_watts(energy)

    def static_power(self) -> float:
        return 0.0

    def noc_access_energy(self) -> float:
        assert isinstance(self._network, self._net_type)
        if self._net_type is None:
            """
            flits_injected = self.get_stat("m_flits_injected",
                                           self._network)
            flits_received = self.get_stat("m_flits_received",
                                           self._network)
            """
            # Below is just a temporary fix, can't get garnet stats
            flits_injected = 2_000_000
            flits_received = 2_500_000
            noc_accesses = self._scaling_factors["NOC_A"] * (
                flits_injected + flits_received
            )
            energy = noc_accesses * (
                self._act_energies["NoCRouter"]["Read"]
                + self._act_energies["NoCRouter"]["Write"]
                + self._act_energies["NoCCrossbar"]
                + self._act_energies["NoCArbiter"]
            )
        elif self._net_type is SimpleDoubleCrossbar:
            msgs = self.get_stat("msg_count", self._network)
            print(msgs)
            energy = 0

        return energy
