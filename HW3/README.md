# HW3

This folder only keeps:

- `question1.py`
- `question2.py`
- the generated `.in` and `.r` files
- `README.md`
- `answers.md`

How to use it:

```bash
python3 HW3/question1.py
python3 HW3/question1.py --write-models
python3 HW3/question2.py
python3 HW3/question2.py --write-models
```

Behavior:

- Running either Python file with no flags prints the answers to the terminal.
- `--write-models` writes the Aleae `.in` and `.r` files into `HW3/`.

Aleae examples:

```bash
./aleae HW3/q1a_00.in HW3/q1a.r 1000 -1 0
./aleae HW3/q2b_1.in HW3/q2b_1.r 1000 -1 0
```
