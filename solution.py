import argparse
import os.path

from helper_functions import *
from visit_airports import Graph


def init_parser():
    parser = argparse.ArgumentParser()

    # positional arguments
    parser.add_argument("dataset",
                        type=str,
                        help="Path to a .csv dataset of available flights")
    parser.add_argument("origin",
                        type=str,
                        help="Origin airport code")
    parser.add_argument("destination",
                        type=str,
                        help="Destination airport code")

    # optional arguments
    parser.add_argument("--bags",
                        type=int,
                        default=0,
                        help="Number of requested bags (default=0)")

    parser.add_argument(
        "--return",
        action="store_true",
        help="Is it a return flight? (default=False)")

    parser.add_argument(
        "--arrival",
        type=str,
        default=None,
        help="Date and time of the soonest arrival to the destination "
             "airport in UTC format (default=None)")

    parser.add_argument(
        "--returnarrival",
        type=str,
        default=None,
        help="Date and time of the soonest arrival to the origin airport "
             "in UTC format - use only if looking for return flights "
             "(default=None)")

    parser.add_argument(
        "--departure",
        type=str,
        default=None,
        help="Date and time of the soonest departure from the origin "
             "airport in UTC format (default=None)")

    return parser.parse_args()


def main():
    args = init_parser()

    # checks for valid input
    if not valid_airport_code(getattr(args, "origin")):
        end_searching("Invalid origin airport code, e.g. KSC")

    if not valid_airport_code(getattr(args, "destination")):
        end_searching("Invalid destination airport code, e.g. CDG")

    if not os.path.isfile(getattr(args, "dataset")):
        end_searching("Given dataset path could not be found")

    if not getattr(args, "origin") != getattr(args, "destination"):
        end_searching(
            "Origin and destination airports can not be the same")

    if getattr(args, "returnarrival") and not getattr(args, "return"):
        end_searching(
            "Return arrival was specified but it is not a return flight")

    args = args.__dict__

    # checks for valid input + converts --> if invalid time
    # format, exits the code
    if args["arrival"] is not None:
        args["arrival"] = str_to_datetime(args["arrival"])

    if args["departure"] is not None:
        args["departure"] = str_to_datetime(args["departure"])

    if args["returnarrival"] is not None:
        args["returnarrival"] = str_to_datetime(args["returnarrival"])

    # valid input check - does customer want to arrive to the
    # destination sooner than he leaves?
    if args["arrival"] is not None and args["departure"] is not None:

        # we have already converted arrival and departure from str
        # to datetime objects if both were not none, now we can compare
        # them as datetime objects
        if args["arrival"] < args["departure"]:
            end_searching("Arrival is sooner than departure")

    # valid input check - does he want to arrive home sooner than he leaves?
    if args["returnarrival"] is not None and args["departure"] is not None:
        if args["returnarrival"] < args["departure"]:
            end_searching()

    all_flights_graph = Graph(**args)
    all_flights_graph.visit_all_vertices(origin=args["origin"],
                                         destination=args["destination"])

    # if it is a return flight, we need to visit vertices from
    # destination to origin
    if args["return"]:
        all_flights_graph.visit_all_vertices(origin=args["destination"],
                                             destination=args["origin"])

    # after having visited all the vertices, print all flight combinations
    all_flights_graph.print_found_combinations()


if __name__ == "__main__":
    main()
