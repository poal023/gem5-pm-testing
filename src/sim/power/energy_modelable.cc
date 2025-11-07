#include "sim/power/energy_modelable.hh"

#include "sim/clock_domain.hh"

namespace gem5
{
EnergyModelable::EnergyModelable(const Params &p)
    : SimObject(p), powerState(p.power_state), clk_domain(*p.clk_domain)
{
    for (auto &pm : p.power_model) {
         pm->setModelableObject(this);
    }
}
void
EnergyModelable::serialize(CheckpointOut &cp) const
{
    powerState->serialize(cp);
}
void
EnergyModelable::unserialize(CheckpointIn &cp)
{
    powerState->unserialize(cp);
}
} // namespace gem5
