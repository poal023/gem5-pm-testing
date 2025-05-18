from m5.objects import Root

from .base_power_model import AbstractPowerModel


class McPATPowerModel(AbstractPowerModel):
    def __init__(self, simobj, xml_tree):
        super().__init__(simobj)
        self.name = "McPATPowerModel"
        self._xml_tree = xml_tree
        self._act_energy_tree_root = self._xml_tree.getroot()
        # self.init_act_energies(xml_tree)

    def convert_to_watts(self, value: float) -> float:
        """Note that McPAT AEs are already in terms of J,
        no need for conversion"""

        time = Root.getInstance().resolveStat("simSeconds").total
        return value / time
