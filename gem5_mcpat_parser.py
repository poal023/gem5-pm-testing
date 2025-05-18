import argparse
import os
import re
import subprocess
import xml.etree.ElementTree as ET

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import *


class McPATValidator:
    def __init__(self, xml_stats_path, gem5_stats_path, is_ooo, verbose):
        """
        Making the assumption that the core is
        the only thing to be validated right now...
        """
        self._filename = xml_stats_path
        self._xml_tree = None
        self._gem5_stats_path = gem5_stats_path
        self._gem5_stats = {}
        self._is_ooo = is_ooo
        self._verbose = verbose
        self.parse_gem5_stats()
        self.open_xml()
        self.results_to_xml()

    def open_xml(self):
        try:
            self._xml_tree = ET.parse(self._filename)
        except:
            panic("something went wrong!")

    def print_tree(self):
        root = self._xml_tree.getroot()
        ET.indent(root)
        print(ET.tostring(root, encoding="unicode"))

    def dump_tree_to_file(self, destination):
        self._xml_tree.write(destination)

    def parse_gem5_stats(self):
        with open(self._gem5_stats_path) as file:
            for line in file:
                line = line.strip()
                # Skip empty lines and header/footer
                if not line or line.startswith("---"):
                    continue

                # Split into parts, handling multiple spaces
                parts = [p for p in line.split(" ") if p]

                # Ensure we have at least 3 parts (name, value, comment)
                if len(parts) >= 2:
                    stat_name = parts[0]
                    stat_value = parts[1]
                    self._gem5_stats[stat_name] = stat_value

    def run_mcpat(self, mcpat_path, mcpat_output_filename):
        arguments = []
        self.dump_tree_to_file("temp.xml")
        arguments.append(f"{mcpat_path}/mcpat")
        arguments.append(f"-infile")
        arguments.append(f"{os.getcwd()}/temp.xml")
        arguments.append(f"-print_level")
        arguments.append(f"5")
        mcpat = subprocess.Popen(arguments, stdout=subprocess.PIPE, text=True)
        stdout, stderr = mcpat.communicate()
        mcpat.wait()
        with open(
            f"./mcpat-runs/{mcpat_output_filename}_mcpat_output.txt", "w"
        ) as f:
            f.write(stdout)
        return self.parse_with_regex(stdout)

    def parse_with_regex(self, text):
        pattern = r"""
            ^([ ]*)                     # Capture indentation
            ([^:=\n]+):                 # Component name
            (?:[^\n]*\n)*?              # Skip intermediate lines
            [ ]*Runtime\ Dynamic\ =\ ([0-9.e+-]+)\ W  # Capture runtime value
            """

        matches = re.finditer(pattern, text, re.MULTILINE | re.VERBOSE)

        components = []
        stack = []
        core_active = False  # Track when we're inside Core hierarchy

        for match in matches:
            indent = len(match.group(1))
            name = match.group(2).strip()
            value = match.group(3)

            if name == "Total L2s":
                components.append(("Processor > L2", value))

            # Clear stack if we exit Core hierarchy
            if (
                core_active and indent <= 2
            ):  # Core's indentation level (adjust based on actual indent)
                core_active = False
                stack = []

            # Maintain component hierarchy using indentation
            while stack and indent <= stack[-1][0]:
                stack.pop()

            # Track Core entry
            if name == "Core":
                core_active = True
                stack = [
                    (indent, "Processor"),
                    (indent, name),
                ]  # Start new hierarchy
            elif core_active:
                stack.append((indent, name))
            else:
                continue  # Skip non-Core components

            # Build full component path
            path = " > ".join([n for _, n in stack])
            components.append((path, value))

        return dict(components)

    def get_gem5_stat(self, stat_name):
        try:
            return float(
                self._gem5_stats.get(
                    stat_name, f"Statistic '{stat_name}' not found"
                )
            )
        except:
            if self._verbose:
                print(f"{stat_name} was not found! returning 0!")
            return 0

    def results_to_xml(self):
        if self._xml_tree == None:
            return None
        xml_root = self._xml_tree.getroot()
        root_str = "board.processor.cores.core."
        root_cache_str = "board.cache_hierarchy."
        idle_cycles = self.get_gem5_stat(root_str + "idleCycles")
        num_cycles = self.get_gem5_stat(root_str + "numCycles")
        for comp in xml_root.iter("component"):
            for param in comp.iter("param"):
                if comp.attrib["name"] == "core0":
                    if param.attrib["name"] == "machine_type":
                        if self._is_ooo:
                            param.attrib["value"] = "0"
                        else:
                            param.attrib["value"] = "1"
            for stat in comp.iter("stat"):
                if comp.attrib["name"] == "system":
                    if stat.attrib["name"] == "total_cycles":
                        stat.attrib["value"] = num_cycles
                    elif stat.attrib["name"] == "busy_cycles":
                        stat.attrib["value"] = num_cycles - idle_cycles
                    elif stat.attrib["name"] == "idle_cycles":
                        stat.attrib["value"] = idle_cycles
                elif comp.attrib["name"] == "core0":
                    if stat.attrib["name"] == "total_instructions":
                        stat.attrib["value"] = self.get_gem5_stat(
                            root_str + "fetchStats0.numInsts"
                        )
                    elif stat.attrib["name"] == "int_instructions":
                        stat.attrib["value"] = self.get_gem5_stat(
                            root_str + "commitStats0.numIntInsts"
                        )
                    elif stat.attrib["name"] == "fp_instructions":
                        stat.attrib["value"] = self.get_gem5_stat(
                            root_str + "commitStats0.numFpInsts"
                        )
                    elif stat.attrib["name"] == "branch_instructions":
                        stat.attrib["value"] = self.get_gem5_stat(
                            root_str + "branchPred.condPredicted"
                        )
                    elif stat.attrib["name"] == "branch_mispredictions":
                        stat.attrib["value"] = self.get_gem5_stat(
                            root_str + "branchPred.condIncorrect"
                        )
                    elif stat.attrib["name"] == "load_instructions":
                        stat.attrib["value"] = self.get_gem5_stat(
                            root_str + "commitStats0.numLoadInsts"
                        )
                    elif stat.attrib["name"] == "store_instructions":
                        stat.attrib["value"] = self.get_gem5_stat(
                            root_str + "commitStats0.numStoreInsts"
                        )
                    if stat.attrib["name"] == "committed_instructions":
                        stat.attrib["value"] = self.get_gem5_stat(
                            root_str + "commitStats0.numOps"
                        )
                    elif stat.attrib["name"] == "committed_int_instructions":
                        stat.attrib["value"] = self.get_gem5_stat(
                            root_str + "commitStats0.numIntInsts"
                        )
                    elif stat.attrib["name"] == "committed_fp_instructions":
                        stat.attrib["value"] = self.get_gem5_stat(
                            root_str + "commitStats0.numFpInsts"
                        )
                    elif stat.attrib["name"] == "int_regfile_reads":
                        stat.attrib["value"] = self.get_gem5_stat(
                            root_str + "executeStats0.numIntRegReads"
                        )
                    elif stat.attrib["name"] == "float_regfile_reads":
                        stat.attrib["value"] = self.get_gem5_stat(
                            root_str + "executeStats0.numFpRegReads"
                        )
                    elif stat.attrib["name"] == "int_regfile_writes":
                        stat.attrib["value"] = self.get_gem5_stat(
                            root_str + "executeStats0.numIntRegWrites"
                        )
                    elif stat.attrib["name"] == "float_regfile_writes":
                        stat.attrib["value"] = self.get_gem5_stat(
                            root_str + "executeStats0.numFpRegWrites"
                        )
                    elif stat.attrib["name"] == "function_calls":
                        stat.attrib["value"] = self.get_gem5_stat(
                            root_str + "commitStats0.functionCalls"
                        )
                    elif stat.attrib["name"] == "ialu_accesses":
                        stat.attrib["value"] = self.get_gem5_stat(
                            root_str + "issuedInstType_0::IntAlu"
                        )
                    elif stat.attrib["name"] == "fpu_accesses":
                        stat.attrib["value"] = self.get_gem5_stat(
                            root_str + "issuedInstType_0::FloatAdd"
                        )
                        stat.attrib["value"] += self.get_gem5_stat(
                            root_str + "issuedInstType_0::FloatMult"
                        )
                        stat.attrib["value"] += self.get_gem5_stat(
                            root_str + "issuedInstType_0::FloatMultAcc"
                        )
                        stat.attrib["value"] += self.get_gem5_stat(
                            root_str + "issuedInstType_0::FloatDiv"
                        )
                        stat.attrib["value"] += self.get_gem5_stat(
                            root_str + "issuedInstType_0::FloatMisc"
                        )
                    elif stat.attrib["name"] == "mul_accesses":
                        stat.attrib["value"] = self.get_gem5_stat(
                            root_str + "issuedInstType_0::IntDiv"
                        )
                        stat.attrib["value"] += self.get_gem5_stat(
                            root_str + "issuedInstType_0::IntMult"
                        )
                    elif stat.attrib["name"] == "cdb_alu_accesses":
                        stat.attrib["value"] = self.get_gem5_stat(
                            root_str + "issuedInstType_0::IntAlu"
                        )
                    elif stat.attrib["name"] == "cdb_fpu_accesses":
                        stat.attrib["value"] = self.get_gem5_stat(
                            root_str + "issuedInstType_0::FloatAdd"
                        )
                        stat.attrib["value"] += self.get_gem5_stat(
                            root_str + "issuedInstType_0::FloatMult"
                        )
                        stat.attrib["value"] += self.get_gem5_stat(
                            root_str + "issuedInstType_0::FloatMultAcc"
                        )
                        stat.attrib["value"] += self.get_gem5_stat(
                            root_str + "issuedInstType_0::FloatDiv"
                        )
                        stat.attrib["value"] += self.get_gem5_stat(
                            root_str + "issuedInstType_0::FloatMisc"
                        )
                    elif stat.attrib["name"] == "cdb_mul_accesses":
                        stat.attrib["value"] = self.get_gem5_stat(
                            root_str + "issuedInstType_0::IntDiv"
                        )
                        stat.attrib["value"] += self.get_gem5_stat(
                            root_str + "issuedInstType_0::IntMult"
                        )
                    elif stat.attrib["name"] == "rename_reads":
                        stat.attrib["value"] = self.get_gem5_stat(
                            root_str + "rename.intLookups"
                        )
                    elif stat.attrib["name"] == "rename_writes":
                        stat.attrib["value"] = self.get_gem5_stat(
                            root_str + "rename.intReturned"
                        )
                        """
                          try:
                            stat.attrib['value'] = "0" if not self._is_ooo else int(
                               (self.get_gem5_stat(root_str + "rename.intLookups") / self.get_gem5_stat(root_str + "rename.lookups")) * self.get_gem5_stat(root_str + "rename.renamedOperands"))
                          except:
                            stat.attrib['value'] = "0"
                          """
                    elif stat.attrib["name"] == "fp_rename_reads":
                        stat.attrib["value"] = self.get_gem5_stat(
                            root_str + "rename.fpLookups"
                        )
                    elif stat.attrib["name"] == "fp_rename_writes":
                        stat.attrib["value"] = self.get_gem5_stat(
                            root_str + "rename.fpReturned"
                        )
                        """
                          try:
                            stat.attrib['value'] = "0" if not self._is_ooo else int(
                               (self.get_gem5_stat(root_str + "rename.fpLookups") / self.get_gem5_stat(root_str + "rename.lookups")) * self.get_gem5_stat(root_str + "rename.renamedOperands"))
                          except:
                            stat.attrib['value'] = "0"
                          """
                    elif stat.attrib["name"] == "inst_window_reads":
                        stat.attrib["value"] = self.get_gem5_stat(
                            root_str + "intInstQueueReads"
                        )
                    elif stat.attrib["name"] == "inst_window_writes":
                        stat.attrib["value"] = self.get_gem5_stat(
                            root_str + "intInstQueueWrites"
                        )
                    elif stat.attrib["name"] == "inst_window_wakeup_accesses":
                        stat.attrib["value"] = self.get_gem5_stat(
                            root_str + "intInstQueueWakeupAccesses"
                        )
                    elif stat.attrib["name"] == "fp_inst_window_reads":
                        stat.attrib["value"] = self.get_gem5_stat(
                            root_str + "fpInstQueueReads"
                        )
                    elif stat.attrib["name"] == "fp_inst_window_writes":
                        stat.attrib["value"] = self.get_gem5_stat(
                            root_str + "fpInstQueueWrites"
                        )
                    elif (
                        stat.attrib["name"] == "fp_inst_window_wakeup_accesses"
                    ):
                        stat.attrib["value"] = self.get_gem5_stat(
                            root_str + "fpInstQueueWakeupAccesses"
                        )
                elif comp.attrib["name"] == "BTB":
                    if stat.attrib["name"] == "read_accesses":
                        stat.attrib["value"] = self.get_gem5_stat(
                            root_str + "branchPred.BTBLookups"
                        )
                    elif stat.attrib["name"] == "write_accesses":
                        stat.attrib["value"] = self.get_gem5_stat(
                            root_str
                            + "commitStats0.committedControl::IsControl"
                        )
                elif comp.attrib["name"] == "dcache":
                    if stat.attrib["name"] == "read_accesses":
                        stat.attrib["value"] = self.get_gem5_stat(
                            root_cache_str
                            + "l1dcaches.ReadReq.accesses::total"
                        )
                    elif stat.attrib["name"] == "write_accesses":
                        stat.attrib["value"] = self.get_gem5_stat(
                            root_cache_str
                            + "l1dcaches.WriteReq.accesses::total"
                        )
                    elif stat.attrib["name"] == "read_misses":
                        stat.attrib["value"] = self.get_gem5_stat(
                            root_cache_str + "l1dcaches.ReadReq.misses::total"
                        )
                    elif stat.attrib["name"] == "write_misses":
                        stat.attrib["value"] = self.get_gem5_stat(
                            root_cache_str + "l1dcaches.WriteReq.misses::total"
                        )
                    stat.attrib["value"] = int(stat.attrib["value"])
                elif comp.attrib["name"] == "icache":
                    if stat.attrib["name"] == "read_accesses":
                        stat.attrib["value"] = self.get_gem5_stat(
                            root_cache_str
                            + "l1icaches.ReadReq.accesses::total"
                        )
                    elif stat.attrib["name"] == "read_misses":
                        stat.attrib["value"] = self.get_gem5_stat(
                            root_cache_str + "l1icaches.ReadReq.misses::total"
                        )
                    stat.attrib["value"] = int(stat.attrib["value"])
                elif comp.attrib["name"] == "L20":
                    if stat.attrib["name"] == "read_accesses":
                        stat.attrib["value"] = self.get_gem5_stat(
                            root_cache_str
                            + "l2cache.ReadExReq.accesses::total"
                        )
                    elif stat.attrib["name"] == "write_accesses":
                        stat.attrib["value"] = self.get_gem5_stat(
                            root_cache_str + "l2cache.overallAccesses::total"
                        ) + self.get_gem5_stat(
                            root_cache_str
                            + "l2cache.WritebackClean.accesses::total"
                        )
                    elif stat.attrib["name"] == "read_misses":
                        stat.attrib["value"] = self.get_gem5_stat(
                            root_cache_str + "l2cache.ReadExReq.misses::total"
                        )
                    elif stat.attrib["name"] == "write_misses":
                        stat.attrib["value"] = self.get_gem5_stat(
                            root_cache_str + "l2cache.overallMisses::total"
                        ) - self.get_gem5_stat(
                            root_cache_str + "l2cache.ReadExReq.misses::total"
                        )
                stat.attrib["value"] = str(stat.attrib["value"])


