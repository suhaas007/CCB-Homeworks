def fibonacci(a, b, steps):
    print(f"Starting values: a={a}, b={b}")
    print(f"Step  0: a={a}, b={b}")
    for i in range(1, steps + 1):
        a, b = b, a + b
        print(f"Step {i:2d}: a={a}, b={b}")
    print(f"\nFinal result after {steps} steps: a={a}")
    return a
 
print("=== Demo 1: starting values 0, 1 ===")
fibonacci(0, 1, 12)
 
print()
 
print("=== Demo 2: starting values 3, 7 ===")
fibonacci(3, 7, 12)
