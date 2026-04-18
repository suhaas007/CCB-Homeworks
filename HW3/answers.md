# Answers

## Question 1

### Part (a)

- Use `f(x) = x(1 - x/4)`.
- Circuit: scale `x` to `x/4` with two `1/2` scalers, invert to get `1 - x/4`, then AND with `x`.
- Sample values:
  - `x = 0.00 -> 0.000000`
  - `x = 0.25 -> 0.234375`
  - `x = 0.50 -> 0.437500`
  - `x = 0.75 -> 0.609375`
  - `x = 1.00 -> 0.750000`

### Part (b)

- Approximation: `cos(x) ≈ 1 - x^2/2 + x^4/24`.
- Bernstein degree-4 coefficients: `1, 1, 11/12, 3/4, 13/24`.
- Sample values:
  - `x = 0.00 -> 1.000000`
  - `x = 0.25 -> 0.968913`
  - `x = 0.50 -> 0.877604`
  - `x = 0.75 -> 0.731934`
  - `x = 1.00 -> 0.541667`

### Part (c)

- Bernstein degree-5 coefficients: `1/2, 1/4, 1/8, 1/16, 1/32, 1`.
- Sample values:
  - `x = 0.00 -> 0.500000`
  - `x = 0.25 -> 0.257416`
  - `x = 0.50 -> 0.149414`
  - `x = 0.75 -> 0.281281`
  - `x = 1.00 -> 1.000000`

## Question 2

### Part (a)

- Source probabilities: `a = 0.4`, `b = 0.5`.
- Targets:
  - `0.8881188`
  - `0.2119209`
  - `0.5555555`
- The exact synthesized formulas are printed by `python3 HW3/question2.py`.

### Part (b)

- Source probability: `h = 0.5`.
- Binary targets:
  - `0.1011111_2 = 95/128 = 0.7421875`
  - `0.1101111_2 = 111/128 = 0.8671875`
  - `0.1010111_2 = 87/128 = 0.6796875`
- Aleae model files:
  - `q2b_1.in`, `q2b_1.r`
  - `q2b_2.in`, `q2b_2.r`
  - `q2b_3.in`, `q2b_3.r`