def results_to_csv(
    benchmark,
    cpu_name,
    true_results,
    estimated_results,
    verbose,
    csv_name=None,
):
    row_names = [
        f"gem5_{cpu_name}_{benchmark}",
        f"mcpat_{cpu_name}_{benchmark}",
    ]
    if csv_name is None:
        csv_name = f"{benchmark}_{cpu_name}_power_results.csv"

    if verbose:
        print(f"Outputting data into csv file: {csv_name}")
    df = pd.DataFrame.from_dict(
        dict(zip(row_names, [estimated_results, true_results])), orient="index"
    )
    print(df.head())
    df.to_csv(f"./mcpat-runs/power_results/{csv_name}")

    # See below for some code to graph this csv file into a fancy stacked chart...

    """
    hatches = ''.join(h*len(df) for h in ' xx///\\')
    ax = df.plot.bar(stacked=True, edgecolor='black')
    bars = ax.patches

    for bar, hatch in zip(bars, hatches):
        bar.set_hatch(hatch)
    ax.legend()

    plt.show()
    """


def results_to_dict(m, results):
    components = ["Core", "L1D$", "L1I$", "L2$"]
    r = lambda n: float(n)

    gem5_core_power = r(
        m.get_gem5_stat("board.processor.cores.core.power_model.dynamicPower")
    )
    gem5_l1d_power = r(
        m.get_gem5_stat(
            "board.cache_hierarchy.l1dcaches.power_model.dynamicPower"
        )
    )
    gem5_l1i_power = r(
        m.get_gem5_stat(
            "board.cache_hierarchy.l1icaches.power_model.dynamicPower"
        )
    )
    gem5_l2_power = r(
        m.get_gem5_stat(
            "board.cache_hierarchy.l2cache.power_model.dynamicPower"
        )
    )

    mcpat_core_power = r(results["Processor > Core"])
    mcpat_l1i_power = r(
        results[
            "Processor > Core > Instruction Fetch Unit > Instruction Cache"
        ]
    )
    mcpat_l1d_power = r(
        results["Processor > Core > Load Store Unit > Data Cache"]
    )
    mcpat_l2_power = r(results["Processor > L2"])

    mcpat_core_power -= mcpat_l1i_power + mcpat_l1d_power

    mcpat_results = dict(
        zip(
            components,
            [
                mcpat_core_power,
                mcpat_l1i_power,
                mcpat_l1d_power,
                mcpat_l2_power,
            ],
        )
    )
    gem5_results = dict(
        zip(
            components,
            [gem5_core_power, gem5_l1i_power, gem5_l1d_power, gem5_l2_power],
        )
    )
    return mcpat_results, gem5_results


