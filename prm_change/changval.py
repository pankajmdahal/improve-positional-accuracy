number_of_iterations_range = 50

for iters in range(1,number_of_iterations_range+1):
    with open("network"+str(iters)+".prm", "w") as text_file:
        text_file.write("R:Y M:Y V:Y D:N C:Y X:Y L:Y V:Y A:Y\n")
        text_file.write("Network-US. US mainlines\n")
        text_file.write("    0.0225      7.40      7.70    0.0225      7.40      7.70     99999  {0:3}  \n".format(iters))
        text_file.write("     10000     10000    100000         0         0         0    150000     15000 \n")