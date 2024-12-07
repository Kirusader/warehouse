# Exogenous Information
import random

def generate_random_position(x_range, y_range):
    """Generate a random position within specified ranges."""
    return random.choice(x_range), random.choice(y_range)
