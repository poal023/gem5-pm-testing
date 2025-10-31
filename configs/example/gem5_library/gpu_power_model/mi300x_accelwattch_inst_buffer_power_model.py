from m5.objects import Shader

from .accelwattch_base_power_model import AccelwattchBasePowerModel


class MI300XAccelwattchInstBufferPower(AccelwattchBasePowerModel):
    def __init__(self, gpu: Shader, act_energies, scaling_factors, interval):
        super().__init__(gpu, act_energies, scaling_factors, interval)
        self.name = "MI300XAccelwattchInstBufferPower"
        """ 40 is a placeholder, changed upon execution."""

    def dynamic_power(self) -> float:
        self._num_cus = self.get_number_of_cus()
        return self.convert_to_watts(self.inst_buffer_energy())

    def static_power(self) -> float:
        return 0.0

    def inst_buffer_energy(self) -> float:
        reads = writes = (
            sum(
                self.get_stat(f"CUs{i}.decodedInsts")
                for i in range(self._num_cus)
            )
            * self._scaling_factors["TOT_INST"]
        )
        return (
            reads * self._act_energies["IB"]["Read"]
            + writes * self._act_energies["IB"]["Write"]
        )
