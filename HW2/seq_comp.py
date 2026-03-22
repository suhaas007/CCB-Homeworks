# Biquad Filter Simulation
# ========================
# From Figure 2a/2b, the biquad implements Direct Form II with all 1/8 coefficients:
#
#   w[n] = X[n] + (1/8)*w[n-1] + (1/8)*w[n-2]   (state update with feedback)
#   Y[n] = (1/8)*w[n] + (1/8)*w[n-1] + (1/8)*w[n-2]  (output)
#
# Chemical implementation uses TWO RGB delay chains:
#   RGB1: stores w[n-1]  (R1 -> G1 -> B1)
#   RGB2: stores w[n-2]  (R2 -> G2 -> B2)
#
# Signal color coding (following the paper's convention):
#   Red:   Y, R1, R2
#   Green: G1, G2
#   Blue:  X, B1, B2
#
# Each RGB cycle proceeds: Red -> Green -> Blue -> Red (next cycle)
# Absence indicators r, g, b gate transitions between color phases.

def biquad_filter(inputs, verbose=True):
    """
    Simulate the biquad filter for a sequence of input values.
    Returns list of output Y values.

    State variables:
      w1 = w[n-1]  (output of first delay, stored in RGB1)
      w2 = w[n-2]  (output of second delay, stored in RGB2)
    """
    w1, w2 = 0.0, 0.0
    outputs = []

    if verbose:
        print("Biquad Filter Simulation")
        print("Equation: w[n] = X[n] + (1/8)*w[n-1] + (1/8)*w[n-2]")
        print("          Y[n] = (1/8)*w[n] + (1/8)*w[n-1] + (1/8)*w[n-2]")
        print()
        print(f"{'Cycle':>5} | {'X':>6} | {'w[n]':>10} | {'w[n-1]':>10} | {'w[n-2]':>10} | {'Y[n]':>10}")
        print("-" * 65)

    for n, x in enumerate(inputs):
        # State update (feedback from both delays)
        w = x + (1/8)*w1 + (1/8)*w2

        # Output (feedforward from current and both delays)
        y = (1/8)*w + (1/8)*w1 + (1/8)*w2

        if verbose:
            print(f"  {n+1:>3} | {x:>6} | {w:>10.4f} | {w1:>10.4f} | {w2:>10.4f} | {y:>10.4f}")

        outputs.append(y)

        # Shift delays: w[n-2] <- w[n-1] <- w[n]
        w2, w1 = w1, w

    return outputs

# ── Chemical Reaction Network Description ──────────────────────────────────
# The chemistry follows the RGB framework from the paper, extended to two delays.
#
# SCALING REACTIONS (group 1 equivalent):
#   g + X  --kslow-->  A + C         X splits into A (->Y path) and C (->RGB1)
#   2C     --kfast-->  R1            halve C  (C/2 -> R1, first delay input)
#   2A     --kfast-->  Y             halve A  (A/2 -> Y direct output)
#   g + B1 --kslow-->  A2 + C2       B1 splits for second delay contribution
#   2C2    --kfast-->  R2            halve C2 -> R2 (second delay input)
#   2A2    --kfast-->  Y             halve A2 -> Y (adds to output)
#
# DELAY REACTIONS (group 2, one per RGB chain):
#   RGB1:  b1 + R1 --kslow--> G1
#          r1 + G1 --kslow--> B1
#          g1 + B1 --kslow--> Y + R1_new   (B1 contributes to Y and reloads)
#
#   RGB2:  b2 + R2 --kslow--> G2
#          r2 + G2 --kslow--> B2
#          g2 + B2 --kslow--> Y + R2_new
#
# COLOR INDICATOR, ABSENCE INDICATOR, and FEEDBACK reactions
# follow the same pattern as equations (3), (4), (5) in the paper,
# duplicated for each RGB chain.
# ───────────────────────────────────────────────────────────────────────────

print("=" * 65)
print("BIQUAD FILTER - 5 RGB CYCLES")
print("=" * 65)
print()

