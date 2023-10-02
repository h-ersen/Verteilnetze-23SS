import networkx as nx
import pandapower as pp
import pandapower.plotting as pplt
import matplotlib.pyplot as plt
from pandapower.plotting.plotly import simple_plotly
import seaborn
from collections import Counter
import pandapower.topology as top

import myfunctions
import functions

net = pp.from_json("example_mv_grid.json")

#ANALYSIS SCENARIOS

#Default Case
print("-----Default Case-----")
myfunctions.n_1_main(net)

#Feed-In Case
print("-----Feed-In Case-----")
net.sgen.scaling = 0.8
net.load.scaling = 0.1
myfunctions.n_1_main(net)

#Heavy Load Case
print("-----Heavy-Load Case-----")
net.sgen.scaling = 0
net.load.scaling = 0.6
myfunctions.n_1_main(net)



#n1analysis()
#print(net.res_line.loading_percent)
#print(net)
####NA2XS2Y 1x240 RM/25 12/20 kV
#-----ALL PLOT FUNCTIONS-----
#Plot the network bigger with geodata
#simple_plotly(net, figsize=10)

#Plot the network with directions
#plotwithdirections()

#Plot without geodata
#myfunctions.plotnogeodata()

#-----NECESSARY NETWORK INFORMATION-----

#print(net.res_bus)
#print(net.res_line)
#print(net.line)
#pp.reset_results(net)







