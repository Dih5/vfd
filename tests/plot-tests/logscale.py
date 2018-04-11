#!/usr/bin/env python
import matplotlib.pyplot as plt
plt.plot([1.0, 2.0, 3.0], [10, 100, 1000])
plt.yscale("log")
plt.savefig("logscale.png")
