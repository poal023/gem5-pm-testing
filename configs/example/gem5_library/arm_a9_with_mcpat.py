# Import helper libs
import argparse
import pathlib
import xml.etree.ElementTree as ET

from l1l2_cache_pm.l1l2_cache_with_pm import PrivateL1SharedL2CacheHierarchy

# Import PM Classes
from mcpat_power_model.inorder_mcpat_power_model.inorder_mcpat_cpu_power_model import (
    InorderMcPATCpuPowerModel,
)
from mcpat_power_model.o3_mcpat_power_model.o3_mcpat_cpu_power_model import (
    O3McPATCpuPowerModel,
)

# Import m5 objects
import m5
from m5.objects import (
    BaseCPU,
    Root,
    TournamentBP,
)

# Import gem5 components:
from gem5.components.boards.simple_board import SimpleBoard
from gem5.components.cachehierarchies.ruby.mesi_two_level_cache_hierarchy import (
    MESITwoLevelCacheHierarchy,
)
from gem5.components.memory.single_channel import SingleChannelLPDDR3_1600
from gem5.components.processors.cpu_types import CPUTypes
from gem5.components.processors.simple_processor import SimpleProcessor
from gem5.isas import ISA

# Import gem5 workload handler
from gem5.resources.resource import (
    BinaryResource,
    obtain_resource,
)
from gem5.simulate.exit_handler import ExitHandler
from gem5.simulate.simulator import (
    ExitEvent,
    Simulator,
)


class BeginExitHandler(ExitHandler, hypercall_num=1999):
    def _process(self, simulator):
        # This method is called when the hypercall occurs.
        print(f"BeginExitHandler, resetting stats")
        # Dump simulation statistics
        m5.stats.reset()

    def _exit_simulation(self):
        return False


class EndExitHandler(ExitHandler, hypercall_num=2000):
    def _process(self, simulator):
        # This method is called when the hypercall occurs.
        print(f"EndExitHandler, dumping stats")
        # Dump simulation statistics
        m5.stats.dump()

    def _exit_simulation(self):
        # We want to exit the simulation after this hypercall.
        return True


cpus = {
    "atomic": CPUTypes.ATOMIC,
    "timing": CPUTypes.TIMING,
    "minor": CPUTypes.MINOR,
    "o3": CPUTypes.O3,
}


