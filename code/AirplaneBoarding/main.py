from simulation import Simulation
from plane import Plane

p = Plane(3,3,30,0.8,0.5,3,2)
sim = Simulation(175,p,1)
#try:

sim.simulate()
#except ValueError:

    #print(sim.plane.aisle.occupance)
    #print(sim.simulation)
print(len(sim.simulation))