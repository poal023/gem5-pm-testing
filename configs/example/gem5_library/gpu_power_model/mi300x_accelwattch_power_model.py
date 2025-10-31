from m5.objects import (
    PowerModel,
    PowerModelPyFunc,
    Shader,
)

from .accelwattch_base_power_model import AccelwattchBasePowerModel
from .mi300x_accelwattch_alu_power_model import MI300XAccelwattchALUPower
from .mi300x_accelwattch_dcache_power_model import (
    MI300XAccelwattchDataCachePower,
)
from .mi300x_accelwattch_dram_power_model import MI300XAccelwattchDRAMPower
from .mi300x_accelwattch_fpu_power_model import MI300XAccelwattchFPUPower
from .mi300x_accelwattch_icache_power_model import (
    MI300XAccelwattchInstCachePower,
)
from .mi300x_accelwattch_idle_power_model import MI300XAccelwattchIdlePower
from .mi300x_accelwattch_inst_buffer_power_model import (
    MI300XAccelwattchInstBufferPower,
)
from .mi300x_accelwattch_l2cache_power_model import (
    MI300XAccelwattchL2CachePower,
)
from .mi300x_accelwattch_lds_power_model import MI300XAccelwattchLDSPower
from .mi300x_accelwattch_memory_ctrl_power_model import (
    MI300XAccelwattchMemoryCtrlPower,
)
from .mi300x_accelwattch_noc_power_model import MI300XAccelwattchNoCPower
from .mi300x_accelwattch_pipeline_power_model import (
    MI300XAccelwattchPipelinePower,
)
from .mi300x_accelwattch_register_file_power_model import (
    MI300XAccelwattchRegisterFilePower,
)
from .mi300x_accelwattch_scheduler_power_model import (
    MI300XAccelwattchSchedulerPower,
)
from .mi300x_accelwattch_sfu_power_model import MI300XAccelwattchSFUPower


