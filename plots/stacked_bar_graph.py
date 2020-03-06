import numpy as np
import matplotlib.pyplot as plt




plot_dict = "../old_to_new/plot_dict.npy"
np.load(plot_dict)

P =

Q = [3]*len(plot_dict)




#the length of P and Q has to be the same
if len(P)==len(Q):
    N = len(P)
else:
    print ("The two stacks do not have the same size, exiting..")
    exit(0)

ind = np.arange(N)    # the x locations for the groups
width = 0.5

#there is an extra space of 0.5
p1 = plt.bar(ind+width/2, P, width, color = "darkorange")
p2 = plt.bar(ind+width/2, Q, width, bottom=P, color = "darkblue")

#label is a single label (ticks are different values)
plt.title('Nodes found within buffer') #at the top
plt.ylabel('Count of nodes')
plt.xlabel('Distance in miles')
plt.xticks(ind+width, [str(float(x)/10) for x in range(1,31)], rotation='vertical')
plt.yticks(np.arange(0, max(P)+10, 5))

plt.legend((p1[0], p2[0]), ('Correctly found', 'cannot be found'), fontsize='small')

plt.show()


