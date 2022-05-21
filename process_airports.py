from collections import OrderedDict
from datetime import datetime, timedelta
from typing import Dict, List, Union

from helper_functions import *


class Flight:
    """Stores information about a flight"""
    def __init__(self,
                 flight_line: str,
                 flight_categories: List[str]) -> None:
        """Accepts one line of a csv file and parses it"""
        self.flight_data: Dict[str, Union[str, int, float, datetime]]
        self.flight_data = dict()

        split_flight_line = flight_line.split(",")

        if len(split_flight_line) != len(FLIGHT_INFORMATION):
            # when the lines of data in the dataset
            # dont match the length of the header line
            end_searching(".csv dataset contains invalid lines")

        for index, value in enumerate(flight_line.split(",")):
            category = flight_categories[index]

            if category in ("departure", "arrival"):
                self.flight_data[category] = str_to_datetime(value)
            elif category in ("base_price", "bag_price"):
                self.flight_data[category] = float(value)
            elif category == "bags_allowed":
                self.flight_data[category] = int(value)
            elif category in ("origin", "destination"):
                if valid_airport_code(value):
                    self.flight_data[category] = value
                else:
                    end_searching("csv file contains invalid airport codes")
            else:
                # remaining value leave as string - flight number
                self.flight_data[category] = value


class FlightCombinations:
    def __init__(self,
                 destination: str,
                 origin: str,
                 bags: int,
                 flights: List[Flight],
                 flight_categories: List[str]) -> None:

        self.combinations: \
            List[OrderedDict[str, Union[List[OrderedDict], str, int, float]]]
        self.combinations = []

        self.bags = bags
        self.destination = destination
        self.origin = origin
        self.flights = flights
        self.flight_categories = flight_categories

    def add_path(self, path: List[int], is_return: bool) -> None:
        """
        Adds formatted path (flights combination) to the result.

        :param path: list of flight indices sorted
                     chronologically - how one travels
        """
        self.combinations.append(self.__format_path(path, is_return))

    def __convert_timedelta(self, time: timedelta) -> str:
        total_sec = int(time.total_seconds())
        hrs = total_sec // 3600
        min = (total_sec // 60) % 60
        sec = total_sec - hrs * 3600 - min * 60
        return f"{hrs}:{min:02d}:{sec:02d}"

    def __total_travel_time(self, flights_indices: List[int]) -> str:
        # <flights> are ordered by time chronologically

        # gets flight on the same index as the first flight of our trip
        first_flight = self.flights[flights_indices[0]]

        # gets flight on the same index as the last flight of our trip
        last_flight = self.flights[flights_indices[-1]]

        first_departure = first_flight.flight_data["departure"]
        last_arrival = last_flight.flight_data["arrival"]

        total_time = last_arrival - first_departure
        return self.__convert_timedelta(total_time)

    def __format_path(self,
                        flights_indices: List[int],
                        is_return: bool) -> OrderedDict:
        """
        Merges <flights> into one dict with the same structure
        as the sample output.
        """
        total_price = 0.0
        allowed_bags = 100

        # get information about the journey
        for flight_index in flights_indices:
            flight = self.flights[flight_index]

            # gets total flight price
            total_price += flight.flight_data["base_price"]

            # we know that the number of bags <= bags_allowed
            total_price += flight.flight_data["bag_price"] * self.bags

            # gets number of allowed bags
            current_bags = flight.flight_data["bags_allowed"]
            allowed_bags = min(allowed_bags, current_bags)

        # get flight time
        total_time = self.__total_travel_time(flights_indices)

        # put acquired information into the correct format,
        # preserving their order
        new_flight = OrderedDict()

        new_flight["flights"] = []

        for flight_index in flights_indices:
            flight = self.flights[flight_index].flight_data

            # flights are stored as list of ordered_dict
            new_flight["flights"].append(self.__get_ordered_dict(flight))

        new_flight["bags_allowed"] = allowed_bags
        new_flight["bags_count"] = self.bags

        # if the flight is return, swap origin and destination airports
        if is_return:
            new_flight["destination"] = self.origin
            new_flight["origin"] = self.destination
        else:
            new_flight["destination"] = self.destination
            new_flight["origin"] = self.origin

        new_flight["total_price"] = total_price
        new_flight["travel_time"] = total_time

        return new_flight

    def __datetime_to_str(self, time: datetime) -> str:
        return time.strftime("%Y-%m-%dT%H:%M:%S")

    def __get_ordered_dict(self, flight_data: Dict) -> OrderedDict:
        """
        Converts a dictionary to OrderedDict using the order of flight
        categories as the sample output requires
        """
        flight = OrderedDict()

        # categories in FLIGHT_INFORMATION are sorted in the same way
        # we want the output to be
        for category in FLIGHT_INFORMATION:
            if category in ("departure", "arrival"):
                datetime_time = flight_data[category]
                flight[category] = self.__datetime_to_str(datetime_time)
            else:
                flight[category] = flight_data[category]

        return flight
