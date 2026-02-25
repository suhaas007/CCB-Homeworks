import numpy as np
import matplotlib.pyplot as plt

data = np.loadtxt("lambda_results.txt", skiprows=1)

moi = data[:,0]
stealth = data[:,1]
hijack = data[:,2]

plt.figure(figsize=(8,5))
plt.plot(moi, stealth, marker='o', label="Stealth (cI2 ≥ 145)")
plt.plot(moi, hijack, marker='s', label="Hijack (Cro2 ≥ 55)")

plt.xlabel("Multiplicity of Infection (MOI)")
plt.ylabel("Probability (%)")
plt.title("Lambda Phage Decision Probability vs MOI")
plt.legend()
plt.grid(True)

plt.savefig("lambda_plot.png", dpi=300)
plt.show()

