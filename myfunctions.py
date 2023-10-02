import pandapower as pp
import pandapower.plotting as pplt
import matplotlib.pyplot as plt
from pandapower.plotting.plotly import simple_plotly
import pandapower.topology as top
from collections import Counter
# from functions import *
from itertools import islice
import networkx as nx
import math
import numpy as np
import time


net = pp.from_json("example_mv_grid.json")
mg = top.create_nxgraph(net)

lines = net.line.index
buses = net.bus.index

global_counter_l=0
global_counter_v=0


"""
def turn_off_al_rslines():
    net.line.loc[26, "in_service"] = False
    net.line.loc[72, "in_service"] = False
    net.line.loc[111, "in_service"] = False
    net.line.loc[162, "in_service"] = False
    net.line.loc[202, "in_service"] = False
    net.line.loc[247, "in_service"] = False
    net.line.loc[320, "in_service"] = False
    net.line.loc[365, "in_service"] = False
    net.line.loc[389, "in_service"] = False
    net.line.loc[411, "in_service"] = False"""

def n_1_safety_ll(net):
    # Set the limits
    max_ll = 100
    line_loading_too_high = []
    # Turn of all Ring Separation Lines
    for m in lines:
         if net.line.loc[m , "name"] == "ring_separation_line":
             net.line.loc[m, "in_service"] = False
    # Check all the loading problems after closing all lines step by step
    for l in lines:
        if net.line.loc[l, "name"] != "ring_separation_line":
          net.line.loc[l, "in_service"] = False
          pp.runpp(net,numba=False)
    # If there is a loading problem in any bus add to list
          for b in lines:
              if net.line.loc[b, "in_service"] == True and net.res_line.loc[b, "loading_percent"] > max_ll:
                  if b not in line_loading_too_high:
                     line_loading_too_high.append(b)
          net.line.loc[l,"in_service"] = True
    return (line_loading_too_high)

def n_1_safety_v(net):
    #Set the limits
    v_max = 1.05
    v_min = 0.95
    voltage_problematic_busses = []
    #Turn of all Ring Separation Lines
    for m in lines:
        if net.line.loc[m, "name"] == "ring_separation_line":
            net.line.loc[m, "in_service"] = False
    #Check all the voltage problems after closing all lines step by step
    for l in lines:
        if net.line.loc[l, "in_service"] == True :
          net.line.loc[l, "in_service"] = False
          pp.runpp(net,numba=False)
    #If there is a voltage problem in any bus add to list
          for b in buses:
              if net.res_bus.loc[b, "vm_pu"] < v_min or net.res_bus.loc[b, "vm_pu"] > v_max:
                  if b not in voltage_problematic_busses:
                     voltage_problematic_busses.append(b)
          net.line.loc[l,"in_service"] = True
    return voltage_problematic_busses

#KISALTILACAK
def add_parallel_line_voltage(net, list):
    all_branches = complete_branches(net)
    counter_array = np.zeros(len(list_starting_lines(net)), dtype=int)
    y = len(list)
    d = len(list_starting_lines(net))
    for m in range(y):
        for h in range(d):
            if list[m] in all_branches[h]:
                counter_array[h] += 1
                break
    counter_cost = 0
    for k in range(d):
        if counter_array[k] != 0:
            starting_bus = list_starting_buses_from_bus(net)[k]
            target_bus = all_branches[k][int(len(all_branches[k]) * (2 / 3))]
            pp.create_line(net=net, from_bus=starting_bus, to_bus=target_bus,
                           length_km=distance_between_bus(net, starting_bus, target_bus),
                           std_type="NA2XS2Y 1x240 RM/25 12/20 kV", name="starting_ring_line")
            #Costs

            counter_cost += distance_between_bus(net, starting_bus, target_bus)
            print("Cable Type:","NA2XS2Y 1x240 RM/25 12/20 kV","Distance:",distance_between_bus(net, starting_bus, target_bus))
            for t in lines:
                if net.line.loc[t, "to_bus"] == target_bus:
                    net.line.loc[t, "in_service"] = False
    print("Total new cables in km:", counter_cost)
    money = 60000 * counter_cost
    print("Total cost:", money,"€" )

def complete_branches(net):
    completebranches = []

    n = len(list_starting_buses_from_bus(net))
    for b in range(n):
        completebranches.append([])

    beforecounter = 0
    for a in range(n):
        completebranches[beforecounter].append(list_starting_buses_from_bus(net)[beforecounter])
        completebranches[beforecounter].append(list_starting_buses_to_bus(net)[beforecounter])
        beforecounter += 1

    aftercounter = 0
    for d in range(n):
        current_bus = completebranches[aftercounter][1]
        current_line = list_starting_lines(net)[aftercounter]

        while net.line.loc[current_line, "name"] != "ring_separation_line":
            for e in lines:
                if net.line.loc[e, "from_bus"] == current_bus and net.line.loc[e, "name"] == "ring_line" and \
                        net.line.loc[e, "to_bus"] not in completebranches[aftercounter]:
                    current_bus = net.line.loc[e, "to_bus"]
                    current_line = e
                    completebranches[aftercounter].append(current_bus)
                    break

                if net.line.loc[e, "to_bus"] == current_bus and net.line.loc[e, "name"] == "ring_line" and net.line.loc[
                    e, "from_bus"] not in completebranches[aftercounter]:
                    current_bus = net.line.loc[e, "from_bus"]
                    current_line = e
                    completebranches[aftercounter].append(current_bus)
                    break

                if net.line.loc[e, "from_bus"] == current_bus and net.line.loc[e, "name"] == "ring_separation_line":
                    current_line = e
                    break

                if net.line.loc[e, "to_bus"] == current_bus and net.line.loc[e, "name"] == "ring_separation_line":
                    current_line = e
                    break

        aftercounter += 1

    return completebranches
def list_starting_buses_to_bus(net):
    listtobus = list()
    for m in lines:
        if net.line.loc[m, "name"] == "starting_ring_line":
            listtobus.append(net.line.to_bus[m])#default function from pandapower
    return listtobus

def list_starting_buses_from_bus(net):
    listfrombus = list()
    for m in lines:
        if net.line.loc[m, "name"] == "starting_ring_line":
            listfrombus.append(net.line.from_bus[m])#default function from pandapower
    return listfrombus

def list_starting_lines(net):
    liststartinglines = list()
    for o in lines:
        if net.line.loc[o, "name"] == "starting_ring_line":
          liststartinglines.append(o)

    return liststartinglines
def distance_between_bus(net, starting_bus, target_bus):

  distance = top.calc_distance_to_bus(net, starting_bus)[target_bus]

  return distance

def increase_number_of_parallels_cost(net,list):
    y = len(list)
    cost = 0.0
    addedparallel_counter = 0.0
    for o in range(y):
        while list[o] in n_1_safety_ll(net):
          net.line.loc[list[o], "parallel"] +=1
          addedparallel_counter += 1
        cost += (addedparallel_counter * net.line.loc[list[o],'length_km'])


def n_1_main(net):
    print("Problematic busses (vmin or vmax) before adding new lines:")
    print(n_1_safety_v(net))
    add_parallel_line_voltage(net,n_1_safety_v(net))
    print("Problematic busses (vmin or vmax) after adding new lines:")
    print(n_1_safety_v(net))
    #print(complete_branches(net))


    """print("Problematic lines (max_ll) before adding parallel lines")
    print(n_1_safety_ll(net))
    increase_number_of_parallels_cost(net,n_1_safety_ll(net))
    print("Problematic lines (max_ll) after adding parallel lines")
    print(n_1_safety_ll(net))"""