def init_act_energies(args):
    act_energies = {
        "IntAlu": 6.22113e-12,
        "FpAlu": 1.86634e-11,
        "ComplexAlu": 1.24423e-11,
        "BTB": {"Read": 5.62534e-12, "Write": 8.68454e-12},
        "InstBuffer": {"Read": 6.69479e-12, "Write": 7.269e-12},
        "IDInst": 4.90024e-12,
        "IDOp": 4.89659e-12,
        "IDMisc": 4.90566e-12,
        "LoadStoreQueue": {
            "Read": 2.49139e-12,
            "Write": 2.57072e-12,
            "Search": 2.5361e-12,
        },
        "ITLB": {
            "Read": 1.4039e-12,
            "Write": 1.77965e-12,
            "Search": 3.49054e-12,
        },
        "DTLB": {
            "Read": 1.4039e-12,
            "Write": 1.77965e-12,
            "Search": 3.49054e-12,
        },
        "GlobalPred": {"Read": 2.81993e-12, "Write": 1.50057e-12, "Search": 0},
        "L1LocalPred": {
            "Read": 1.59669e-13,
            "Write": 2.99057e-13,
            "Search": 0,
        },
        "L2LocalPred": {
            "Read": 1.22289e-13,
            "Write": 1.96004e-13,
            "Search": 0,
        },
        "ChooserPred": {
            "Read": 2.81993e-12,
            "Write": 1.50057e-12,
            "Search": 0,
        },
        "RAS": {"Read": 3.36208e-13, "Write": 4.51353e-13, "Search": 0},
    }

    if args.cpu_type != "o3":
        act_energies["IntRegFile"] = {
            "Read": 1.93199e-12,
            "Write": 2.55776e-12,
        }
        act_energies["FpRegFile"] = {"Read": 1.3027e-12, "Write": 1.66805e-12}
        act_energies["IntBypass"] = 4.99873e-12
        act_energies["IntTagBypass"] = 1.24968e-12
        act_energies["FpBypass"] = 1.18181e-11
        act_energies["FpTagBypass"] = 2.08847e-12
        act_energies["MulBypass"] = 1.09294e-11
        act_energies["MulTagBypass"] = 1.82156e-12
        act_energies["Pipeline"] = 1.17338e-11
    else:
        act_energies["IntRegFile"] = {
            "Read": 2.14779e-12,
            "Write": 3.49231e-12,
        }
        act_energies["FpRegFile"] = {"Read": 1.44241e-12, "Write": 2.26658e-12}
        act_energies["IntBypass"] = 6.87115e-12
        act_energies["IntTagBypass"] = 1.56691e-12
        act_energies["FpBypass"] = 8.74963e-12
        act_energies["FpTagBypass"] = 1.88238e-12
        act_energies["MulBypass"] = 1.00743e-11
        act_energies["MulTagBypass"] = 2.16751e-12
        act_energies["IntInstWindow"] = {
            "Read": 1.50873e-12,
            "Write": 1.83695e-12,
            "Search": 2.67858e-12,
        }
        act_energies["FpInstWindow"] = {
            "Read": 1.35879e-12,
            "Write": 1.38643e-12,
            "Search": 1.61929e-12,
        }
        act_energies["IntFreeList"] = {
            "Read": 2.97125e-13,
            "Write": 3.43681e-13,
        }
        act_energies["FpFreeList"] = {"Read": 1.767e-13, "Write": 3.1542e-13}
        act_energies["IntFRAT"] = {
            "Read": 4.6752e-13,
            "Write": 6.88901e-13,
            "Search": 2.31626e-12,
        }
        act_energies["FpFRAT"] = {
            "Read": 3.31586e-13,
            "Write": 4.81804e-13,
            "Search": 1.83071e-12,
        }
        act_energies["IntDCL"] = 8.6783e-13
        act_energies["FpDCL"] = 8.6783e-13
        act_energies["SelLogic"] = 2.44692e-12
        act_energies["Pipeline"] = 6.34086e-12

    return act_energies


def _apply_pm(simobj, power_model_fn, so_type, act_energies):
    for desc in simobj.descendants():
        if not isinstance(desc, so_type):
            continue
        desc.power_state.default_state = "ON"
        desc.power_model = power_model_fn(desc, act_energies)


def simulation_main(args):
    cache_hierarchy = PrivateL1SharedL2CacheHierarchy(
        l1d_size="32kB", l1i_size="32kB", l2_size="1MB"
    )
    mem = SingleChannelLPDDR3_1600("1GiB")
    processor = SimpleProcessor(
        cpu_type=cpus[args.cpu_type], num_cores=1, isa=ISA.ARM
    )
    board = SimpleBoard(
        clk_freq="2GHz",
        processor=processor,
        memory=mem,
        cache_hierarchy=cache_hierarchy,
    )

    act_energies = init_act_energies(args)

    # Applying Power Model:
    for core in processor.get_cores():
        core.core.branchPred = TournamentBP()
        if args.cpu_type == "o3":
            _apply_pm(
                core, O3McPATCpuPowerModel, m5.objects.BaseO3CPU, act_energies
            )
        else:
            _apply_pm(
                core,
                InorderMcPATCpuPowerModel,
                m5.objects.BaseCPU,
                act_energies,
            )

    # Setting workload:
    if args.workload == "hello-world":
        board.set_se_binary_workload(obtain_resource("arm-hello64-static"))
    else:
        this_dir = pathlib.Path(__file__).parent.absolute()
        workload_path = str(this_dir / f"workloads/{args.workload}")
        board.set_se_binary_workload(BinaryResource(local_path=workload_path))

    simulator = Simulator(board=board)

    # scheduleTickExitAbsolute(20000000, "hello!")
    simulator.run()


def parse_cli_args(parser):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--cpu_type",
        type=str,
        choices=list(cpus.keys()),
        default="timing",
        help="CPU simulation mode. Default: %(default)s",
    )
    parser.add_argument(
        "--workload",
        type=str,
        choices=["hello-world", "iaxpy", "daxpy", "iax", "sax", "saxpy"],
        default="hello-world",
        help="Workload to run.",
    )

    return parser.parse_args()


parser = argparse.ArgumentParser()
args = parse_cli_args(parser)
simulation_main(args)
