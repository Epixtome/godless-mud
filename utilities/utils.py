import random

def roll_dice(dice_str):
    """Parses '2d3' and returns the sum of rolls."""
    try:
        count, sides = map(int, dice_str.lower().split('d'))
        return sum(random.randint(1, sides) for _ in range(count))
    except ValueError:
        return 0