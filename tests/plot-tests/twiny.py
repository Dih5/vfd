#!/usr/bin/env python
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
twiny = ax.twiny()
ax.plot([1.0, 2.0, 3.0], [1.0, 2.0, 9.0], label='Dum')
twiny.semilogx([1.0, 2.0, 3.0], [1.0, 1.5, 1.0], label='Dee', color="C1")
ax.set_xlabel("Tweedledum")
twiny.set_xlabel("Tweedledee")
twiny.set_xlim(0.1, 2.1)
ax.legend(loc="lower right")
twiny.legend(loc="upper right")
plt.savefig("twiny.png")
