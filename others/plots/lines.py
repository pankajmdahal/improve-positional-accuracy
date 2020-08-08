import numpy as np
import matplotlib.pyplot as plt




plot_dict_loc = "../old_to_new/plot_dict11.npy"
plot_dict = np.load(plot_dict_loc).item()

colors = list("rgbcmyk")

plt.figure()
for i in plot_dict.keys()[9:10]:
    subset_data = {y[2]:y[1] for x,y in plot_dict[i].iteritems()} #
    dataXY = subset_data
    _x_ = dataXY.keys()
    _x_.sort()
    _y_ = [float(dataXY[k]) for k in _x_]
    #normalizing values
    x = [float(p) for p in _x_]
    y = [float(p) for p in _y_]
    plt.plot(x,y,color='grey')

plt.show()





ind = np.arange(N)    # the x locations for the groups
width = 0.5

#there is an extra space of 0.5
p1 = plt.bar(ind+width/2, P, width, color = "darkorange")


#label is a single label (ticks are different values)
plt.title('Nodes found within buffer') #at the top
plt.ylabel('Count of nodes')
plt.xlabel('Distance in miles')
plt.xticks(ind+width, [str(float(x)/10) for x in range(1,31)], rotation='vertical')
plt.yticks(np.arange(0, max(P)+10, 5))

plt.legend((p1[0]), ('Correctly found'), fontsize='small')

plt.show()


