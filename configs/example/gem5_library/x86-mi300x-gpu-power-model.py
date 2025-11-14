# Copyright (c) 2024 Advanced Micro Devices, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its
# contributors may be used to endorse or promote products derived from this
# software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

"""
Script to run a full system GPU simulation.

Usage:
------
```
scons build/VEGA_X86/gem5.opt
./build/VEGA_X86/gem5.opt
    configs/example/gem5_library/x86-viper-gpu.py
    --image <disk image>
    --kernel <kernel>
    --app <gpu application>
```

Example:
--------
```
./build/VEGA_X86/gem5.opt
    configs/example/gem5_library/x86-viper-gpu.py
    --image ./gem5-resources/src/x86-ubuntu-gpu-ml/disk-image/x86-ubuntu-gpu-ml
    --kernel ./gem5-resources/src/x86-ubuntu-gpu-ml/vmlinux-gpu-ml
    --app ./gem5-resources/src/gpu/square/bin.default/square.default
```
"""

import argparse

from gem5.coherence_protocol import CoherenceProtocol
from gem5.components.devices.gpus.amdgpu import (
    MI210,
    MI300X,
)
from gem5.components.memory import HBM2Stack
from gem5.components.memory.memory import ChanneledMemory
from gem5.components.memory.single_channel import SingleChannelDDR4_2400
from gem5.components.processors.cpu_types import CPUTypes
from gem5.components.processors.simple_processor import SimpleProcessor
from gem5.isas import ISA
from gem5.prebuilt.viper.board import ViperBoard
from gem5.prebuilt.viper.cpu_cache_hierarchy import ViperCPUCacheHierarchy
from gem5.resources.resource import (
    DiskImageResource,
    FileResource,
)
from gem5.simulate.exit_event import ExitEvent
from gem5.simulate.exit_handler import *
from gem5.simulate.simulator import Simulator
from gem5.utils.requires import requires

""" Accelwattch Power Model Imports """

from gpu_power_model.mi300x_accelwattch_power_model import (
    MI300XAccelwattchPowerModel,
)

from m5.objects import (
    GPU_VIPER_SQC_Controller,
    HBMCtrl,
    MemInterface,
    Root,
    RubyCache,
    Shader,
    SimObject,
)

from gem5.components.cachehierarchies.ruby.caches.viper.sqc import SQCCache
from gem5.components.cachehierarchies.ruby.caches.viper.tcc import TCCCache
from gem5.components.cachehierarchies.ruby.caches.viper.tcp import TCPCache
from gem5.components.memory.dram_interfaces.gddr import GDDR5_4000_2x32

requires(
    isa_required=ISA.X86,
    coherence_protocol_required=CoherenceProtocol.GPU_VIPER,
)


"""
def handle_workbegin():
    print("Encountered beginning of ROI")
    gpu = Root.getInstance().board.gpus[0]
    #gpu.shader.power_model[0].pm[0].startSampling()
    yield False

def handle_workend():
    print("Encountered end of ROI")
    gpu = Root.getInstance().board.gpus[0]
    #gpu.shader.power_model[0].pm[0].stopSampling()
    yield True

"""


class BeginExitHandler(ExitHandler, hypercall_num=3333):

    def _process(self, simulator):
        print("BeginExitHandler: Hypercall 3333 detected. Resetting stats.")
        gpu = Root.getInstance().board.gpus[0]
        gpu.shader.power_model[0].pm[0].startSampling()
        # gpu.shader.power_model[0].pm[0].dynamic_power()

    def _exit_simulation(self):
        return False  # Continue simulation


class EndExitHandler(ExitHandler, hypercall_num=3334):

    def _process(self, simulator):
        gpu = Root.getInstance().board.gpus[0]
        gpu.shader.power_model[0].pm[0].stopSampling()

        print("EndExitHandler: Hypercall 3334 detected. Dumping stats.")
        m5.stats.dump()

    def _exit_simulation(self):
        return True  # Exit simulation


