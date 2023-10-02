import pandapower as pp
import pandapower.topology as top
from collections import Counter
# from functions import *
from itertools import islice
import networkx as nx
import math



net = pp.from_json("example_mv_grid.json")
mg = top.create_nxgraph(net)





def find_branch_buses(net):
    ''' returns the buses which are the first element
    of a branch with the number of branches as a tuple
    '''
    bus_list = list()
    lines = net.line.index
    for line in lines:
        if net.line.loc[line, "name"] == "branch_line":
            bus_list.append(net.line.loc[line, "from_bus"])

    return Counter(bus_list)


def lines_connected_with_bus(net, bus):
    ''' returns the index of lines which are connected with the bus in a list
    '''

    lines = net.line.index
    line_index = list()
    for line in lines:
        if net.line.loc[line, "from_bus"] == bus or net.line.loc[line, "to_bus"] == bus:
            line_index.append(line)

    return line_index


def get_lines_to_bus(net, bus):
    ''' returns the list of the lines which leads to the bus ina list
    '''

    lines = net.line.index
    line_to_bus = list()
    for line in lines:
        if net.line.loc[line, "to_bus"] == bus:
            line_to_bus.append(line)
    return line_to_bus


def get_lines_from_bus(net, bus):
    ''' returns the index of the lines which leads away from the bus in a list
    '''
    lines = net.line.index
    lines_from_bus = list()
    for line in lines:
        if net.line.loc[line, "from_bus"] == bus:
            lines_from_bus.append(line)
    return lines_from_bus


def get_prev_bus(net, bus):
    ''' returns the previous bus of the given bus
    '''

    line_to_bus = get_lines_to_bus(net, bus)
    prev_bus = net.line.loc[line_to_bus[0], "from_bus"]
    return prev_bus


def get_main_bus(net, bus):
    current_bus = bus
    while (net.line.loc[get_lines_to_bus(net, current_bus)[0], "name"] != "starting_ring_line"):
        current_bus = get_prev_bus(net, current_bus)
    return current_bus


def get_prev_bus_nx(mg, bus):
    cc = top.connected_component(mg, bus)
    prev_bus = next(islice(cc, 1, None))
    return int(prev_bus)


def get_main_bus_short(mg, net, bus):
    """Returns the nearest main bus connected to the given bus
    mg: nX network
    net: pandapower network
    bus: given bus
    """
    main_buses = list()
    main_bus = None
    lines = net.line.index
    for i in lines:
        if net.line.loc[i, "name"] == "starting_ring_line":
            main_bus = net.line.loc[i, "to_bus"]
            main_buses.append(main_bus)

    min_distance = 500
    for i in main_buses:
        distance = nx.shortest_path_length(mg, i, bus)

        if distance < min_distance:
            min_distance = distance
            nearest_main_bus = i
    return nearest_main_bus


def get_main_trafo(mg, net, bus):
    """Returns the nearest main bus connected to the given bus
    mg: nX network
    net: pandapower network
    bus: given bus
    """
    main_buses = list()
    main_bus = None
    lines = net.line.index
    for i in lines:
        if net.line.loc[i, "name"] == "starting_ring_line":
            main_bus = net.line.loc[i, "from_bus"]
            main_buses.append(main_bus)

    min_distance = 500
    for i in main_buses:
        distance = nx.shortest_path_length(mg, i, bus)

        if distance < min_distance:
            min_distance = distance
            nearest_main_bus = i
    return nearest_main_bus


def get_end_bus(mg, net, bus):
    end_buses = list()
    lines = net.line.index
    for i in lines:
        if net.line.loc[i, "name"] == "ring_separation_line":
            end_buses.append(net.line.loc[i, "from_bus"])
            end_buses.append(net.line.loc[i, "to_bus"])

    min_distance = 500
    for i in end_buses:
        distance = nx.shortest_path_length(mg, i, bus)

        if distance < min_distance:
            min_distance = distance
            nearest_end_bus = i
    return nearest_end_bus


def shortest_distance_from_main_bus(mg, net, bus):
    main_bus = get_main_bus_short(mg, net, bus)
    shortest_distance = nx.shortest_path(mg, main_bus, bus)
    return shortest_distance


def shortest_distance_from_trafo(mg, net, bus):
    main_bus = get_main_trafo(mg, net, bus)
    shortest_distance = nx.shortest_path(mg, main_bus, bus)
    return shortest_distance


def distance_between_bus(net, bus1, bus2):
    distance = math.sqrt(math.pow(net.bus_geodata.loc[bus1, "x"] - net.bus_geodata.loc[bus2, "x"], 2)
                         + math.pow(net.bus_geodata.loc[bus1, "y"] - net.bus_geodata.loc[bus2, "y"], 2))
    return distance


def add_parallel_line_from_main_bus(nx, net, bus):
    shortest_path = shortest_distance_from_main_bus(nx, net, bus)
    target_bus = shortest_path[int(len(shortest_path)*(2/3))]
    pp.create_line(net=net, from_bus=shortest_path[0], to_bus=target_bus, length_km=distance_between_bus(
        net, shortest_path[0], target_bus), std_type="NAYY 4x50 SE")
    global mg
    mg = top.create_nxgraph(net)


def add_parallel_line_from_trafo(nx, net, bus):
    shortest_path = get_branch(nx, net, bus)
    target_bus = shortest_path[int(len(shortest_path)*(2/3))]
    pp.create_line(net=net, from_bus=shortest_path[0], to_bus=target_bus, length_km=distance_between_bus(
        net, shortest_path[0], target_bus), std_type="NAYY 4x50 SE")
    net.line.loc[get_lines_to_bus(net, target_bus)[0], "in_service"] = False
    global mg
    mg = top.create_nxgraph(net)


def get_branch(mg, net, bus):
    end_bus = get_end_bus(mg, net, bus)
    starting_bus = get_main_trafo(mg, net, bus)
    path = nx.shortest_path(mg, starting_bus, end_bus)
    return path