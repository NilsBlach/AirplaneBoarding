from aisle import Aisle
import math
from compartment import Compartment
from simulation import Simulation
import numpy as np

class Plane:

    def __init__(self, seats_left, seats_right, rows, length_of_row, row_entry_size, compartment_size, compartment_length):

        row_entry_size = Simulation.meter_to_space_unit(row_entry_size)
        length_of_row = Simulation.meter_to_space_unit(length_of_row)
        compartment_length = Simulation.meter_to_space_unit(compartment_length)
        self.seatsLeft = seats_left
        self.seatsRight = seats_right
        self.seat_occupance = np.full((rows, seats_left + seats_right), 0, dtype=int)
        self.rows = rows
        self.length = rows * length_of_row
        self.aisle = Aisle(self, length_of_row, row_entry_size)
        self.compartments = []
        self.compartment_length = compartment_length
        self.actors = None
        self.length_of_row = length_of_row

        # initialize compartments
        self.nr_compartments = int(self.length/compartment_length)
        for i in range(0, self.nr_compartments):
            self.compartments.append(Compartment(compartment_size*2, i*compartment_length, (i+1)*compartment_length))

    def get_start_of_row(self, row_number):
        return row_number * self.length_of_row

    def get_compartment_at_pos(self, position):
        return self.compartments[math.floor(position/self.compartment_length)]