# Kernel, disk, and applications are obtained locally.
parser = argparse.ArgumentParser()

parser.add_argument(
    "--image",
    type=str,
    required=True,
    help="Full path to the gem5-resources x86-ubuntu-gpu-ml disk-image.",
)

parser.add_argument(
    "--kernel",
    type=str,
    required=True,
    help="Full path to the gem5-resources vmlinux-gpu-ml kernel.",
)

parser.add_argument(
    "--app",
    type=str,
    required=True,
    help="Path to GPU application, python script, or bash script to run",
)

parser.add_argument(
    "--kvm-perf",
    default=False,
    action="store_true",
    help="Use KVM perf counters to give accurate GPU insts/cycles with KVM",
)

args = parser.parse_args()

# stdlib only supports up to 3GiB currently. This will need to be expanded in
# the future.
memory = SingleChannelDDR4_2400(size="3GiB")

# Note: Only KVM and ATOMIC work due to buggy MOESI_AMD_Base protocol.
processor = SimpleProcessor(cpu_type=CPUTypes.KVM, isa=ISA.X86, num_cores=2)

for core in processor.cores:
    if core.is_kvm_core():
        core.get_simobject().usePerf = args.kvm_perf

# gddr = GDDR5_4000_2x32(device_size="16GiB")

# The GPU must be created first so we can assign CPU-side DMA ports to the
# CPU cache hierarchy.
# gpu_memory = HBM2Stack(size="16GiB")
gpu0 = MI300X(gpu_memory=HBM2Stack(size="16GiB"))
# gpu0 = MI210(gpu_memory=HBM2Stack(size="16GiB"), use_garnet=True)
# gpu0 = MI300X(gpu_memory=gpu_memory)


