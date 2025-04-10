
import sqlite3;
import pygame
import random
import time
import pandas as pd
import os
import subprocess
from pygame.locals import *

myconnection = sqlite3.connect('Fitzesdb.db')
cursor = myconnection.cursor()
 
# Initialize pygame

pygame.init()
 
# Set screen dimensions to a larger size

screen_width = 1024

screen_height = 768

screen = pygame.display.set_mode((screen_width, screen_height))

pygame.display.set_caption("Fitts' Law Experiment")
 
# Colors

WHITE = (255, 255, 255)

BLACK = (0, 0, 0)

RED = (255, 0, 0)

GREEN = (0, 200, 0)

BLUE = (0, 0, 255)
 
# Experiment settings

circle_diameters = [35, 40, 45, 50, 55, 65, 70, 100]  # in pixels

distances = [100, 150, 200, 250, 300, 350, 400]  # in pixels

directions = ['left', 'right']

task_combinations = [(d, dist, dir) for d in circle_diameters for dist in distances for dir in directions]

random.shuffle(task_combinations)
 
# Participant info (You should replace this with actual data from participants)

participants = [{"id": i + 1} for i in range(15)]  # 15 participants

participant_results = []
 
# Create a function to present a circle and time the task

def present_task(diameter, distance, direction):

    circle_radius = diameter // 2

    center_x, center_y = screen_width // 2, screen_height // 2
 
    if direction == 'left':

        target_x = center_x - distance

    elif direction == 'right':

        target_x = center_x + distance
 
    target_y = center_y
 
    # Draw background and circle target

    screen.fill(WHITE)

    pygame.draw.circle(screen, RED, (target_x, target_y), circle_radius)

    # Update the display

    pygame.display.flip()
 
    # Start the timing and wait for a click

    start_time = time.time()

    clicked = False

    while not clicked:

        for event in pygame.event.get():

            if event.type == QUIT:

                pygame.quit()

                exit()

            elif event.type == MOUSEBUTTONDOWN:

                mouse_x, mouse_y = pygame.mouse.get_pos()

                distance_to_center = ((mouse_x - target_x) ** 2 + (mouse_y - target_y) ** 2) ** 0.5

                if distance_to_center <= circle_radius:

                    clicked = True  # Valid click inside the circle

                    end_time = time.time()

                    task_time = end_time - start_time  # Time taken to click

                    return task_time, distance_to_center, True, target_x, target_y  # Return target coordinates for square
 
# Create a function to present the square click after the circle


def click_square():

    square_size = 25

    square_x, square_y = screen_width // 2 - square_size // 2, screen_height // 2 - square_size // 2

    screen.fill(WHITE)

    pygame.draw.rect(screen, GREEN, (square_x, square_y, square_size, square_size))

    pygame.display.flip()
 
    # Start timing and wait for square click

    start_time = time.time()

    clicked = False

    while not clicked:

        for event in pygame.event.get():

            if event.type == QUIT:

                pygame.quit()

                exit()

            elif event.type == MOUSEBUTTONDOWN:

                mouse_x, mouse_y = pygame.mouse.get_pos()

                if square_x <= mouse_x <= square_x + square_size and square_y <= mouse_y <= square_y + square_size:

                    clicked = True

                    end_time = time.time()

                    square_time = end_time - start_time

                    return square_time  # Time taken to click square
 
# Function to display the countdown timer (remaining trials)

def show_timer(remaining_trials, total_trials):

    font = pygame.font.SysFont(None, 36)

    timer_text = f"Remaining: {remaining_trials}/{total_trials} trials"

    text_surface = font.render(timer_text, True, BLACK)  # Timer text in black color

    screen.blit(text_surface, (10, 10))  # Position text at the top-left corner

    pygame.display.flip()
 
# Main experiment loop for each participant

def run_experiment(participant_id):

    trials = 320  # 10 blocks of 32 tasks

    results = []

    total_distance = 0

    total_accuracy = 0

    total_square_time = 0

    successful_trials = 0
 
    for trial_num in range(1, trials + 1):

        diameter, distance, direction = random.choice(task_combinations)

        task_time, distance_travelled, success, circle_x, circle_y = present_task(diameter, distance, direction)

        square_time = click_square()  # Perform square click after circle click
 
        # Update total distance, accuracy, and square click time

        total_distance += distance_travelled

        total_square_time += square_time

        if success:

            successful_trials += 1

        # Calculate accuracy and record data for the trial

        accuracy = success

        results.append([participant_id, diameter, distance, direction, task_time, distance_travelled, success, square_time])

        #TESTING SQLITE
        #cursor.execute("INSERT INTO Accuracy_Table (PK, Action) VALUES (1,'AMANDA')")
        #myconnection.commit()

        # Update countdown timer on the screen

        remaining_trials = trials - trial_num

        show_timer(remaining_trials, trials)
 
    accuracy_percentage = (successful_trials / trials) * 100

    average_square_time = total_square_time / trials




 
    # Display thank you message after completing all trials

    font = pygame.font.SysFont(None, 48)

    thank_you_text = "Thank you for participating!"

    text_surface = font.render(thank_you_text, True, BLUE)

    screen.blit(text_surface, (screen_width // 2 - text_surface.get_width() // 2, screen_height // 2))  # Center the text

    pygame.display.flip()
 
    # Wait for a few seconds to display the message before closing

    time.sleep(3)
 
    # Return trial data along with summary metrics

    return results, total_distance, accuracy_percentage, average_square_time
 
# Function to save the results to Excel

def save_results(participant_results):

    columns = ["Participant ID", "Diameter", "Distance", "Direction", "Task Time", "Distance Travelled", "Success", "Square Click Time"]

    df = pd.DataFrame(participant_results, columns=columns)
 
    # Adding total distance, accuracy, and average square time as summary row

    summary_columns = ["Participant ID", "Total Distance", "Accuracy (%)", "Average Square Click Time"]

    summary_data = []
 
    for participant in range(1, len(participant_results) + 1):

        participant_data = next((x for x in participant_results if x[0][0] == participant), None)

        if participant_data:

            total_distance = sum([x[5] for x in participant_data])

            accuracy = (sum([x[6] for x in participant_data]) / len(participant_data)) * 100

            avg_square_time = sum([x[7] for x in participant_data]) / len(participant_data)

            summary_data.append([participant, total_distance, accuracy, avg_square_time])
 
    summary_df = pd.DataFrame(summary_data, columns=summary_columns)

    with pd.ExcelWriter('fitts_law_results.xlsx') as writer:

        df.to_excel(writer, sheet_name="Trial Data", index=False)

        summary_df.to_excel(writer, sheet_name="Summary", index=False)
 
    # Open the Excel file automatically after saving

    if os.name == 'nt':  # For Windows

        os.startfile('fitts_law_results.xlsx')

    elif os.name == 'posix':  # For MacOS/Linux

        subprocess.call(['open', 'fitts_law_results.xlsx'])




 
# Main code to run the experiment for all participants

if __name__ == '__main__':

    for participant in participants:

        print(f"Running experiment for Participant {participant['id']}")

        results, total_distance, accuracy, average_square_time = run_experiment(participant['id'])

        participant_results.extend(results)

        print(f"Completed experiment for Participant {participant['id']}")
 

    # Save all results to an Excel file

    #save_results(participant_results)
 
    # End the pygame window

    pygame.quit()

 