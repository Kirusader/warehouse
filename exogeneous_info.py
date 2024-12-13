# Exogenous Information
import random

def generate_random_position(x_range, y_range):
    """Choose a random position from the provided list."""
    return random.choice(x_range), random.choice(y_range)
