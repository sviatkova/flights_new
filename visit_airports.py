from datetime import datetime, time, timedelta
from json import dumps
from typing import Dict, List, Optional, Set

from helper_functions import FLIGHT_INFORMATION, end_searching
from process_airports import Flight, FlightCombinations


class Graph:
    def __init__(self, **customer_requirements) -> None:
        """
        Imports nodes from a csv file and creates an adjacency list
        of possible flights (the ones in compliance with the customer
        requirements).

        Graph structure:
        {
            "origin airport1": {
                "destination airport 1 (paris)": {
                    date (YYYYMMDD): [0, 1, 4],
                    20221025: [2]
                },
                "bordeaux": {
                    20221023: [3, 5]
                }
            }
        }

        In our graph, we only store indices of fligths.
        """
        # stores relationships between nodes - flights
        self.graph: Dict[str, Dict[str, Dict[int, List[int]]]] = dict()

        # stores nodes - flights in the same order they are in
        # the .csv file we will then access them through indices
        self.flights: List[Flight] = []

        # keeps track of how many flights were put into our graph
        self.flights_counter = 0

        # gather information about the customer's requirements -->
        # to use them when creating the output and checking
        # for possible flights
        self.bags = customer_requirements["bags"]
        self.destination = customer_requirements["destination"]
        self.origin = customer_requirements["origin"]

        # soonest arrivals
        self.arrival: Optional[datetime] = customer_requirements["arrival"]
        self.return_arrival: Optional[datetime] = \
            customer_requirements["returnarrival"]

        csv_filename = customer_requirements["dataset"]
        with open(csv_filename, "r") as file:
            flights_file = file.readlines()

        # use header row to get categories / csv columns in their
        # original order - specific for the current dataset
        flight_categories = flights_file[0].strip().split(",")

        # checks if the dataset is valid - according to the assignment
        # it is okay if:
        #   - the columns do not have the same order in
        #       different datasets
        #   - there are more columns than the ones we need
        if self.__less_categories(flight_categories):
            end_searching("Some columns is the dataset are missing.")

        # add nodes - flights, skip the header row
        self.__add_nodes(flights_file[1:], flight_categories, customer_requirements)

        # class instance to keep track of all possible flights
        # for this search
        self.flight_combinations = FlightCombinations(self.destination,
                                                      self.origin,
                                                      self.bags,
                                                      self.flights,
                                                      flight_categories)

    def __add_nodes(self,
                    file_lines_flights: List[str],
                    flight_categories: List[str],
                    customer_requirements: Dict) -> None:
        for line in file_lines_flights:
            new_flight = Flight(line, flight_categories)

            # check if this flight meets all the requirements
            # from input - if not, we will not add it to the graph
            if customer_requirements["bags"] \
                    <= new_flight.flight_data["bags_allowed"]:
                # default number of bags is 0

                flight_departure: datetime = \
                    new_flight.flight_data["departure"]
                customer_departure: Optional[datetime] = \
                    customer_requirements["departure"]

                # we can add a flight to our graph only if the customer
                # hasnt specified the soonest departure date or a
                # flight departure is after the desired departure date
                if customer_departure is None \
                        or flight_departure > customer_departure:
                        self.__add_flight(new_flight)

    def __less_categories(self, flight_categories: List[str]) -> bool:
        """
        Determines if the given .csv file has the all the columns as
        is specified in the assignment - checks if our .csv is valid
        """
        return len(set(flight_categories)) < len(set(FLIGHT_INFORMATION))


    def __add_airport(self, airport_code: str) -> None:
        """
        Adds a vertex to the graph of airports.
        """
        self.graph[airport_code] = dict()

    def __add_flight(self, flight_information: Flight) -> None:
        """
        Adds an edge to the graph between the origin
        and destination airport.
        """
        origin_airport = flight_information.flight_data["origin"]
        destination_airport = flight_information.flight_data["destination"]

        departure_date = \
            self.__datetime_to_int(flight_information.flight_data["departure"])

        if destination_airport not in self.graph:
            self.__add_airport(destination_airport)

        if origin_airport not in self.graph:
            self.__add_airport(origin_airport)

        if destination_airport not in self.graph[origin_airport]:
            self.graph[origin_airport][destination_airport] = dict()

        if departure_date not in \
                self.graph[origin_airport][destination_airport]:
            self.graph[origin_airport][destination_airport][departure_date] = []
            self.graph[origin_airport][destination_airport][departure_date].\
                append(self.flights_counter)

        self.flights.append(flight_information)
        self.flights_counter += 1

    def visit_all_vertices(self, origin: str, destination: str):
        """
        All paths from <origin> to <destination>
        """
        # stores indices of flights on given path
        path_indices = []

        # how it searches the flights:
        # from the city we are in right now, we have to look how to get
        # to other cities but we have to look for flights that comply
        # with the arrival date of the current flight

        # first we look for all the flights that originate
        # in customer's city of origin = here we only find
        # the first flight

        if origin in self.graph:
            for dest_city in self.graph[origin]:
                for departure_date in self.graph[origin][dest_city]:
                    for flight_index in \
                            self.graph[origin][dest_city][departure_date]:

                        # keeps track of vertices in current path
                        visited_cities: Set[str] = set()
                        visited_cities.add(origin)

                        self.__visit_all_vertices_util(destination,
                                                       visited_cities,
                                                       path_indices,
                                                       flight_index)

    def print_found_combinations(self) -> None:
        sorted_list = sorted(self.flight_combinations.combinations,
                             key=lambda x: x["total_price"])
        print(dumps(sorted_list, indent=4))

    def __seconds_to_midnight(self, current_time: datetime) -> int:
        midnight = datetime.combine(current_time + timedelta(days=1), time())
        return (midnight - current_time).seconds

    def __next_day(self, date: datetime) -> datetime:
        return date + timedelta(days=1)

    def __datetime_to_int(self, time: datetime) -> int:
        return int(time.strftime("%Y%m%d"))
    
    def __in_final_destination(self,
                               final_destination: str,
                               arrival_time: datetime,
                               path: List[int]) -> None:

        if final_destination == self.destination:
            # journey A -> B
            if self.arrival is None or arrival_time > self.arrival:
                self.flight_combinations.add_path(path, False)

        elif final_destination == self.origin:
            # return journey B -> A
            if self.return_arrival is None or arrival_time \
                        > self.return_arrival:
                self.flight_combinations.add_path(path, True)

    def __add_next_day(self,
                       arrival_time: datetime,
                       flight_destination: str,
                       new_destination: str,
                       next_flights: List[int]) -> List[int]:

        next_day = self.__next_day(arrival_time)

        # in our graph, dates of the departures
        # are stored as int
        next_day_int = self.__datetime_to_int(next_day)

        if next_day_int in self.graph[flight_destination][new_destination]:
            next_flights += self.graph[flight_destination][new_destination][next_day_int]

        return next_flights

    def __visit_all_vertices_util(self,
                                  final_destination: str,
                                  visited: Set[str],
                                  path: List[int],
                                  flight_index: int):
        """
        Recursive helper function that visits vertices in the graph.

        <path> stores indices of flights on path
        """
        current_flight: Flight = self.flights[flight_index]

        # get information about current flight
        flight_destination: str = current_flight.flight_data["destination"]
        arrival_time: datetime = current_flight.flight_data["arrival"]
        arrival_date = self.__datetime_to_int(arrival_time)

        visited.add(flight_destination)
        path.append(flight_index)

        if flight_destination == final_destination:

            # we already checked that self.destination != self.origin
            # we compare <arrival_time> to the soonest arrivals
            # the customer has specified

            self.__in_final_destination(flight_destination,
                                        arrival_time,
                                        path)

        else:
            # we need to look for flights from destination of
            # our current flight to other cities
            for new_destination in self.graph[flight_destination]:
                if new_destination not in visited:

                    # are there any flights from this city this day?
                    if arrival_date in \
                            self.graph[flight_destination][new_destination]:
                        next_flights = \
                            self.graph[flight_destination][new_destination][arrival_date]
                    else:
                        next_flights = []

                    # if there is less than 6 hours to midnight, we also need
                    # to check for the flights the next day (as the layover
                    # can be up to 6 hours)
                    # 1 hour = 60 min * 60 seconds
                    if self.__seconds_to_midnight(arrival_time) <= 6 * 3600:
                        next_flights = self.__add_next_day(arrival_time,
                                                           flight_destination,
                                                           new_destination,
                                                           next_flights)

                    for fl_index in next_flights:
                        possible_flight = self.flights[fl_index].flight_data
                        possible_departure: datetime = possible_flight["departure"]

                        layover_time: timedelta = \
                            possible_departure - arrival_time
                        layover_time_sec = layover_time.total_seconds()

                        # we want the layover to be more than 1 hour
                        # and less than 6 hours
                        if 3600 < layover_time_sec < 6 * 3600:
                            self.__visit_all_vertices_util(final_destination,
                                                           visited,
                                                           path,
                                                           fl_index)

        path.pop()
        visited.remove(flight_destination)