inputs = [100, 5, 500, 20, 250]
outputs = biquad_filter(inputs, verbose=True)

print()
print("=" * 65)
print("SUMMARY")
print("=" * 65)
print(f"{'Cycle':>5} | {'Input X':>8} | {'Output Y':>10}")
print("-" * 32)
for i, (x, y) in enumerate(zip(inputs, outputs)):
    print(f"  {i+1:>3} | {x:>8} | {y:>10.4f}")

print()
print("Note: Y values would be sampled (cleared) between cycles.")
print("The delay states w[n-1] and w[n-2] persist across cycles.")

import matplotlib.pyplot as plt
import numpy as np

# Biquad filter simulation
inputs = [100, 5, 500, 20, 250]
cycles = list(range(1, 6))

w1, w2 = 0.0, 0.0
w_vals, y_vals = [], []

for x in inputs:
    w = x + (1/8)*w1 + (1/8)*w2
    y = (1/8)*w + (1/8)*w1 + (1/8)*w2
    w_vals.append(w)
    y_vals.append(y)
    w2, w1 = w1, w

w1_hist = [0] + w_vals[:-1]
w2_hist = [0, 0] + w_vals[:-2]

# Plot
fig, axes = plt.subplots(2, 2, figsize=(12, 8))
fig.suptitle('Biquad Filter — 5 RGB Cycles', fontsize=14, fontweight='bold')

# 1. Input vs Output
ax = axes[0, 0]
x_pos = np.array(cycles)
ax.bar(x_pos - 0.2, inputs, 0.4, label='Input X', color='steelblue', alpha=0.8)
ax.bar(x_pos + 0.2, y_vals, 0.4, label='Output Y', color='tomato', alpha=0.8)
ax.set_title('Input X vs Output Y')
ax.set_xlabel('Cycle')
ax.set_xticks(cycles)
ax.legend()
ax.grid(axis='y', alpha=0.4)

# 2. Signal trajectories
ax = axes[0, 1]
ax.plot(cycles, inputs, 'o-', color='steelblue', label='Input X', lw=2)
ax.plot(cycles, y_vals, 's-', color='tomato',    label='Output Y', lw=2)
ax.plot(cycles, w_vals, '^--',color='seagreen',  label='State w[n]', lw=1.5, alpha=0.8)
ax.set_title('Signal Trajectories')
ax.set_xlabel('Cycle')
ax.set_xticks(cycles)
ax.legend()
ax.grid(alpha=0.4)

# 3. Delay states
ax = axes[1, 0]
ax.plot(cycles, w1_hist, 'o-', color='orange', label='w[n-1]  RGB1', lw=2)
ax.plot(cycles, w2_hist, 's-', color='purple', label='w[n-2]  RGB2', lw=2)
ax.set_title('Delay State Contents')
ax.set_xlabel('Cycle')
ax.set_xticks(cycles)
ax.legend()
ax.grid(alpha=0.4)

# 4. Y contribution breakdown
ax = axes[1, 1]
c1 = [w/8 for w in w_vals]
c2 = [(1/8)*w for w in w1_hist]
c3 = [(1/8)*w for w in w2_hist]
ax.bar(cycles, c1, label='(1/8)·w[n]',   color='seagreen', alpha=0.8)
ax.bar(cycles, c2, bottom=c1,            label='(1/8)·w[n-1]', color='orange', alpha=0.8)
ax.bar(cycles, c3, bottom=[a+b for a,b in zip(c1,c2)], label='(1/8)·w[n-2]', color='purple', alpha=0.8)
ax.plot(cycles, y_vals, 'ko--', lw=1.5, ms=6, label='Y total')
ax.set_title('Y Contribution Breakdown')
ax.set_xlabel('Cycle')
ax.set_xticks(cycles)
ax.legend(fontsize=8)
ax.grid(axis='y', alpha=0.4)

plt.tight_layout()
plt.savefig('biquad_plot.png', dpi=150, bbox_inches='tight')
plt.show()
print("Done!")