def main(args):
    is_ooo = True if args.cpu_type == "out-of-order" else False
    if args.verbose:
        print(f"Processor is {args.cpu_type}")

    m = McPATValidator(
        "../mcpat/ARM_A9_2GHz_gem5.xml", args.m5_stats, is_ooo, args.verbose
    )
    mcpat_output_filename = f"{args.cpu_name}-{args.benchmark_name}"
    results = m.run_mcpat(args.mcpat_path, mcpat_output_filename)

    for component, power in results.items():
        if args.verbose:
            print(f"{component}: {power} W")

    """
   NOTE: For these results, I'm considering McPAT to be the "ground truth"
         and gem5 to be the "estimated power"
   """

    true, estimated = results_to_dict(m, results)
    results_to_csv(
        args.benchmark_name, args.cpu_name, true, estimated, args.verbose
    )

    if args.verbose:
        print(
            f"For {args.m5_stats}, core power is estimated to be {estimated['Core']} W"
        )
        print(f"\t L1D$ Power is estimated to be {estimated['L1D$']} W")
        print(f"\t L1I$ Power is estimated to be {estimated['L1I$']} W")
        print(f"\t L1I$ Power is estimated to be {estimated['L2$']} W")

    total_gem5 = sum(estimated.values())
    total_mcpat = sum(true.values())

    print(f"Total gem5 power: {total_gem5}")
    print(f"Total mcpat power: {total_mcpat}")
    print(
        f"Total Error: {abs(total_mcpat - total_gem5) / (total_mcpat) * 100}%"
    )


def parse_cli_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--cpu_type",
        type=str,
        choices=["in-order", "out-of-order"],
        default="in-order",
        help="The CPU type your processor is",
    )

    parser.add_argument(
        "--m5_stats",
        type=str,
        default="./m5out/stats.txt",
        help="Path to gem5 stats file (assumes ./m5out/stats.txt if not specified)",
    )

    parser.add_argument(
        "--mcpat_path",
        type=str,
        default="../mcpat",
        help="Path to directory holding the McPAT executable",
    )

    parser.add_argument("--verbose", "-v", action="store_true")

    parser.add_argument(
        "--cpu_name",
        type=str,
        default="gem5cpu",
        help="Name of the CPU that was simulated in gem5 (used for CSV generation)",
    )

    parser.add_argument(
        "--benchmark_name",
        type=str,
        default="bmrk",
        help="Name of the benchmark that was simulated in gem5 (used for CSV generation)",
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_cli_args()
    main(args)
