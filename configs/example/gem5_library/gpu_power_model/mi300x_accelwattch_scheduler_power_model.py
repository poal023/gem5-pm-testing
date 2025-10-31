from m5.objects import (
    RubyNetwork,
    Shader,
    SimpleNetwork,
)

from .accelwattch_base_power_model import AccelwattchBasePowerModel


class MI300XAccelwattchSchedulerPower(AccelwattchBasePowerModel):
    def __init__(self, gpu: Shader, act_energies, scaling_factors, interval):
        super().__init__(gpu, act_energies, scaling_factors, interval)
        self.name = "MI300XAccelwattchSchedulerPower"
        # print(f"{dir(self._simobj.get_parent().gpu_caches)}")

    def dynamic_power(self) -> float:
        self._num_cus = self.get_number_of_cus()
        energy = self.int_inst_window_energy()
        return self.convert_to_watts(energy)

    def static_power(self) -> float:
        return 0.0

    def int_inst_window_energy(self) -> float:
        int_insts = (
            sum(
                self.get_stat(f"CUs{i}.decodedIntInsts")
                for i in range(self._num_cus)
            )
            * self._scaling_factors["FP_INT"]
        )
        fp_insts = (
            sum(
                self.get_stat(f"CUs{i}.decodedFpInsts")
                for i in range(self._num_cus)
            )
            * self._scaling_factors["FP_INT"]
        )
        reads = writes = int_insts + fp_insts
        searches = 2 * (int_insts + fp_insts)

        return (
            reads * self._act_energies["IntInstWindow"]["Read"]
            + writes * self._act_energies["IntInstWindow"]["Write"]
            + searches * self._act_energies["IntInstWindow"]["Search"]
            + writes * self._act_energies["InstSel"]
        )
