import random, math, threading
import matplotlib.pyplot as plt
from tkinter import Tk, Frame, Canvas, Scrollbar, VERTICAL, Button
from turtle import TurtleScreen
from initial_state import initialize_warehouse
from model import release_robot
from policy import bring_shelf_to_target
from transition import bfs, move_robot

# Create the main Tkinter window
window = Tk()
window.title("Warehouse Automation")
window.minsize(width=800, height=800)
window.config(padx=20, pady=20, bg="gray")

# Create a main canvas that will be scrollable
main_canvas = Canvas(window, bg="gray", width=800, height=800)
main_canvas.pack(fill="both", expand=True, side="left")

# Add a vertical scrollbar and attach it to the main canvas
v_scrollbar = Scrollbar(window, orient=VERTICAL, command=main_canvas.yview)
v_scrollbar.pack(side="right", fill="y")
main_canvas.config(yscrollcommand=v_scrollbar.set)

# Create a frame inside the main canvas to hold other widgets
content_frame = Frame(main_canvas, bg="gray")
main_canvas.create_window((0, 0), window=content_frame, anchor="nw")

# Configure the main canvas scroll region to update as content is added
def update_scrollregion(event=None):
    main_canvas.configure(scrollregion=main_canvas.bbox("all"))

main_canvas.bind("<Configure>", update_scrollregion)

# Frame to hold the turtle canvas
turtle_canvas = Canvas(content_frame, width=800, height=700, bg="#acbeaa")
turtle_canvas.grid(column=0, row=0, padx=20, pady=20)

# Create a TurtleScreen from the Tkinter canvas and set tracer to 0 for faster drawing
turtle_screen = TurtleScreen(turtle_canvas)
turtle_screen.bgcolor("#acbeaa")
turtle_screen.tracer(0)  # Disable automatic updates

# Initialize warehouse
shelves, robots, occupied_positions, marker_positions, shelf_turtles= initialize_warehouse(turtle_screen)

# Assign tasks and control buttons
robot_x_cord = [-360, -280, -200, -120, -40, 40, 120, 200, 280]
robot_y_cord = [-200, -100, 0]
assigned_robots = {}
assigned_tasks = {}
track_shelf={}
lock = threading.Lock()
robot_distances = {robot: 0.0 for robot in robots}  # Dictionary to track total distances
# Function to calculate distance
def calculate_distance(pos1, pos2):
    return math.sqrt((pos2[0] - pos1[0]) ** 2 + (pos2[1] - pos1[1]) ** 2)
# Robot action functions
def pick_shelf(robot_index, target_position):
    """Generic function to pick a shelf and move to a target."""
    robot = robots[robot_index]
    shelf_name = f"shelf{random.randint(0, len(shelves) - 2)}"

    # Assign the task
    with lock:
        assigned_robots[robot] = shelf_name
        bring_shelf_to_target(robot, shelf_name, target_position, shelves, assigned_tasks)
        shelf_position = assigned_tasks[robot][0]

    # Calculate path to shelf
    robot_position = (round(robot.position()[0]), round(robot.position()[1]))
    start_marker_shelf = min(marker_positions, key=lambda pos: math.hypot(pos[0] - robot_position[0], pos[1] - robot_position[1]))
    goal_marker_shelf = min(marker_positions, key=lambda pos: math.hypot(pos[0] - shelf_position[0], pos[1] - shelf_position[1]))
    path = bfs(start_marker_shelf, goal_marker_shelf, marker_positions)
    move_robot(robot, path, occupied_positions, (goal_marker_shelf[0],shelf_position[1]), marker_positions)
    # Handle shelf visibility and tracking
    with lock:
        for shelf_turtle in shelf_turtles:
            if shelf_turtle.position() == shelves[shelf_name]:
                shelf_turtle.hideturtle()
                track_shelf[shelf_name] = shelf_turtle
                robot.shapesize(stretch_wid=2.0, stretch_len=2.0)
                robot.color("yellow")

    # Calculate path to target
    start_marker_target = min(marker_positions, key=lambda pos: math.hypot(pos[0] - shelf_position[0], pos[1] - shelf_position[1]))
    goal_marker_target = min(marker_positions, key=lambda pos: math.hypot(pos[0] - target_position[0], pos[1] - target_position[1]))
    path = bfs(start_marker_target, goal_marker_target, marker_positions)
    move_robot(robot, path, occupied_positions, (goal_marker_target[0],target_position[1]), marker_positions)
    robot_distances[robot]=calculate_distance(start_marker_shelf,goal_marker_shelf) + calculate_distance(start_marker_target,goal_marker_target)
    # Release the robot
    print(f"{shelf_name} moved to {target_position}. Total distance traveled by Robot {robot_index}: {robot_distances[robot]:.2f}")
    with lock:
        release_robot(robot, assigned_robots, assigned_tasks)