""" Accelwattch Power Model """
act_energies = {
    "IB": {"Read": 2.54512e-13, "Write": 3.33324e-13},
    "IRF": {"Read": 3.02599e-11, "Write": 3.03936e-11},
    "OPC": 9.6156e-14,
    "xbar_rfu": 1.52382e-10,
    "arbiter_rfu": 2.57026e-13,
    "ALU": 2.30936e-13,
    "FPU": 1.88535e-11,
    "SFU": 3.86739e-11,
    "InstSel": 8.42839e-13,
    "IntInstWindow": {
        "Read": 3.19756e-13,
        "Write": 4.06628e-13,
        "Search": 1.07235e-12,
    },
    "Pipeline": 3.24487e-10,
    "icache": {"Read": 1.74322e-11, "Write": 1.89846e-11, "Search": 0},
    "icacheMissb": {"Write": 5.61104e-12, "Search": 5.27101e-12},
    "icacheIfb": {"Write": 5.40753e-12, "Search": 5.10543e-12},
    "icachePrefetchb": {"Write": 5.40753e-12, "Search": 5.10543e-12},
    "SharedMemory": {"Read": 1.10716e-10},
    "xbar_shared": 3.36513e-11,
    "dcache": {"Read": 1.24809e-11, "Write": 1.42577e-11},
    "dcacheTag": 1.00797e-12,
    "dcacheMissb": {"Write": 2.21128e-12, "Search": 2.50593e-12},
    "dcacheIfb": {"Write": 1.90158e-12, "Search": 2.2674e-12},
    "dcachePrefetchb": {"Write": 1.90158e-12, "Search": 2.2674e-12},
    "l2cache": {"Read": 5.45557e-11, "Write": 6.5393e-11},
    "l2cacheTag": {"Read": 1.87159e-12, "Write": 6.70033e-12},
    "l2cacheMissb": {"Write": 1.09324e-12, "Search": 1.09324e-12},
    "l2cacheIfb": {"Write": 5.40753e-12, "Search": 5.10543e-12},
    "l2cachePrefetchb": {"Write": 5.40753e-12, "Search": 5.10543e-12},
    "l2cacheWbb": {"Write": 5.40753e-12, "Search": 5.10543e-12},
    "dram_pre_coeff": 3.8475e-8,
    "dram_rd_coeff": 7.74707143e-8,
    "dram_wr_coeff": 3.54664286e-8,
    "memFrontendBuffer": {
        "Read": 5.77961e-13,
        "Write": 7.89614e-13,
        "Search": 1.74426e-12,
    },
    "memRWBuffer": {"Read": 3.80661e-13, "Write": 5.84396e-13},
    "PRT": {"Read": 4.38159e-12, "Write": 6.09919e-12},
    "PRC": {"Read": 1.14781e-13, "Write": 1.33843e-13},
    "threadMasks": {"Read": 7.18764e-13, "Write": 6.11804e-13},
    "perAccessCoalescing": 1.45326e-13,
    "NoCRouter": {"Read": 1.03984e-13, "Write": 1.03984e-13},
    "NoCCrossbar": 2.131711e-12,
    "NoCArbiter": 1.58013e-13,
}
scaling_factors = {
    "TOT_INST": 10,  # Corresponds to IB AF (total WF/Warp insts)
    "FP_INT": 4.661,  # Scheduler AF
    "IC_H": 8.593489331,  # I$ Hit
    "IC_M": 29.735231,  # I$ Miss
    "DC_RH": 9.835033124,  # D$ Read Hit
    "DC_RM": 10.95446778,  # D$ Read Miss
    "DC_WH": 0.679656761,  # D$ Write Hit
    "DC_WM": 17.67551799,  # D$ Write Miss
    "CC_H": 0.1107,  # C$ Hit
    "CC_M": 0.1233,  # C$ Miss
    "SHRD_ACC": 0.779992642,  # SHMEM/LDS Accs.
    "REG_RD": 0.100560581,  # RF Reads
    "REG_WR": 0.140604679,  # RF Writes
    "INT_ACC": 14.98768151,  # Int Accs.
    "FP_ACC": 0.529670751,  # Fp Accs.
    "DP_ACC": 0.777229051,  # Dp Accs.
    "INT_MUL_ACC": 0.115098,
    "INT_MUL24_ACC": 0,  # Note: SASS version DNI the scaling factors
    "INT_MUL32_ACC": 0,  # which are == to 0.
    "INT_DIV_ACC": 0,
    "FP_DIV_ACC": 0,
    "DP_DIV_ACC": 0,
    "FP_MUL_ACC": 0.089517055,
    "FP_SQRT_ACC": 0.195089,
    "FP_LG_ACC": 0.12552166,
    "FP_SIN_ACC": 0.1333630,
    "FP_EXP_ACC": 0.3620441,
    "DP_MUL_ACC": 0.1321288,
    "TENSOR_ACC": 0.8154546,
    "TEX_ACC": 0.115100088,  # TexU Accs.
    "MEM_RD": 0.025941068,
    "MEM_WR": 0.031443719,
    "MEM_PRE": 0.008647023,
    "L2_RH": 1.260867526,  # L2 Read Hit
    "L2_RM": 2.394535301,  # L2 Read Miss
    "L2_WH": 4.124916,  # L2 Write Hit
    "L2_WM": 1.222707601,  # L2 Write Miss
    "NOC_A": 32.09037703,  # NoC Accs.
    "PIPE_A": 0.514,  # Pipeline Accs.
    "CONSTANT_POWER": 32.32522272,
    "IDLE_CORE_POWER": 0.28279166,
    """ Constants for the static power model """
    "static_cat1_flane": 15.29035866,
    "static_cat1_addlane": 0.586233603,
    "static_cat2_flane": 18.6179906,
    "static_cat2_addlane": 0.645228013,
    "static_cat3_flane": 19.10017723,
    "static_cat3_addlane": 0.726863055,
    "static_cat4_flane": 18.55029744,
    "static_cat4_addlane": 0.6099397,
    "static_cat5_flane": 14.74826681,
    "static_cat5_addlane": 0.514367937,
    "static_cat6_flane": 48.94875596,
    "static_cat6_addlane": 0.0,
    "static_light_flane": 1.965373811,
    "static_light_addlane": 0.003966868,
    "static_intadd_flane": 19.70468506,
    "static_intadd_addlane": 0.388578623,
    "static_intmul_flane": 16.64811823,
    "static_intmul_addlane": 0.281803166,
    "static_geomean_flane": 17.21745077,
    "static_geomean_addlane": 0.650630555,
    "static_shared_flane": 31.40965691,
    "static_l1_flane": 34.79491352,
    "static_l2_flane": 17.30654755,
}

