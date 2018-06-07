#!/usr/bin/env python
import matplotlib.pyplot as plt
f, axarr = plt.subplots(2, 2)
axarr[0][0].plot([0, 1, 2, 3], [0, 1, 2, 3])
axarr[0][0].set_xlabel("Matrix element 1,1")
# Note matplotlib convention is transpose of the matrix notation we are using
axarr[0][1].plot([0, 1, 4, 9], [0, 1, 2, 3])
axarr[0][1].set_xlabel("Matrix element 1,2")
axarr[1][0].plot([0, 1, 2, 3], [0, 1, 4, 9])
axarr[1][0].set_xlabel("Matrix element 2,1")
axarr[1][1].plot([0, 1, 4, 9], [0, 1, 4, 9])
axarr[1][1].set_xlabel("Matrix element 2,2")
plt.savefig("multiplot.png")
