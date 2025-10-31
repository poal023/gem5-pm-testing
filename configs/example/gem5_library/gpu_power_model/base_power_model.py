import traceback

from m5.objects import Root

from _m5.stats import (
    Vector2dInfo,
    VectorInfo,
)


class AbstractPowerModel:
    def __init__(self, simobj, interval):
        self._simobj = simobj
        self._interval = interval
        self.name = "AbstractPowerModel"
        self._stats = {}

    def get_stat(self, stat, simobj=None):
        if simobj == None:
            simobj = self._simobj
        try:
            value = simobj.resolveStat(stat).total
            if self._interval > 0:
                if stat not in self._stats:
                    if stat == "shaderActiveTicks":
                        print(f"sAT add in dict as: {self._stats[stat]}")
                    self._stats[stat] = value
                else:
                    self._stats[stat] = value - self._stats[stat]
                    if stat == "shaderActiveTicks":
                        print(f"stat in stat dict is: {self._stats[stat]}")
                        print(f"difference is: {value}")
                return self._stats[stat]
            return value
        except KeyError as e:
            print(f"{stat} not found in stats!")
            traceback.print_exc()
            return 0.0

    def dynamic_power(self) -> float:
        raise NotImplementedError

    def static_power(self) -> float:
        raise NotImplementedError

    def convert_to_watts(self, value) -> float:
        if self._interval > 0:
            return value / self._interval
        time = Root.getInstance().resolveStat("simSeconds").total
        return value / time