cache_hierarchy = ViperCPUCacheHierarchy(
    l1d_size="32KiB",
    l1d_assoc=8,
    l1i_size="32KiB",
    l1i_assoc=8,
    l2_size="1MiB",
    l2_assoc=16,
    l3_size="16MiB",
    l3_assoc=16,
)

board = ViperBoard(
    clk_freq="3GHz",
    processor=processor,
    memory=memory,
    cache_hierarchy=cache_hierarchy,
    gpus=[gpu0],
)

# Example of using a local disk image resource
disk = DiskImageResource(local_path=args.image, root_partition="1")
kernel = FileResource(local_path=args.kernel)

board.set_kernel_disk_workload(
    kernel=kernel,
    disk_image=disk,
    readfile_contents=board.make_gpu_app(gpu0, args.app, ""),
)

simulator = Simulator(
    board=board,
    # on_exit_event={
    #    ExitEvent.WORKBEGIN : handle_workbegin(),
    #    ExitEvent.WORKEND : handle_workend(),
    # }
)
""" Power Model Hack:
    ---
    In the stdlib, cache simobjs don't immediately appear,
    and thus aren't accessible before simulator instantiation.
    To be able to access the cache objects and give them a
    PM/pass them into the GPU PM, we can instantiate the sim
    now. I highly discourage doing this in the future.
"""
print(gpu0._memory.path())
gpu_memory = gpu0._memory
for gpus in gpu0.descendants():
    if isinstance(gpus, Shader):
        print(f"Num SIMDs: {gpus.get_compute_units()[0].num_SIMDs}")
        gpus.power_state.default_state = "ON"
        gpus.power_model = MI300XAccelwattchPowerModel(
            gpus, gpu_memory, act_energies, scaling_factors
        )
    continue
"""
gpu0.power_stat.default_stat = "ON"
gpu0.power_model = MI300XAccelwattchPowerModel(gpus, gpu_memory,
                                               act_energies,
                                               scaling_factors)
"""
simulator._instantiate()
print(gpu_memory.path())
for caches in board.gpus[0].gpu_caches.descendants():
    if isinstance(caches, SQCCache):
        print(f"Found SQC Cache! Has path of {caches.path()}")
    elif isinstance(caches, TCCCache):
        print("Found TCC Cache!")
    elif isinstance(caches, TCPCache):
        print("Found TCP Cache!")
    else:
        continue


simulator.run()

flits_injected = (
    Root.getInstance()
    .resolveStat("board.gpus.gpu_caches.ruby_gpu.network.flits_injected")
    .total
)
flits_received = (
    Root.getInstance()
    .resolveStat("board.gpus.gpu_caches.ruby_gpu.network.flits_received")
    .total
)
noc_power = (
    (flits_injected + flits - received)
    * scaling_factors["NOC_A"]
    * (
        act_energies["NoCCrossbar"]
        + act_energies["NoCArbiter"]
        + act_energies["NoCRouter"]["Read"]
        + act_energies["NoCRouter"]["Write"]
    )
)
print(f"NOC: {noc_power}")
