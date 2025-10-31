from m5.objects import Shader

from .accelwattch_base_power_model import AccelwattchBasePowerModel


class MI300XAccelwattchConstantPower(AccelwattchBasePowerModel):
    def __init__(self, gpu: Shader, act_energies, scaling_factors, interval):
        super().__init__(gpu, act_energies, scaling_factors, interval)
        self.name = "MI300XAccelwattchConstantPower"

    def dynamic_power(self) -> float:
        self._num_cus = self.get_number_of_cus()
        energy = self.int_inst_window_energy()
        return self.convert_to_watts(energy)

    def static_power(self) -> float:
        return 0.0

    def int_inst_window_energy(self) -> float:
        int_insts = sum(
            self.get_stat(f"CUs{i}.decodedIntInsts")
            for i in range(self._num_cus)
        )
        fp_insts = sum(
            self.get_stat(f"CUs{i}.decodedFpInsts")
            for i in range(self._num_cus)
        )
        reads = writes = int_insts + fp_insts
        searches = 2 * (int_insts + fp_insts)

        return (
            reads * self._act_energies["IntInstWindow"]["Read"]
            + writes * self._act_energies["IntInstWindow"]["Write"]
            + searches * self._act_energies["IntInstWindow"]["Search"]
            + writes * self._act_energies["InstSel"]
        )
