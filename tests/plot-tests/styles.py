#!/usr/bin/env python
import matplotlib.pyplot as plt
# Explicitly set styles:
plt.plot([1.0, 2.0, 3.0], [0.5, 2, 3.5], color='blue', linestyle='-.')
# Automatic styles should start from the beginning:
plt.plot([1.0, 2.0, 3.0], [1.0, 2.0, 3.0], color='red', linestyle='--')
plt.savefig("styles.png")
