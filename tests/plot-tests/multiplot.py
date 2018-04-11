#!/usr/bin/env python
import matplotlib.pyplot as plt
f, axarr = plt.subplots(2, 2)
axarr[0][0].plot([0, 1, 2, 3], [0, 1, 2, 3])
axarr[0][0].set_xlabel(r"Plot 0,0")
axarr[1][0].plot([0, 1, 4, 9], [0, 1, 2, 3])
axarr[1][0].set_xlabel(r"Plot 1,0")
axarr[0][1].plot([0, 1, 2, 3], [0, 1, 4, 9])
axarr[0][1].set_xlabel(r"Plot 0,1")
axarr[1][1].plot([0, 1, 4, 9], [0, 1, 4, 9])
axarr[1][1].set_xlabel(r"Plot 1,1")
plt.savefig("multiplot.png")
