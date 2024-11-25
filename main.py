import random, math, threading,time,tracemalloc,queue
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
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
main_canvas = Canvas(window, bg="gray", width=1000, height=1000)
main_canvas.pack(fill="both", expand=True, side="left")

# Add a vertical scrollbar and attach it to the main canvas
v_scrollbar = Scrollbar(window, orient=VERTICAL, command=main_canvas.yview)
v_scrollbar.pack(side="right", fill="y")
main_canvas.config(yscrollcommand=v_scrollbar.set)

# Create a frame inside the main canvas to hold other widgets
content_frame = Frame(main_canvas, bg="gray")
main_canvas.create_window((0, 0), window=content_frame, anchor="nw")

# Create a new canvas for the bar plot
bar_canvas = Canvas(content_frame, width=800, height=800, bg="#94d2bd", highlightthickness=0)
bar_canvas.grid(column=0, row=2, padx=20, pady=20)

# Configure the main canvas scroll region to update as content is added
def update_scrollregion(event=None):
    main_canvas.configure(scrollregion=main_canvas.bbox("all"))

main_canvas.bind("<Configure>", update_scrollregion)

# Frame to hold the turtle canvas
turtle_canvas = Canvas(content_frame, width=800, height=800, bg="#acbeaa")
turtle_canvas.grid(column=0, row=0, padx=20, pady=20)

# Create a TurtleScreen from the Tkinter canvas and set tracer to 0 for faster drawing
turtle_screen = TurtleScreen(turtle_canvas)
turtle_screen.bgcolor("#acbeaa")
turtle_screen.tracer(0)  # Disable automatic updates

# Initialize warehouse
shelves, robots, occupied_positions, marker_positions, shelf_turtles= initialize_warehouse(turtle_screen)
robot_x_cord = [-360, -280, -200, -120, -40, 40, 120, 200, 280]
robot_y_cord = [-200, -100, 0]
# Assign tasks and control buttons
assigned_robots = {}
assigned_tasks = {}
track_shelf={}
lock = threading.Lock()
# Tracking data for robots
robot_distances = {robot: 0.0 for robot in robots}
robot_times = {robot: 0.0 for robot in robots}
robot_memories = {robot: 0.0 for robot in robots}
# Thread-safe queue for updating the bar plot
plot_update_queue = queue.Queue()
def calculate_distance(pos1, pos2):
    """Calculate Euclidean distance between two positions."""
    return math.sqrt((pos2[0] - pos1[0]) ** 2 + (pos2[1] - pos1[1]) ** 2)
def update_bar_plot_main():
    """Update the bar plot on the main thread."""
    try:
        # Process data from the queue
        while not plot_update_queue.empty():
            robot_labels, distances, times, memories = plot_update_queue.get()

            # Create the plot
            fig, ax = plt.subplots(figsize=(12, 5))
            width = 0.25  # Width of the bars

            # Plot data
            x = range(len(robot_labels))
            ax.bar([i - width for i in x], distances, width, label="Distance (units)")
            ax.bar(x, times, width, label="Time (s)")
            ax.bar([i + width for i in x], memories, width, label="Memory (MB)")

            # Add labels and legend
            ax.set_title("Robot Performance Metrics")
            ax.set_xticks(x)
            ax.set_xticklabels(robot_labels)
            ax.set_xlabel("Robots")
            ax.legend()

            # Clear previous plots from the canvas
            for widget in bar_canvas.winfo_children():
                widget.destroy()

            # Embed the plot into the Tkinter canvas
            canvas = FigureCanvasTkAgg(fig, master=bar_canvas)
            canvas_widget = canvas.get_tk_widget()
            canvas_widget.pack()
            canvas.draw()
    except Exception as e:
        print(f"Error updating plot: {e}")

def schedule_bar_plot_update():
    """Schedule the bar plot update on the main thread."""
    robot_labels = [f"Robot {i}" for i in range(len(robot_distances))]
    distances = list(robot_distances.values())
    times = list(robot_times.values())
    memories = [mem * 300 / (1024*1024) for mem in robot_memories.values()]  # Convert memory to MB

    # Put data in the queue and schedule the update
    plot_update_queue.put((robot_labels, distances, times, memories))
    window.after(100, update_bar_plot_main)

# Robot action functions
def pick_shelf(robot_index, target_position):
    """Generic function to pick a shelf and move to a target."""
    robot = robots[robot_index]
    while True:
        shelf_name = f"shelf{random.randint(0, len(shelves) - 2)}"
        if shelf_name not in track_shelf.keys():
            break
    start_time =  time.time()
    tracemalloc.start()
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
    # Update time and memory
    robot_times[robot] += abs(time.time() - start_time)
    current_memory, _ = tracemalloc.get_traced_memory()
    robot_memories[robot] += current_memory
    tracemalloc.stop()
    # Release the robot
    print(f"{shelf_name} moved to {target_position}. Total distance traveled by Robot {robot_index}: {robot_distances[robot]:.2f}")
    with lock:
        release_robot(robot, assigned_robots, assigned_tasks)
        # Update the bar plot after task completion
        # Schedule the bar plot update
    schedule_bar_plot_update()
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
    threading.Thread(target=finish_shelf, args=(2,  ((random.choice(robot_x_cord)+40),(random.choice(robot_y_cord)+50)))).start()

def finish_stow_2():
    """Start a thread for Stow 2 task."""
    threading.Thread(target=finish_shelf, args=(3,  ((random.choice(robot_x_cord)+40),(random.choice(robot_y_cord)+50)))).start()

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

# Initialize the first bar plot
schedule_bar_plot_update()
turtle_screen.update()

# Main loop to run the Tkinter window
window.mainloop()
