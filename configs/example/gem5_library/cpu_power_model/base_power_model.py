# don't use `import *` and import the specific things you need
from m5.objects import Root
from m5.objects import BaseMinorCPU, BaseO3CPU, BaseSimpleCPU

bp_stats = {
    "BTBLookups": "branchPred.BTBLookups",
    "BTBHits": "branchPred.BTBHits",
    "BTBUpdates": "branchPred.BTBUpdates",
    "condPredicted": "branchPred.condPredicted",
    "condMispredicted": "branchPred.condIncorrect",
}

minor_stats = {
    "numIntAluAccesses": "executeStats0.numIntAluAccesses",
    "numFpAluAccesses": "executeStats0.numFpAluAccesses",
    "numVecAluAccesses": "executeStats0.numVecAluAccesses",
    "numIntRegReads": "executeStats0.numIntRegReads",
    "numIntRegWrites": "executeStats0.numIntRegWrites",
    "numFpRegReads": "executeStats0.numFpRegReads",
    "numFpRegWrites": "executeStats0.numFpRegWrites",
    "numMiscRegReads": "executeStats0.numFpRegReads",
    "numMiscRegWrites": "executeStats0.numFpRegWrites",
    "BTBLookups": bp_stats["BTBLookups"],
    "BTBHits": bp_stats["BTBHits"],
    "BTBUpdates": bp_stats["BTBUpdates"],
    "condPredicted": bp_stats["condPredicted"],
    "condMispredicted": bp_stats["condMispredicted"],
}

o3_stats = {
    "numIntAluAccesses": "intAluAccesses",
    "numFpAluAccesses": "fpAluAccesses",
    "numVecAluAccesses": "vecAluAccesses",
    "numIntRegReads": "executeStats0.numIntRegReads",
    "numIntRegWrites": "executeStats0.numIntRegWrites",
    "numFpRegReads": "executeStats0.numFpRegReads",
    "numFpRegWrites": "executeStats0.numFpRegWrites",
    "numMiscRegReads": "executeStats0.numFpRegReads",
    "numMiscRegWrites": "executeStats0.numFpRegWrites",
    "BTBLookups": bp_stats["BTBLookups"],
    "BTBHits": bp_stats["BTBHits"],
    "BTBUpdates": bp_stats["BTBUpdates"],
    "condPredicted": bp_stats["condPredicted"],
    "condMispredicted": bp_stats["condMispredicted"],
}


# Class names should be in CamelCase. Also, this is an abstract base class.
# I.e., no one should ever create an instance of this class.
class AbstractPowerModel:
    def __init__(self, simobj):
        # You shouldn't use a list of functions. Instead, implement the
        # dynamic/static power functions in the sub classes
        # using a leading underscore is a good idea so that it's not
        # considered a simobject child
        self._simobj = simobj
        self.name = "AbstractPowerModel"  # should be overridden for debugging
        # I don't like the above, but it's a little hack to make the debugging
        # easier.

    # A better name is "get_stat"
    def get_stat(self, stat):
        """Get the value of a stat, if it exists. Otherwise, return 0.0"""
        stats_dictionary = {0: minor_stats, 1: minor_stats, 2: o3_stats}
        try:
            target_stat = stats_dictionary[self.check_cpu_type(self._simobj)][
                stat
            ]
            total = self._simobj.resolveStat(target_stat).total
            return total
        except KeyError:
            # In the future, this should be a `panic`
            print(f"{stat} not found in stats!")
            return 0.0

    def dynamic_power(self) -> float:
        """Returns dynamic power in Watts"""
        # These should not be implemented in this (abstract) base class
        raise NotImplementedError

    def static_power(self) -> float:
        """Returns static power in Watts"""
        # These should not be implemented in this (abstract) base class
        raise NotImplementedError

    def check_cpu_type(self, core):
        if isinstance(core, BaseMinorCPU):
            return 0
        elif isinstance(core, BaseSimpleCPU):
            return 1
        elif isinstance(core, BaseO3CPU):
            return 2

    def convert_to_watts(self, value: float) -> float:
        """Convert energy in nanojoules to Watts"""
        time = Root.getInstance().resolveStat("simSeconds").total
        value_in_j = value * 1e-9
        return value_in_j / time
