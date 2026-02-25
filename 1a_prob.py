import random

def choose_reaction(x1, x2, x3):
    a1 = 0
    a2 = 0
    a3 = 0

    # Check feasibility before computing propensity
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


def simulate():
    x1, x2, x3 = 110, 26, 55

    while True:
        # Check stopping conditions
        if x1 >= 150:
            return 1
        if x2 < 10:
            return 2
        if x3 > 100:
            return 3

        reaction = choose_reaction(x1, x2, x3)

        if reaction is None:
            return None

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


def estimate(N=10000):
    c1 = c2 = c3 = 0

    for _ in range(N):
        result = simulate()

        if result == 1:
            c1 += 1
        elif result == 2:
            c2 += 1
        elif result == 3:
            c3 += 1

    print("Results after", N, "simulations:")
    print("Pr(C1) ≈", c1/N)
    print("Pr(C2) ≈", c2/N)
    print("Pr(C3) ≈", c3/N)


estimate(10000)
