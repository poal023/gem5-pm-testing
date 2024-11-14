from m5.objects import (
    L2XBar,
    Port,
    PowerModel,
    PowerModelPyFunc,
    SystemXBar,
)
from m5.stats import *


class L1IPowerOn(PowerModelPyFunc):
    def __init__(self, l1icache):
        super().__init__()
        # The SimObject that contains the stats we need.
        self._l1icache = l1icache
        self.dyn = lambda: self.dynamic_power()
        self.st = lambda: self.static_power()

    def static_power(self):
        """Returns static power in Watts"""
        return 1.0

    def dynamic_power(self):
        """Returns dynamic power in Watts"""
        time = Root.getInstance().resolveStat("simSeconds").total
        total_energy_nj = (
            self.tag_energy() + self.instruction_energy() + self.mshr_energy()
        )
        # print(total_energy_nj)
        total_energy_j = total_energy_nj * 1e-9
        return total_energy_j / time

    def tag_energy(self):
        """Returns tag energy in nJ"""

        misses = self._l1icache.resolveStat("overallMisses").total
        hits = self._l1icache.resolveStat("overallHits").total

        tag_reads = hits + misses
        tag_writes = misses

        return tag_reads * 0.7 + tag_writes * 1.0

    def instruction_energy(self):
        """Returns data energy in nJ"""
        misses = self._l1icache.resolveStat("overallMisses").total
        hits = self._l1icache.resolveStat("overallHits").total
        writebacks = self._l1icache.resolveStat("writebacks").total

        inst_reads = hits + misses + writebacks
        inst_writes = misses

        return inst_reads * 1.5 + inst_writes * 3.5

    def mshr_energy(self):
        misses = self._l1icache.resolveStat("overallMisses").total
        probes = 1.0

        mshr_reads = misses + probes
        mshr_writes = misses

        return mshr_reads * 0.1 + mshr_writes * 0.3


class L1IPowerOff(PowerModelPyFunc):
    def __init__(self):
        super().__init__()
        self.dyn = lambda: 0.0
        self.st = lambda: 0.0


class L1IPowerModel(PowerModel):
    def __init__(self, l1icache, **kwargs):
        super().__init__(**kwargs)
        # Choose a power model for every power state
        self.pm = [
            L1IPowerOn(l1icache),  # ON
            L1IPowerOff(),  # CLK_GATED
            L1IPowerOff(),  # SRAM_RETENTION
            L1IPowerOff(),  # OFF
        ]
