#!/usr/bin/env python3
import sys
import random


def roll_dice(roll_string):
    d_split = d_string.split("d")
    d_type = int(d_split[1])
    d_amount = int(d_split[0])

    rolls = []
    for i in range(0, d_amount):
        rolls.append(random.randint(1, d_type))

    return rolls


if __name__ == "__main__":
    d_string = sys.argv[1]
    rolls = roll_dice(d_string)
    print(rolls)
    print(sum(rolls))
