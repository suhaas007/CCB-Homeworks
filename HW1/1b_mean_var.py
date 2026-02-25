import random
import numpy as np

def choose_reaction(x1, x2, x3):
    a1 = 0
    a2 = 0
    a3 = 0

    if x1 >= 2 and x2 >= 1:
        a1 = 0.5 * x1 * (x1 - 1) * x2

    if x1 >= 1 and x3 >= 2:
        a2 = x1 * x3 * (x3 - 1)

    if x2 >= 1 and x3 >= 1:
        a3 = 3 * x2 * x3

    total = a1 + a2 + a3

    if total == 0:
        return None

    r = random.uniform(0, total)

    if r < a1:
        return 1
    elif r < a1 + a2:
        return 2
    else:
        return 3


def simulate_7_steps():
    x1, x2, x3 = 9, 8, 7

    for _ in range(7):
        reaction = choose_reaction(x1, x2, x3)

        if reaction is None:
            break

        if reaction == 1:
            x1 -= 2
            x2 -= 1
            x3 += 4

        elif reaction == 2:
            x1 -= 1
            x2 += 3
            x3 -= 2

        elif reaction == 3:
            x1 += 2
            x2 -= 1
            x3 -= 1

    return x1, x2, x3


def estimate_statistics(N=50000):

    X1 = []
    X2 = []
    X3 = []

    for _ in range(N):
        x1, x2, x3 = simulate_7_steps()
        X1.append(x1)
        X2.append(x2)
        X3.append(x3)

    X1 = np.array(X1)
    X2 = np.array(X2)
    X3 = np.array(X3)

    print("After 7 steps:")
    print("Mean X1 =", np.mean(X1))
    print("Variance X1 =", np.var(X1))

    print("Mean X2 =", np.mean(X2))
    print("Variance X2 =", np.var(X2))

    print("Mean X3 =", np.mean(X3))
    print("Variance X3 =", np.var(X3))


estimate_statistics(50000)

