import numpy as np
import random
from passenger_type import Passenger_Type
from actor import Actor
from seat_assignments import Assignments


PASSENGER_SIZE = 0.25
PASSENGER_PERSONAL_SPACE = PASSENGER_SIZE + 0.21

UNIT_LENGTH = 0.001  # meter
UNIT_TIME = 0.1  # seconds

SEAT_PITCH_2002 = 0.813  # m
passing_one_row_seconds = [1.8, 2.4, 3.0]
MAXIMUM_MOVING_SPEED = SEAT_PITCH_2002/passing_one_row_seconds[0]  # m/s
MINIMUM_MOVING_SPEED = SEAT_PITCH_2002/passing_one_row_seconds[2]  # m/s
MODE_MOVING_SPEED = SEAT_PITCH_2002/passing_one_row_seconds[1]  # m/s

MAXIMUM_EXIT_ROW_TIME = 15  # s
MINIMUM_EXIT_ROW_TIME = 5  # s
MODE_EXIT_ROW_TIME = 7.5

MAXIMUM_ROW_ENTER_TIME = MAXIMUM_EXIT_ROW_TIME  # s
MINIMUM_ROW_ENTER_TIME = MINIMUM_EXIT_ROW_TIME  # s
MODE_ROW_ENTER_TIME = MODE_EXIT_ROW_TIME


MAXIMUM_STORE_TIME = 17  # s
MINIMUM_STORE_TIME = 3  # s
MODE_STORING_TIME = 9



