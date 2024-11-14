from m5.objects import (
    L2XBar,
    Port,
    PowerModel,
    PowerModelFunc,
    SystemXBar,
)
from m5.stats import *


class L1DPowerOn(PowerModelFunc):
    def __init__(self, l1dcache):
        super().__init__()
        # The SimObject that contains the stats we need.
        self._l1dcache = l1dcache
        self.dyn = lambda: self.dynamic_power()
        self.st = lambda: self.static_power()

    def static_power(self):
        """Returns static power in Watts"""
        return 1.0

    def dynamic_power(self):
        """Returns dynamic power in Watts"""
        time = Root.getInstance().resolveStat("simSeconds").total
        total_energy_nj = (
            self.tag_energy() + self.data_energy() + self.mshr_energy()
        )
        # print(total_energy_nj)
        total_energy_j = total_energy_nj * 1e-9
        return total_energy_j / time

    def tag_energy(self):
        """Returns tag energy in nJ"""

        misses = self._l1dcache.resolveStat("overallMisses").total
        hits = self._l1dcache.resolveStat("overallHits").total

        tag_reads = hits + misses
        tag_writes = misses

        return tag_reads * 0.7 + tag_writes * 1.0

    def data_energy(self):
        """Returns data energy in nJ"""
        misses = self._l1dcache.resolveStat("overallMisses").total
        hits = self._l1dcache.resolveStat("overallHits").total
        writebacks = self._l1dcache.resolveStat("writebacks").total

        data_reads = hits + misses + writebacks
        data_writes = misses

        return data_reads * 2.0 + data_writes * 4.0

    def mshr_energy(self):
        misses = self._l1dcache.resolveStat("overallMisses").total
        probes = 1.0

        mshr_reads = misses + probes
        mshr_writes = misses

        return mshr_reads * 0.1 + mshr_writes * 0.3


class L1DPowerOff(PowerModelFunc):
    def __init__(self):
        super().__init__()
        self.dyn = lambda: 0.0
        self.st = lambda: 0.0


class L1DPowerModel(PowerModel):
    def __init__(self, l1dcache, **kwargs):
        super().__init__(**kwargs)
        # Choose a power model for every power state
        self.pm = [
            L1DPowerOn(l1dcache),  # ON
            L1DPowerOff(),  # CLK_GATED
            L1DPowerOff(),  # SRAM_RETENTION
            L1DPowerOff(),  # OFF
        ]