def finish_shelf(robot_index, target_position):
    """Generic function to return a shelf to its original position."""
    robot = robots[robot_index]
    with lock:
        # Ensure a shelf exists in track_shelf before proceeding
        if not track_shelf:
            print("No shelves to return.")
            return
        shelf_name, shelf_turtle = track_shelf.popitem()
    shelf_position=shelf_turtle.position()
    # Calculate path to shelf
    robot_position = (round(robot.position()[0]), round(robot.position()[1]))
    start_marker_shelf = min(marker_positions, key=lambda pos: math.hypot(pos[0] - robot_position[0], pos[1] - robot_position[1]))
    goal_marker_shelf = min(marker_positions, key=lambda pos: math.hypot(pos[0] - shelf_position[0], pos[1] - shelf_position[1]))
    path = bfs(start_marker_shelf, goal_marker_shelf, marker_positions)
    move_robot(robot, path, occupied_positions, (goal_marker_shelf[0],shelf_position[1]), marker_positions)

    # Handle shelf visibility
    with lock:
        shelf_turtle.showturtle()
        robot.shapesize(stretch_wid=1.5, stretch_len=1.5)
        robot.color("blue")

    # Calculate path to target
    robot_position = (round(robot.position()[0]), round(robot.position()[1]))
    start_marker = min(marker_positions, key=lambda pos: math.hypot(pos[0] - robot_position[0], pos[1] - robot_position[1]))
    goal_marker = min(marker_positions, key=lambda pos: math.hypot(pos[0] - target_position[0], pos[1] - target_position[1]))
    path = bfs(start_marker, goal_marker, marker_positions)
    move_robot(robot, path, occupied_positions, target_position, marker_positions)
    # Release the robot
    print(f"{shelf_name} returned to its original position.")
    with lock:
        release_robot(robot, assigned_robots, assigned_tasks)

# Button actions
def pick_shelf_1():
    threading.Thread(target=pick_shelf, args=(0, (-300, -260))).start()

def pick_shelf_2():
    threading.Thread(target=pick_shelf, args=(1, (-200, -260))).start()
def stow_shelf_1():
    """Start a thread for Stow 1 task."""
    threading.Thread(target=pick_shelf, args=(2, (200, -260))).start()

def stow_shelf_2():
    """Start a thread for Stow 2 task."""
    threading.Thread(target=pick_shelf, args=(3, (300, -260))).start()
def finish_pick_1():
    """Start a thread for Pick 1 task."""
    threading.Thread(target=finish_shelf, args=(0,  ((random.choice(robot_x_cord)+40),(random.choice(robot_y_cord)+50)))).start()

def finish_pick_2():
    """Start a thread for Pick 2 task."""

    threading.Thread(target=finish_shelf, args=(1,  ((random.choice(robot_x_cord)+40),(random.choice(robot_y_cord)+50)))).start()

def finish_stow_1():
    """Start a thread for Stow 1 task."""
    threading.Thread(target=finish_shelf, args=(2, ((random.randint(-300, 200)), (random.randint(-200, 60))))).start()

def finish_stow_2():
    """Start a thread for Stow 2 task."""
    threading.Thread(target=finish_shelf, args=(3, ((random.randint(-300,200)), (random.randint(-200,60))))).start()

# Create a separate canvas for text elements and buttons below the turtle canvas
text_canvas = Canvas(content_frame, width=800, height=300, bg="#94d2bd", highlightthickness=0)
text_canvas.grid(column=0, row=1, padx=20, pady=20)

# Adding text labels to the text canvas
text_canvas.create_text(400, 40, text="Work Stations", fill="white", font=("Courier", 18, "bold"))
text_canvas.create_text(100, 100, text="Pick Station", fill="white", font=("Courier", 14, "bold"))
text_canvas.create_text(50, 150, text="Pick 1", fill="white", font=("Courier", 12, "bold"))
text_canvas.create_text(150, 150, text="Pick 2", fill="white", font=("Courier", 12, "bold"))
text_canvas.create_text(670, 100, text="Stow Station", fill="white", font=("Courier", 14, "bold"))
text_canvas.create_text(610, 150, text="Stow 1", fill="white", font=("Courier", 12, "bold"))
text_canvas.create_text(740, 150, text="Stow 2", fill="white", font=("Courier", 12, "bold"))

# Adding interactive buttons to the text canvas
pick_1 = Button(text="Pick", command=pick_shelf_1, font=("Courier", 12, "bold"))
pick_2 = Button(text="Pick", command=pick_shelf_2, font=("Courier", 12, "bold"))
stow_1 = Button(text="Stow", command=stow_shelf_1, font=("Courier", 12, "bold"))
stow_2 = Button(text="Stow", command=stow_shelf_2, font=("Courier", 12, "bold"))

# Place buttons on the text canvas
text_canvas.create_window(50, 180, window=pick_1)
text_canvas.create_window(150, 180, window=pick_2)
text_canvas.create_window(610, 180, window=stow_1)
text_canvas.create_window(740, 180, window=stow_2)
finish_pick_1 = Button(text="Finish", command=finish_pick_1, font=("Courier", 12, "bold"))
finish_pick_2 = Button(text="Finish", command=finish_pick_2, font=("Courier", 12, "bold"))
finish_stow_1 = Button(text="Finish", command=finish_stow_1, font=("Courier", 12, "bold"))
finish_stow_2 = Button(text="Finish", command=finish_stow_2, font=("Courier", 12, "bold"))

# Place buttons on the text canvas
text_canvas.create_window(50, 230, window=finish_pick_1)
text_canvas.create_window(150, 230, window=finish_pick_2)
text_canvas.create_window(610, 230, window=finish_stow_1)
text_canvas.create_window(740, 230, window=finish_stow_2)
# Update the turtle screen manually after drawing all elements
turtle_screen.update()

# Main loop to run the Tkinter window
window.mainloop()
