from m5.objects import Shader

from .accelwattch_base_power_model import AccelwattchBasePowerModel


class MI300XAccelwattchIdlePower(AccelwattchBasePowerModel):
    def __init__(self, gpu: Shader, act_energies, scaling_factors, interval):
        super().__init__(gpu, act_energies, scaling_factors, interval)
        self.name = "MI300XAccelwattchIdlePower"
        self._num_units = 4.0
        self._num_pipelines = 1.0

    def dynamic_power(self) -> float:
        self._num_cus = self.get_number_of_cus()
        energy = self.idle_energy()
        return self.convert_to_watts(energy)

    def static_power(self) -> float:
        return 0.0

    def idle_energy(self) -> float:
        time = self.get_stat("shaderActiveTicks") / 1e12
        return (
            self.get_avg_idle_cores()
            * self._scaling_factors["IDLE_CORE_POWER"]
            * time
        )
