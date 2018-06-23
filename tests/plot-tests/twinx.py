#!/usr/bin/env python
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
twinx = ax.twinx()
ax.plot([1.0, 2.0, 3.0], [1.0, 2.0, 9.0], label='Dum')
twinx.semilogy([1.0, 2.0, 3.0], [1.0, 1.5, 1.0], label='Dee', color="C1")
ax.set_ylabel("Tweedledum")
twinx.set_ylabel("Tweedledee")
twinx.set_ylim(0.1, 2.1)
ax.legend(loc="upper left")
twinx.legend(loc="upper right")
plt.savefig("twinx.png")
