#ifndef __SIM_POWERMODEL_FUNC_PM_HH__
#define __SIM_POWERMODEL_FUNC_PM_HH__

#include "params/PowerModelPyFunc.hh"
#include "python/pybind11/pybind.hh"
#include "sim/power/power_model.hh"
#include "sim/sim_object.hh"

namespace gem5
{

class PowerModelPyFunc : public PowerModelState
{
   private:
     pybind11::object dyn;
     pybind11::object st;
     const Cycles pwr_interval;
     std::string clock_stat;
     pybind11::function st_func;
     pybind11::function dyn_func;
     Tick prev_tick = 0;
     bool begin_sampling = false;

     EventFunctionWrapper intervalEvent;
     void powerAtInterval();

   public:
     PARAMS(PowerModelPyFunc);
     PowerModelPyFunc(const Params &p);
     double getDynamicPower() const override {
             pybind11::object result_py = dyn_func();
             return result_py.cast<double>();
     }
     double getStaticPower() const override {
             pybind11::object result_py = st_func();
             return result_py.cast<double>();
     }
     void startSampling();
     void stopSampling();
};

} // namespace gem5

#endif
