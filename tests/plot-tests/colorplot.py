#!/usr/bin/env python
import matplotlib.pyplot as plt
plt.pcolormesh([1.0, 2.0], [1.0, 2.0, 9.0], [[1, 2], [4, 5], [7, 8]])
plt.xlabel("The x label")
plt.title("The title")
plt.colorbar()
plt.savefig("colorplot.png")
