# McPAT Power Model

This is folder holds all the files to make a power model (PM), in Python, for a Minor ARM CPU. The power model made by these files tries to capture the behavior of an ARM A9 running @ 2GHz.

**WARNING: These files may be modified and changed via pushes, please pull often!**

## Usage

Firstly, make sure you compile gem5 for any architecture to run this PM, via:
`scons -j`nproc` build/ARM/gem5.opt`

Once this is done, if you wish to just run the current power model you should be able to use a simple script from the base gem5/ directory:
`./run-power-modeling.sh`, which just runs the python script at `configs/example/gem5_library/arm-a9-power-modeling.py`.

The actual SimObj that takes in the return result of a Python function is `PowerModelFunc`, which expects the return value of `dynamic_power` and `static_power` to be fed into `self.dyn` and `self.st`. Please see `configs/example/gem5_library/minor_mcpat_cpu_power_model/minor_mcpat_cpu_power_model.py` for an example.

## Modfying PMs and PM SimObjects
The actual PowerModelFunc SimObject is located in `src/learning_gem5/part2/power_model_func.{cc/hh}`, while the SimObj Python file is in the same directory but just `PowerModelFunc.py`.
