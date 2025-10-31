from math import ceil

from m5.objects import Shader

from .base_power_model import AbstractPowerModel


class AccelwattchBasePowerModel(AbstractPowerModel):
    def __init__(
        self, simobj: Shader, act_energies, scaling_factors, interval
    ):
        super().__init__(simobj, interval)
        self.name = "AccelwattchBasePowerModel"
        self._act_energies = act_energies
        self._scaling_factors = scaling_factors
        """ # of CUs is a placeholder, each class will need to change this
            upon execution.
        """
        self._num_cus = 0

    def convert_to_watts(self, value: float) -> float:
        """gem5 Simulates 1e12 ticks / s, so this is fine"""
        """ You could do the long formula, that being:
            period = self._simobj.clock_domain.clock.getValue()
            cycles = ticks / (1e12/period)
            time = cycles / (1e12/period)
        """

        ticks = self.get_stat("shaderActiveTicks")
        time = ticks / 1e12
        return value / time

    def get_number_of_cus(self) -> float:
        """Get the number of compute units passed to this GPU
        Paticularly useful if you need to sum the stats of
        all CUs into one number
        """
        return len(self._simobj.get_compute_units())

    def get_number_of_SIMDs(self) -> float:
        """Gets the number of SIMD units on this GPU.
        Similar reasoning as above, useful if you
        need to sum the stats for say, a VRF or SRF.
        """
        return self._simobj.get_compute_units()[0].num_SIMDs

    def get_SIMD_width(self) -> float:
        return self._simobj.get_compute_units()[0].simd_width.getValue()

    def get_wf_size(self) -> float:
        return self._simobj.get_compute_units()[0].wf_size.getValue()

    def get_num_gmem_pipelines(self) -> float:
        return self._simobj.get_compute_units()[
            0
        ].num_global_mem_pipes.getValue()

    def get_num_smem_pipelines(self) -> float:
        return self._simobj.get_compute_units()[
            0
        ].num_shared_mem_pipes.getValue()

    def get_total_cycles(self) -> float:
        return (
            self.get_stat("shaderActiveTicks")
            / self._simobj.clk_domain.clock.getValue()[0]
        )

    def get_avg_idle_cores(self) -> float:
        """Gets the number of avg. idle cores during simulation.
        There's no direct stat, but my proxy is basically
        take, on average, how many cycles the CUs were idle,
        and then get the proprtion of idle / total cycles.
        Once we get this proportion, multiply it by # of
        CUs
        """
        avg_idle_cycles = (
            sum(
                self.get_stat(f"CUs{i}.ExecStage.numCyclesWithNoIssue")
                for i in range(self.get_number_of_cus())
            )
        ) / self.get_number_of_cus()

        cycles = self.get_total_cycles()
        return ceil(self.get_number_of_cus() * (avg_idle_cycles / cycles))

    def get_avg_active_cores(self) -> float:
        idle_cores = self.get_avg_idle_cores()
        cus = self.get_number_of_cus()
        return (cus - idle_cores) / cus

    def get_gpu_duty_cycle(self) -> float:
        avg_active_cycles = (
            sum(
                self.get_stat(f"CUs{i}.ExecStage.numCyclesWithInstrIssued")
                for i in range(self.get_number_of_cus())
            )
            / self.get_number_of_cus()
        )
        cycles = self.get_total_cycles()
        return avg_active_cycles / cycles

    def get_avg_threads_in_wf(self) -> float:
        cus = self.get_number_of_cus()
        avg_threads = (
            sum(self.get_stat(f"CUs{i}.vALUUtilization") for i in range(cus))
        ) / cus
        return avg_threads / 100 * self.get_wf_size()
