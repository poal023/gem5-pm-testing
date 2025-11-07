#ifndef __SIM_POWER_ENERGY_MODELABLE_HH
#define __SIM_POWER_ENERGY_MODELABLE_HH
#include "params/EnergyModelable.hh"
#include "sim/clock_domain.hh"
#include "sim/power/power_model.hh"
#include "sim/power_state.hh"
#include "sim/sim_object.hh"

namespace gem5
{
class EnergyModelable : public SimObject
{
  public:
     PARAMS(EnergyModelable);
     EnergyModelable(const Params &p);
     PowerState *powerState;
     double voltage() const {return clk_domain.voltage();}
     Tick clockPeriod() const { return clk_domain.clockPeriod(); }
     void serialize(CheckpointOut &cp) const override;
     void unserialize(CheckpointIn &cp) override;

   private:
     ClockDomain &clk_domain;
};

}

#endif
