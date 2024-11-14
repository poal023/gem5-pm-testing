from minor_mcpat_cpu_power_model.minor_mcpat_cpu_power_model import (
    MinorMcPATCpuPowerModel,
)

from m5.objects import *
from m5.stats import *
from m5.stats.gem5stats import get_simstat

from gem5.components.boards.simple_board import SimpleBoard
from gem5.components.cachehierarchies.classic.private_l1_shared_l2_cache_hierarchy import (
    PrivateL1SharedL2CacheHierarchy,
)
from gem5.components.memory.single_channel import SingleChannelLPDDR3_1600
from gem5.components.processors.cpu_types import CPUTypes
from gem5.components.processors.simple_processor import SimpleProcessor
from gem5.isas import ISA
from gem5.resources.resource import (
    BinaryResource,
    CustomResource,
    Resource,
)
from gem5.resources.workload import CustomWorkload
from gem5.simulate.simulator import Simulator

# from mcpat_minor_power_model.tournament_bp_power_model import *

# from l1l2_cache_pm.power_model_l1i import L1IPowerModel
# from l1l2_cache_pm.power_model_l1d import L1DPowerModel
# from l1l2_cache_pm.power_model_l2 import L2PowerModel
"""
from l1l2_cache_pm.l1l2_cache_with_pm import (
        PrivateL1SharedL2CacheHierarchy
)
"""

cache_hierarchy = PrivateL1SharedL2CacheHierarchy(
    l1d_size="32kB", l1i_size="32kB", l2_size="128kB"
)
mem = SingleChannelLPDDR3_1600("1GiB")
processor = SimpleProcessor(cpu_type=CPUTypes.MINOR, num_cores=1, isa=ISA.ARM)

for cores in processor.get_cores():
    for c in cores.core.descendants():
        if not isinstance(c, m5.objects.BaseCPU):
            continue
        c.power_state.default_state = "ON"
        c.power_model = MinorMcPATCpuPowerModel(c)


"""
l1i = cache_hierarchy.l1icaches
l1i.power_state.default_state = "ON"
l1i.power_model = L1IPowerModel(l1i)

l1d = cache_hierarchy.l1dcaches
l1d.power_state.default_state = "ON"
l1d.power_model = L1DPowerModel(l1d)

l2 = cache_hierarchy.l2caches
l2.power_state.default_state = "ON"
l2.power_model = L2PowerModel(l2)
"""

board = SimpleBoard(
    clk_freq="2GHz",
    processor=processor,
    memory=mem,
    cache_hierarchy=cache_hierarchy,
)
binary = Resource("arm-hello64-static")
board.set_se_binary_workload(binary)

print(vars(processor.get_cores()[0].core.icache_port))
for b in board.descendants():
    if isinstance(b, m5.objects.Cache) is True:
        print(b)

# Setup the Simulator and run the simulation.
simulator = Simulator(board=board)
simulator.run()
