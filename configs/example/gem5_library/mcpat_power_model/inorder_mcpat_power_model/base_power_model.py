from m5.objects import Root
from m5.util import panic


class AbstractPowerModel:
    def __init__(self, simobj):
        self._simobj = simobj
        self.name = "AbstractPowerModel"

    def get_stat(self, stat):
        try:
            stat = self._simobj.resolveStat(stat)
            return stat
        except KeyError:
            panic(f"{stat} not found in stats!")
            return 0.0

    def dynamic_power(self) -> float:
        """Returns dynamic power in Watts"""
        # These should not be implemented in this (abstract) base class
        raise NotImplementedError

    def static_power(self) -> float:
        """Returns static power in Watts"""
        # These should not be implemented in this (abstract) base class
        raise NotImplementedError

    def convert_to_watts(self, value: float) -> float:
        """Convert energy in nanojoules to Watts"""
        time = Root.getInstance().resolveStat("simSeconds").total
        value_in_j = value * 1e-9
        return value_in_j / time
