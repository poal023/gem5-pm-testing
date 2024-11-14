import xml.etree.ElementTree as ET

from m5.objects import Root

from .base_power_model import AbstractPowerModel


class McPATPowerModel(AbstractPowerModel):
    def __init__(self, act_energies_path=None, xml_out_path=None):
        super().__init__()
        self.name = "McPATPowerModel"
        self.act_energy_tree_root = None
        self.init_act_energies(self.act_energies_path)

    def init_act_energies(self, act_energies_path):
        """Change prints to panics in the future"""
        try:
            self.act_energy_tree_root = ET.parse(act_energies_path).getroot()
        except xml.etree.ElementTree.ParseError:
            print("Malformatted XML Tree, please check the file")
        except FileNotFoundError:
            print("Path for Activation Energies was not found!")

    def obtain_act_energy(self, component, act_energy_type):
        for tags in act_energy_tree_root.iter(component):
            if tags.tag == act_energy_type:
                return float(tags.attrib[act_energy_type])

    def convert_to_watts(self, value: float) -> float:
        """Note that McPAT AEs are already in terms of J, no need for conversion"""
        time = Root.getInstance().resolveStat("simSeconds").total
        value_in_j = value
        return value_in_j