class MI300XAccelwattchPowerOn(PowerModelPyFunc):
    def __init__(self, gpu: Shader, gpu_memory, act_energies, scaling_factors):
        super().__init__()
        interval = 500
        self._ib = MI300XAccelwattchInstBufferPower(
            gpu, act_energies, scaling_factors, interval
        )
        self._rf = MI300XAccelwattchRegisterFilePower(
            gpu, act_energies, scaling_factors, interval
        )
        self._lds = MI300XAccelwattchLDSPower(
            gpu, act_energies, scaling_factors, interval
        )
        self._ialu = MI300XAccelwattchALUPower(
            gpu, act_energies, scaling_factors, interval
        )
        self._fpu = MI300XAccelwattchFPUPower(
            gpu, act_energies, scaling_factors, interval
        )
        self._sfu = MI300XAccelwattchSFUPower(
            gpu, act_energies, scaling_factors, interval
        )
        self._schedu = MI300XAccelwattchSchedulerPower(
            gpu, act_energies, scaling_factors, interval
        )
        self._icache = MI300XAccelwattchInstCachePower(
            gpu, act_energies, scaling_factors, interval
        )
        self._dcache = MI300XAccelwattchDataCachePower(
            gpu, act_energies, scaling_factors, interval
        )
        self._mem_ctrl = MI300XAccelwattchMemoryCtrlPower(
            gpu, gpu_memory, act_energies, scaling_factors, interval
        )
        self._dram = MI300XAccelwattchDRAMPower(
            gpu, gpu_memory, act_energies, scaling_factors, interval
        )
        self._noc = MI300XAccelwattchNoCPower(
            gpu, act_energies, scaling_factors, interval
        )
        self._l2cache = MI300XAccelwattchL2CachePower(
            gpu, act_energies, scaling_factors, interval
        )
        self._pipeline = MI300XAccelwattchPipelinePower(
            gpu, act_energies, scaling_factors, interval
        )
        self._idle = MI300XAccelwattchIdlePower(
            gpu, act_energies, scaling_factors, interval
        )
        self._scaling_factors = scaling_factors
        self.pwr_interval = interval
        """
        self._static_model = MI300XAccelwattchStaticPower(gpu, act_energies,
                                                          scaling_factors)
        """
        self.dyn = self.dynamic_power
        self.st = self.static_power

    def dynamic_power(self):
        print(f"Instruction Buffer: {self._ib.dynamic_power()}")
        print(f"Instruction Scheduler: {self._schedu.dynamic_power()}")
        print(f"Instruction Cache: {self._icache.dynamic_power()}")
        print(f"Data Cache: {self._dcache.dynamic_power()}")
        print(f"LDS: {self._lds.dynamic_power()}")
        print(f"RF: {self._rf.dynamic_power()}")
        print(f"IALU: {self._ialu.dynamic_power()}")
        print(f"FPU: {self._fpu.dynamic_power()}")
        print(f"SFU: {self._sfu.dynamic_power()}")
        print(f"Pipeline: {self._pipeline.dynamic_power()}")
        print(f"Memory Controller: {self._mem_ctrl.dynamic_power()}")
        print(f"DRAM: {self._dram.dynamic_power()}")
        # print(f"NoC: {self._noc.dynamic_power()}")
        print(f"L2 Cache: {self._l2cache.dynamic_power()}")
        print(f"Idle CUs: {self._idle.dynamic_power()}")
        print(f"Constant: {self._scaling_factors['CONSTANT_POWER']}")
        power = (
            self._ib.dynamic_power()
            + self._schedu.dynamic_power()
            + self._icache.dynamic_power()
            + self._dcache.dynamic_power()
            + self._lds.dynamic_power()
            + self._rf.dynamic_power()
            + self._ialu.dynamic_power()
            + self._fpu.dynamic_power()
            + self._sfu.dynamic_power()
            + self._mem_ctrl.dynamic_power()
            + self._dram.dynamic_power()
            # + self._noc.dynamic_power()
            + self._l2cache.dynamic_power()
            + self._pipeline.dynamic_power()
            + self._idle.dynamic_power()
            + self._scaling_factors["CONSTANT_POWER"]
        )
        return power

    def static_power(self):
        int_add_accesses = self._ialu.iadd_static_coeff()
        int_mul_accesses = self._sfu.imul_static_coeff()
        int_accesses = int_add_accesses + int_mul_accesses

        fp_accesses = (
            self._fpu.fp_static_coeff() + self._sfu.fpmul_static_coeff()
        )
        dp_accesses = (
            self._fpu.dp_static_coeff() + self._sfu.dpmul_static_coeff()
        )
        sfu_accesses = self._sfu.sfu_static_coeff()
        tensor_accesses = self._sfu.tensor_static_coeff()
        tex_accesses = self._sfu.tex_static_coeff()

        l1_accesses = self._dcache.dcache_static_coeff()
        l2_accesses = self._l2cache.l2cache_static_coeff()
        lds_accesses = self._lds.lds_static_coeff()
        active_cores = self._ialu.get_avg_active_cores()
        avg_threads_in_wf = self._ialu.get_avg_threads_in_wf()

        base_static_power = 0.0
        lane_static_power = 0.0

        if avg_threads_in_wf == 0:
            if l1_accesses != 0:
                return self._scaling_factors["static_l1_flane"] * active_cores
            elif lds_accesses != 0:
                return (
                    self._scaling_factors["static_shared_flane"] * active_cores
                )
            elif l2_accesses != 0:
                return self._scaling_factors["static_l2_flane"] * active_cores
            else:
                return (
                    self._scaling_factors["static_light_flane"] * active_cores
                )

        if (
            (int_accesses != 0)
            and (fp_accesses != 0)
            and (dp_accesses != 0)
            and (sfu_accesses == 0)
            and (tensor_accesses == 0)
            and (tex_accesses == 0)
        ):
            base_static_power = self._scaling_factors["static_cat3_flane"]
            lane_static_power = self._scaling_factors["static_cat3_addlane"]
        elif (
            (int_accesses != 0)
            and (fp_accesses != 0)
            and (dp_accesses == 0)
            and (sfu_accesses == 0)
            and (tensor_accesses != 0)
            and (tex_accesses == 0)
        ):
            base_static_power = self._scaling_factors["static_cat6_flane"]
            lane_static_power = self._scaling_factors["static_cat6_addlane"]
        elif (
            (int_accesses != 0)
            and (fp_accesses != 0)
            and (dp_accesses == 0)
            and (sfu_accesses != 0)
            and (tensor_accesses == 0)
            and (tex_accesses == 0)
        ):
            base_static_power = self._scaling_factors["static_cat4_flane"]
            lane_static_power = self._scaling_factors["static_cat4_addlane"]
        elif (
            (int_accesses != 0)
            and (fp_accesses != 0)
            and (dp_accesses == 0)
            and (sfu_accesses == 0)
            and (tensor_accesses == 0)
            and (tex_accesses != 0)
        ):
            base_static_power = self._scaling_factors["static_cat5_flane"]
            lane_static_power = self._scaling_factors["static_cat5_addlane"]
        elif (
            (int_accesses != 0)
            and (fp_accesses != 0)
            and (dp_accesses == 0)
            and (sfu_accesses == 0)
            and (tensor_accesses == 0)
            and (tex_accesses == 0)
        ):
            base_static_power = self._scaling_factors["static_cat2_flane"]
            lane_static_power = self._scaling_factors["static_cat2_addlane"]
        elif (
            (int_accesses != 0)
            and (fp_accesses == 0)
            and (dp_accesses == 0)
            and (sfu_accesses == 0)
            and (tensor_accesses == 0)
            and (tex_accesses == 0)
        ):
            if (int_add_accesses != 0) and (int_mul_accesses == 0):
                base_static_power = self._scaling_factors[
                    "static_intadd_flane"
                ]
                lane_static_power = self._scaling_factors[
                    "static_intadd_addlane"
                ]
            elif (int_add_accesses == 0) and (int_mul_accesses != 0):
                base_static_power = self._scaling_factors[
                    "static_intmul_flane"
                ]
                lane_static_power = self._scaling_factors[
                    "static_intmul_addlane"
                ]
            else:
                base_static_power = self._scaling_factors["static_cat1_flane"]
                lane_static_power = self._scaling_factors[
                    "static_cat1_addlane"
                ]
        elif (
            (int_accesses == 0)
            and (fp_accesses == 0)
            and (dp_accesses == 0)
            and (sfu_accesses == 0)
            and (tensor_accesses == 0)
            and (tex_accesses == 0)
        ):
            lane_static_power = 0
            if l1_accesses != 0:
                base_static_power = self._scaling_factors["static_l1_flane"]
            elif lds_accesses != 0:
                base_static_power = self._scaling_factors[
                    "static_shared_flane"
                ]
            elif l2_accesses != 0:
                base_static_power = self._scaling_factors["static_l2_flane"]
            else:
                base_static_power = self._scaling_factors["static_light_flane"]
                lane_static_power = self._scaling_factors[
                    "static_light_addlane"
                ]
        else:
            base_static_power = self._scaling_factors["static_geomean_flane"]
            lane_static_power = self._scaling_factors["static_geomean_addlane"]

        total_static_power = (
            base_static_power + avg_threads_in_wf * lane_static_power
        ) * active_cores
        print(f"Static: {total_static_power}")
        print(f"\tBase static: {base_static_power}")
        print(f"\tLane static: {lane_static_power}")
        print(f"\tavg_threads: {avg_threads_in_wf}")
        print(f"\tactive cores: {active_cores}")
        return total_static_power


class MI300XAccelwattchPowerOff(PowerModelPyFunc):
    def __init__(self):
        super().__init__()
        self.dyn = lambda: 0.0
        self.st = lambda: 0.0


class MI300XAccelwattchPowerModel(PowerModel):
    def __init__(self, gpu, gpu_memory, act_energies, scaling_factors):
        super().__init__()
        # Choose a power model for every power state
        self.pm = [
            MI300XAccelwattchPowerOn(
                gpu, gpu_memory, act_energies, scaling_factors
            ),  # ON
            MI300XAccelwattchPowerOff(),  # CLK_GATED
            MI300XAccelwattchPowerOff(),  # SRAM_RETENTION
            MI300XAccelwattchPowerOff(),  # OFF
        ]
