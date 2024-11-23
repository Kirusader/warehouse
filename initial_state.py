# Initial States
import random
from turtle import RawTurtle
robot_x_cord = [-360, -280, -200, -120, -40, 40, 120, 200, 280]
robot_y_cord = [-200, -100, 0]
def initialize_warehouse(turtle_screen):
    """Initialize warehouse with robots, shelves, and markers."""
    shelves = {}
    robots = []
    occupied_positions = set()
    marker_positions = []
    shelf_turtles = []
    create_shelves(turtle_screen, shelves, shelf_turtles)
    create_robots(turtle_screen, robots, occupied_positions)
    add_grid_markers(turtle_screen, marker_positions)
    draw_vertical_lines(turtle_screen)
    draw_horizontal_lines(turtle_screen)
    return shelves, robots, occupied_positions, marker_positions, shelf_turtles

def create_shelves(turtle_screen, shelves, shelf_turtles):
    """Create shelves in a grid layout."""
    for x in range(-320, 300, 80):
        for y in range(200, 360, 60):
            shelf = RawTurtle(turtle_screen, shape="square")
            shelf.speed(0)
            shelf.color("yellow")
            shelf.shapesize(stretch_wid=2, stretch_len=2)
            shelf.penup()
            shelf.goto(x, y)
            shelf_turtles.append(shelf)
            shelves[f"shelf{shelf_turtles.index(shelf)}"] = (x, y)

def create_robots(turtle_screen, robots, occupied_positions):
    """Create robots at random positions."""
    for _ in range(4):
        robot = RawTurtle(turtle_screen, shape="square")
        robot.speed(1)
        robot.color("blue")
        robot.penup()
        robot.shapesize(stretch_len=1.5, stretch_wid=1.5)
        position = ((random.choice(robot_x_cord)+40),(random.choice(robot_y_cord)+50))
        robot.goto(position)
        robots.append(robot)
        occupied_positions.add(position)
# Function to draw vertical grid lines
def draw_vertical_lines(turtle_screen):
    for x in range(-360, 360, 80):
        line = RawTurtle(turtle_screen)
        line.color("red")
        line.pensize(4)
        line.penup()
        line.goto(x, 320)
        line.pendown()
        line.goto(x, -200)
        line.hideturtle()

# Function to draw horizontal grid lines
def draw_horizontal_lines(turtle_screen):
    for y in range(-200, 100, 100):
        line = RawTurtle(turtle_screen)
        line.color("red")
        line.pensize(4)
        line.penup()
        line.goto(-360, y)
        line.pendown()
        line.goto(280, y)
        line.hideturtle()
def add_grid_markers(turtle_screen, marker_positions):
    """Add grid markers for navigation."""
    for x in range(-360, 360, 80):
        for y in range(-200, 100, 100):
            marker = RawTurtle(turtle_screen, shape="square")
            marker.color("green")
            marker.penup()
            marker.goto(x, y)
            marker_positions.append((x, y))
