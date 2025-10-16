#include "sim/power/power_model_pyfunc.hh"

#include "base/flags.hh"
#include "base/statistics.hh"
#include "base/trace.hh"
#include "debug/PwrIntervalEvent.hh"
#include "sim/clocked_object.hh"

namespace gem5
{

PowerModelPyFunc::PowerModelPyFunc(const Params &p)
           :  PowerModelState(p), dyn(p.dyn), st(p.st),
           pwr_interval(p.pwr_interval), clock_stat(p.clock_stat),
           intervalEvent([this]{powerAtInterval();}, name(), false,
                   Event::Priority(60))
        {
           // Bind PyFunc parameters into functions to be called in this SimObj

           dyn_func =
                   pybind11::reinterpret_borrow<pybind11::function>(dyn);
           st_func =
                   pybind11::reinterpret_borrow<pybind11::function>(st);
        }
void
PowerModelPyFunc::startup()
{
    DPRINTF(PwrIntervalEvent, "Name of SO: %s\n", clocked_object->name());
    if (pwr_interval > 0) {
        schedule(intervalEvent, curTick() + pwr_interval);
    }

}

void
PowerModelPyFunc::powerAtInterval()
{
    auto prev_stat = 0;
    if (pwr_interval > 0) {
        auto *stat_info = clocked_object->resolveStat(clock_stat);
        auto stat = dynamic_cast<const statistics::ScalarInfo *>(stat_info);
        DPRINTF(PwrIntervalEvent, "SO (%s) is non-zero with %llu\n",
                clocked_object->name(), stat->value());
        if (stat->value() != 0) {
            prev_stat = stat->value();
            begin_sampling = true;
            getDynamicPower();
            getStaticPower();
        }
        if (begin_sampling && prev_stat == stat->value()){
            deschedule(intervalEvent);
        } else {
            schedule(intervalEvent, curTick() + pwr_interval);
        }
    }

}


} // namespace gem5
