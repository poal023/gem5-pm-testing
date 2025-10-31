from math import ceil

from m5.objects import Shader
from m5.util.convert import (
    anyToFrequency,
    toFrequency,
)

from .accelwattch_base_memory_power_model import (
    AccelwattchBaseMemoryPowerModel,
)
from .mi300x_accelwattch_memory_backend_power_model import (
    MI300XAccelwattchMemoryBackendPower,
)
from .mi300x_accelwattch_memory_frontend_power_model import (
    MI300XAccelwattchMemoryFrontendPower,
)
from .mi300x_accelwattch_memory_phy_power_model import (
    MI300XAccelwattchMemoryPhyPower,
)


class MI300XAccelwattchMemoryCtrlPower(AccelwattchBaseMemoryPowerModel):
    def __init__(
        self, gpu: Shader, gpu_memory, act_energies, scaling_factors, interval
    ):
        super().__init__(
            gpu, gpu_memory, act_energies, scaling_factors, interval
        )
        self.name = "MI300XAccelwattchMemoryCtrlPower"
        self._llc_block_size = (
            int(ceil(gpu._cache_line_size / 8.0)) + gpu._cache_line_size
        )
        self._data_bus_width = int(
            ceil(self._gpu_mem._dram[0].device_bus_width / 8.0)
        ) + int(self._gpu_mem._dram[0].device_bus_width)
        self._frontend = MI300XAccelwattchMemoryFrontendPower(
            gpu, gpu_memory, act_energies, scaling_factors, interval
        )
        self._backend = MI300XAccelwattchMemoryBackendPower(
            gpu, gpu_memory, act_energies, scaling_factors, interval
        )
        self._phy = MI300XAccelwattchMemoryPhyPower(
            gpu, gpu_memory, act_energies, scaling_factors, interval
        )

    def dynamic_power(self) -> float:
        return (
            self._frontend.dynamic_power()
            + self._backend.dynamic_power()
            + self._phy.dynamic_power()
        )

    def static_power(self) -> float:
        return 0.0
