from m5.objects import (
    L2XBar,
    Port,
    PowerModel,
    PowerModelPyFunc,
    SystemXBar,
)
from m5.stats import *

from .mcpat_power_model import McPATPowerModel


class L1DPowerOn(PowerModelPyFunc, McPATPowerModel):
    def __init__(self, l1dcache, writeback):
        super().__init__()
        # The SimObject that contains the stats we need.
        self._l1dcache = l1dcache
        self._writeback = writeback

        self._dcache_data_ae = 7.80998e-12
        self._dcache_tag_ae = 1.57793e-12

        self._dcache_read_ae = self._dcache_data_ae + self._dcache_tag_ae
        self._dcache_write_ae = 1.77257e-11

        self._dcache_mb_read_ae = 6.13188e-12
        self._dcache_mb_write_ae = 6.03686e-12
        self._dcache_mb_search_ae = 5.31524e-12

        self._dcache_ifb_read_ae = 3.19263e-12
        self._dcache_ifb_write_ae = 3.17392e-12
        self._dcache_ifb_search_ae = 2.93613e-12

        self._dcache_pfb_read_ae = 3.19263e-12
        self._dcache_pfb_write_ae = 3.17392e-12
        self._dcache_pfb_search_ae = 2.93613e-12

        self._dcache_wbb_read_ae = 3.19263e-12
        self._dcache_wbb_write_ae = 3.17392e-12
        self._dcache_wbb_search_ae = 2.93613e-12

        self.dyn = lambda: self.dynamic_power()
        self.st = lambda: self.static_power()

    def static_power(self):
        """Returns static power in Watts"""
        return 1.0

    def dynamic_power(self):
        """Returns dynamic power in Watts"""
        time = Root.getInstance().resolveStat("simSeconds").total
        total_energy = self.dcache_energy()
        print(f"L1Dcache energy: {total_energy}")
        total_energy += self.miss_buffer_energy()
        print(f"\t+ mb energy: {total_energy}")
        total_energy += self.inst_fill_buffer_energy()
        print(f"\t+ ifb energy: {total_energy}")
        total_energy += self.prefetch_buffer_energy()
        print(f"\t+ prefetch energy: {total_energy}")
        total_energy += self.writeback_buffer_energy()
        print(f"\t+ wbb energy: {total_energy}")
        print(f"L1D power: {self.convert_to_watts(total_energy)}")
        return self.convert_to_watts(total_energy)

    def dcache_energy(self):
        read_accesses = self._l1dcache.resolveStat("ReadReq.accesses").total
        write_accesses = self._l1dcache.resolveStat("WriteReq.accesses").total

        read_misses = self._l1dcache.resolveStat("ReadReq.misses").total
        write_misses = self._l1dcache.resolveStat("WriteReq.misses").total

        read_hits = read_accesses - read_misses
        write_hits = write_accesses - write_misses

        energy = (
            read_hits * self._dcache_read_ae
            + read_misses * self._dcache_read_ae
            + write_misses * self._dcache_tag_ae
            + write_accesses * self._dcache_write_ae
        )
        if self._writeback:
            # extra write for write misses since wb policy
            energy += write_misses * self._dcache_write_ae
        return energy

    def miss_buffer_energy(self):
        # by default, there is WB in caches (to my knowledge)
        if self._writeback:
            read_accesses = write_accesses = self._l1dcache.resolveStat(
                "WriteReq.misses"
            ).total
        else:
            read_accesses = write_accesses = self._l1dcache.resolveStat(
                "ReadReq.misses"
            ).total

        return (
            read_accesses * self._dcache_mb_search_ae  # CAM Energy
            + write_accesses * self._dcache_mb_write_ae  # Miss Energy
        )

    def inst_fill_buffer_energy(self):
        if self._writeback:
            read_accesses = write_accesses = self._l1dcache.resolveStat(
                "WriteReq.misses"
            ).total
        else:
            read_accesses = write_accesses = self._l1dcache.resolveStat(
                "ReadReq.misses"
            ).total
        return (
            read_accesses * self._dcache_ifb_search_ae
            + write_accesses * self._dcache_ifb_write_ae
        )

    def prefetch_buffer_energy(self):
        if self._writeback:
            read_accesses = write_accesses = self._l1dcache.resolveStat(
                "WriteReq.misses"
            ).total
        else:
            read_accesses = write_accesses = self._l1dcache.resolveStat(
                "ReadReq.misses"
            ).total
        return (
            read_accesses * self._dcache_pfb_search_ae
            + write_accesses * self._dcache_pfb_write_ae
        )

    def writeback_buffer_energy(self):
        if not self._writeback:
            return 0
        read_accesses = write_accesses = self._l1dcache.resolveStat(
            "WriteReq.misses"
        ).total
        return (
            read_accesses * self._dcache_wbb_search_ae
            + write_accesses * self._dcache_wbb_write_ae
        )


class L1DPowerOff(PowerModelPyFunc):
    def __init__(self):
        super().__init__()
        self.dyn = lambda: 0.0
        self.st = lambda: 0.0


class L1DPowerModel(PowerModel):
    def __init__(self, l1dcache, writeback):
        super().__init__()
        # Choose a power model for every power state
        self.pm = [
            L1DPowerOn(l1dcache, writeback),  # ON
            L1DPowerOff(),  # CLK_GATED
            L1DPowerOff(),  # SRAM_RETENTION
            L1DPowerOff(),  # OFF
        ]
