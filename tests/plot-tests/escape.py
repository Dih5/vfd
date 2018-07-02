#!/usr/bin/env python
import matplotlib.pyplot as plt
plt.plot([1.0, 2.0, 3.0], [1.0, 2.0, 9.0], label="I'm a test")
plt.legend()
plt.xlabel("I have ', \", \\'a and \\\"a")
plt.ylabel("Escaped LaTeX acute:\n \\'a")
plt.savefig("escape.png")
