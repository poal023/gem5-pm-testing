import xml.etree.ElementTree as ET

from m5.objects import Root

from .base_power_model import AbstractPowerModel


class McPATPowerModel(AbstractPowerModel):
    def __init__(self, simobj, xml_tree):
        super().__init__(simobj)
        self.name = "McPATPowerModel"
        self._act_energy_tree_root = None
        self.init_act_energies(xml_tree)

    def init_act_energies(self, act_energies_tree):
        """Change prints to panics in the future"""
        try:
            self._act_energy_tree_root = act_energies_tree.getroot()
        except:
            print("Problem with XML file!")

    def get_act_energy(self, component, act_energy_type: str) -> float:
        try:
            for tags in self._act_energy_tree_root.iter(component):
                if tags.tag == component:
                    return float(tags.attrib[act_energy_type])
        except KeyError:
            print(
                "Could not find activation energy of type {act_energy_type}\
                in {component}!"
            )
            return 0.0

    def convert_to_watts(self, value: float) -> float:
        """Note that McPAT AEs are already in terms of J,
        no need for conversion"""

        time = Root.getInstance().resolveStat("simSeconds").total
        return value / time
