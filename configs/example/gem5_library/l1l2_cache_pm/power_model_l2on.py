from m5.objects import (
    L2XBar,
    Port,
    PowerModel,
    PowerModelFunc,
    SystemXBar,
)
from m5.stats import *


class L2PowerOn(PowerModelFunc):
    def __init__(self, l2cache):
        super().__init__()
        # The SimObject that contains the stats we need.
        self._l2cache = l2cache
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

        misses = self._l2cache.resolveStat("overallMisses").total
        hits = self._l2cache.resolveStat("overallHits").total

        tag_reads = hits + misses
        tag_writes = misses

        return tag_reads * 1.0 + tag_writes * 1.5

    def data_energy(self):
        """Returns data energy in nJ"""
        misses = self._l2cache.resolveStat("overallMisses").total
        hits = self._l2cache.resolveStat("overallHits").total
        writebacks = self._l2cache.resolveStat("writebacks").total

        data_reads = hits + misses + writebacks
        data_writes = misses

        return data_reads * 4.0 + data_writes * 6.5

    def mshr_energy(self):
        """Returns MSHR energy in nJ"""
        misses = self._l2cache.resolveStat("overallMisses").total
        # Fix below!
        # probes = = self.l2cache.resolveStat('probes')
        probes = 1.0

        mshr_reads = misses + probes
        mshr_writes = misses

        return mshr_reads * 0.1 + mshr_writes * 0.5
