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
           intervalEvent([this]{powerAtInterval();}, name())
        {
           // Bind PyFunc parameters into functions to be called in this SimObj

           dyn_func =
                   pybind11::reinterpret_borrow<pybind11::function>(dyn);
           st_func =
                   pybind11::reinterpret_borrow<pybind11::function>(st);
        }

void
PowerModelPyFunc::startSampling()
{
    assert(pwr_interval > 0);
    begin_sampling = true;
    DPRINTF(PwrIntervalEvent, "Starting sampling of SO: %s\n",
            clocked_object->name());
    schedule(intervalEvent, curTick() + pwr_interval);

}

void
PowerModelPyFunc::stopSampling()
{
    assert(pwr_interval > 0 && begin_sampling);
    DPRINTF(PwrIntervalEvent, "Stopping sampling of SO: %s\n",
            clocked_object->name());
    deschedule(intervalEvent);
}

void
PowerModelPyFunc::powerAtInterval()
{
    assert(pwr_interval > 0 && begin_sampling);
    DPRINTF(PwrIntervalEvent, "In powerAtInterval... (tick: %llu)\n",
            curTick());
    auto *stat_info = clocked_object->resolveStat(clock_stat);
    if (stat_info) {
        auto stat = dynamic_cast<const statistics::ScalarInfo *>(stat_info);
        if (stat->value() != 0) {
            DPRINTF(PwrIntervalEvent, "Calling dyn/st power (tick %llu)\n",
                    curTick());
            DPRINTF(PwrIntervalEvent, "Stat is %d\n", stat->value());
            getDynamicPower();
            getStaticPower();
        }
    }
    schedule(intervalEvent, curTick() + pwr_interval);


}

} // namespace gem5
