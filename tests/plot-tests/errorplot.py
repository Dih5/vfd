#!/usr/bin/env python
import matplotlib.pyplot as plt

plt.plot([1.0, 2.0, 3.0], [1.0, 2.0, 9.0])
plt.fill_between([1.0, 2.0, 3.0], [0.0, 0.5, 7.0], [2.0, 3.5, 11.0], alpha=0.5)
plt.errorbar([1.0, 2.0, 3.0], [2.0, 3.0, 10.0], yerr=[1, 1.5, 2], fmt="o")
plt.savefig("errorplot.png")
