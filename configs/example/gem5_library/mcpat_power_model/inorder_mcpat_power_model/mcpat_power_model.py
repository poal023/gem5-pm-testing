import xml.etree.ElementTree as ET

from m5.objects import Root

from .base_power_model import AbstractPowerModel


class McPATPowerModel(AbstractPowerModel):
    def __init__(self, simobj, act_energies):
        super().__init__(simobj)
        self.name = "McPATPowerModel"
        self._act_energies = act_energies

    def convert_to_watts(self, value: float) -> float:
        """Note that McPAT AEs are already in terms of J,
        no need for conversion"""

        time = Root.getInstance().resolveStat("simSeconds").total
        return value / time