class Simulation:

    def __init__(self, number_of_actors, plane, luggage_distribution_index, seat_assignment_id, first_seat_assignment_input, second_seat_assignment_input, third_seat_assignment_input, random_seat_deletion):



        self.seat_assignment = Assignments.generate_seat_assignment(seat_assignment_id, plane,
                                                                    first_seat_assignment_input,
                                                                    second_seat_assignment_input,
                                                                    third_seat_assignment_input)
        if random_seat_deletion:
            adapted_seat_assignment = list(self.seat_assignment)
            for i in range(0, len(self.seat_assignment) - number_of_actors):
                index = random.randint(0, len(self.seat_assignment)-i-1)
                del adapted_seat_assignment[index]
            self.seat_assignment = adapted_seat_assignment
        self.actors = []

        self.plane = plane
        self.number_of_actors = number_of_actors
        # can either be the index for the old version for the ditribution or a percentage, indicating how full the compartements are
        self.luggage_distribution_index = luggage_distribution_index

        # fill actors[] with random actors
        luggage_distribution = self.get_luggage_distribution_given_capacity()
        for i in range(1, self.number_of_actors+1):
            actor = Actor(i, self.get_random_passenger(luggage_distribution[i-1]), self.seat_assignment[i-1], 0, plane)
            self.actors.append(actor)
        self.plane.actors = self.actors
        # simulation[] will contain all states observed during simulation (in order)
        self.simulation = list()
        self.actor_boarding_times = np.zeros(self.number_of_actors, dtype=int)

    """
    Passenger moving speed data is given in from of a triangular distribution (it was recoded for Short Haul airplanes):
        passing_one_row_seconds = [1.8, 2.4, 3.0] seconds per row - average row size around 2002 was 0.813m
        install_in_seat_seconds = [6.0, 9.0, 30.0] seconds
        exit_from_seat_into_aisle = [3.0, 3.6, 4.2] seconds
    Passenger luggage load is chosen by us, so we can have different set ups. 
    In the paper they had two options normal and high load. 
    """
    def get_luggage_distribution_given_capacity(self):
        total_number_of_pieces = int((self.luggage_distribution_index/100) * self.plane.nr_compartments * self.plane.compartment_size * 2)
        #print(total_number_of_pieces)
        luggage_distribution = np.zeros(self.number_of_actors, dtype=int)
        if total_number_of_pieces > self.number_of_actors*2 or self.luggage_distribution_index > 100 or self.luggage_distribution_index < 0:
            raise ValueError('ERROR: Either you have not enough passengers to fill the compartments of the plane '
                             'to 100 percent occupance, or the percentage you have given is not within 0 to 100')
        for i in range (0, total_number_of_pieces):
            while True:
                j = np.random.randint(0, self.number_of_actors)
                if luggage_distribution[j] < 2:
                    luggage_distribution[j] += 1
                    break
        return luggage_distribution


    # This method is in early retirement, but might have to come back
    def get_luggage_distribution(self):
        load_distribution = [[0.35, 0.6, 0.5], [0.2, 0.6, 0.2]]
        total_number_of_pieces = 0
        maximum_luggage_capacity = self.plane.nr_compartments * self.plane.compartment_size * 2
        luggage_distribution = np.zeros(self.number_of_actors, dtype=int)
        count = 0
        j = 0
        for i in range(0, self.number_of_actors):
            if j < len(load_distribution[self.luggage_distribution_index]):
                if count < int(load_distribution[self.luggage_distribution_index][j] * self.number_of_actors):
                    luggage_distribution[i] = j
                    count += 1
                    total_number_of_pieces += j
                elif count == int(load_distribution[self.luggage_distribution_index][j] * self.number_of_actors):
                    count = 0
                    j += 1
                    total_number_of_pieces += j
                    luggage_distribution[i] = j
            else:
                luggage_distribution[i] = 0

        if total_number_of_pieces > maximum_luggage_capacity:
            raise ValueError('ERROR: The luggage distribution, number of passengers and plane specifications '
                             'will result in more hand luggage than available space in the compartments. '
                             'This is not allowed. The total number of pieces amounts to: ', total_number_of_pieces,
                             ' and the available space is: ', maximum_luggage_capacity)
        np.random.shuffle(luggage_distribution)
        return luggage_distribution




    def get_random_passenger(self, number_of_bags):
        # test data
        moving_speed = [Simulation.m_per_s_to_speed_unit(np.random.triangular(MINIMUM_MOVING_SPEED, MODE_MOVING_SPEED, MAXIMUM_MOVING_SPEED)), Simulation.sec_to_time_unit(np.random.triangular(MINIMUM_ROW_ENTER_TIME, MODE_ROW_ENTER_TIME, MAXIMUM_ROW_ENTER_TIME)),
                        Simulation.sec_to_time_unit(np.random.triangular(MINIMUM_EXIT_ROW_TIME, MODE_EXIT_ROW_TIME, MAXIMUM_EXIT_ROW_TIME))]
        storing_time = Simulation.sec_to_time_unit(np.random.triangular(MINIMUM_STORE_TIME, MODE_STORING_TIME, MAXIMUM_STORE_TIME))
        return Passenger_Type(number_of_bags, moving_speed, storing_time,  Simulation.meter_to_space_unit(PASSENGER_SIZE), Simulation.meter_to_space_unit(PASSENGER_PERSONAL_SPACE), 3 * self.plane.length_of_row)

    def simulate(self):
        done = False
        i = 0
        next_actor_in = 0

        while not done:
            if i%1000 == 0:
                print('still going strong ', i)
            j = 0
            actors_seated = 0
            prev_actor = -1
            # loop backwards through aisle and store order of actors in list
            acting_order = list()
            for x in reversed(range(0, len(self.plane.aisle.occupance))):
                if self.plane.aisle.occupance[x] != prev_actor and self.plane.aisle.occupance[x] > 0:
                    acting_order.append(self.actors[self.plane.aisle.occupance[x]-1])
                    prev_actor = self.plane.aisle.occupance[x]
            # let the actors do their magic
            for a in acting_order:
                a.act()
            # try letting the next actor enter the plane
            if next_actor_in < len(self.actors) and self.actors[next_actor_in].act() != 1:
                next_actor_in += 1

            frame = (np.zeros((self.number_of_actors,4), dtype=int), np.zeros(self.plane.nr_compartments, dtype=int))
            for a in self.actors:
                frame[0][j, 0] = a.position
                frame[0][j, 1] = a.action
                frame[0][j, 2] = a.luggage
                frame[0][j, 3] = a.switching
                if a.action == 5:
                    actors_seated += 1
                j += 1
            n = 0
            for c in self.plane.compartments:
                frame[1][n] = c.free_space
                n += 1
            self.simulation.append(frame)
            i += 1
            if actors_seated == self.number_of_actors:
                done = True
                print('Boarding took: ', i/600, ' minutes')
                self.boarding_time_total = i/600

        for i in range(0, self.number_of_actors):
            self.actor_boarding_times[i] = round(self.actors[i].personal_boarding_duration * 0.1)

    @staticmethod
    def m_per_s_to_speed_unit(speed):
        return round(speed / (UNIT_LENGTH/UNIT_TIME))

    @staticmethod
    def sec_to_time_unit(seconds):
        return round(seconds / UNIT_TIME)

    @staticmethod
    def meter_to_space_unit(meters):
        return round(meters / UNIT_LENGTH)

