from m5.objects import Shader

from .accelwattch_base_power_model import AccelwattchBasePowerModel


class AccelwattchBaseMemoryPowerModel(AccelwattchBasePowerModel):
    def __init__(
        self, gpu: Shader, gpu_memory, act_energies, scaling_factors, interval
    ):
        super().__init__(gpu, act_energies, scaling_factors, interval)
        self.name = "AccelwattchBaseMemoryPowerModel"
        self._gpu_mem = gpu_memory

    def get_memory_stat(self, stat):
        try:
            value = self._gpu_mem.resolveStat(stat).total
            return value
        except KeyError:
            print(
                f"In GPU Memory {self._gpu_mem.path()},\
                        could not resolve stat {stat}"
            )

    def get_num_memory_controllers(self):
        return len(self._gpu_mem.get_memory_controllers())
