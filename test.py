import sqlite3
import pygame
import random
import time
from pygame.locals import *

# Database setup
myconnection = sqlite3.connect("/Users/amanda_1/Desktop/Fitzesdb.db")
cursor = myconnection.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS TrialData (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        participant_id INTEGER,
        diameter INTEGER,
        distance INTEGER,
        direction TEXT,
        task_time REAL,
        distance_travelled REAL,
        hit INTEGER,
        miss INTEGER,
        square_time REAL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS ParticipantSummary (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        participant_id INTEGER,
        total_distance REAL,
        hits INTEGER,
        misses INTEGER,
        accuracy_percentage REAL,
        average_square_time REAL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
''')

cursor.execute('SELECT MAX(participant_id) FROM ParticipantSummary')
result = cursor.fetchone()
next_participant_id = 1 if result[0] is None else result[0] + 1
myconnection.commit()

# Pygame setup
pygame.init()
screen_width, screen_height = 1024, 768
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Fitts' Law Experiment")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 200, 0)
BLUE = (0, 0, 255)

# Experiment settings
circle_diameters = [40, 50, 70, 100]
distances = [100, 200, 300, 400]
directions = ['left', 'right']
task_combinations = [(d, dist, dir) for d in circle_diameters for dist in distances for dir in directions]
random.shuffle(task_combinations)

# Progress bar
def show_progress_bar(current_trial, total_trials):
    bar_x = 10
    bar_y = 10
    bar_width = 300
    bar_height = 25
    progress = current_trial / total_trials

    pygame.draw.rect(screen, (200, 200, 200), (bar_x, bar_y, bar_width, bar_height))
    pygame.draw.rect(screen, (135, 206, 250), (bar_x, bar_y, int(bar_width * progress), bar_height))

    font = pygame.font.SysFont(None, 24)
    progress_text = f"Progress: {current_trial}/{total_trials} Trials"
    text_surface = font.render(progress_text, True, BLACK)
    screen.blit(text_surface, (bar_x + 10, bar_y + bar_height + 5))

# Square click
def click_square(trial_num, total_trials):
    square_size = 20
    square_x = screen_width // 2 - square_size // 2
    square_y = screen_height // 2 - square_size // 2

    screen.fill(WHITE)
    pygame.draw.rect(screen, GREEN, (square_x, square_y, square_size, square_size))
    show_progress_bar(trial_num, total_trials)
    pygame.display.flip()

    start_time = time.time()
    clicked = False
    while not clicked:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                exit()
            elif event.type == MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                if square_x <= mx <= square_x + square_size and square_y <= my <= square_y + square_size:
                    clicked = True
                    return time.time() - start_time

# Circle click
def present_task(diameter, distance, direction, trial_num, total_trials):
    circle_radius = diameter // 2
    center_x, center_y = screen_width // 2, screen_height // 2

    if direction == 'left':
        target_x = center_x - distance
    else:
        target_x = center_x + distance

    target_y = center_y

    screen.fill(WHITE)
    pygame.draw.circle(screen, RED, (target_x, target_y), circle_radius)
    show_progress_bar(trial_num, total_trials)
    pygame.display.flip()

    start_time = time.time()
    clicked = False
    hit = miss = False

    while not clicked:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                exit()
            elif event.type == MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                dist_to_center = ((mx - target_x) ** 2 + (my - target_y) ** 2) ** 0.5
                if dist_to_center <= circle_radius:
                    hit = True
                    clicked = True
                else:
                    miss = True
                return time.time() - start_time, dist_to_center, hit, miss, target_x, target_y

# Main experiment
def run_experiment(participant_id):
    trials = 320  # You can change this to 320
    total_distance = hits = misses = total_square_time = 0

    for trial_num in range(1, trials + 1):
        square_time = click_square(trial_num, trials)
        diameter, distance, direction = random.choice(task_combinations)

        while True:
            task_time, distance_travelled, hit, miss, circle_x, circle_y = present_task(
                diameter, distance, direction, trial_num, trials
            )

            total_distance += distance_travelled
            if hit:
                hits += 1
                break
            if miss:
                misses += 1

        total_square_time += square_time

        cursor.execute('''
            INSERT INTO TrialData (
                participant_id, diameter, distance, direction,
                task_time, distance_travelled, hit, miss, square_time
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (participant_id, diameter, distance, direction,
              task_time, distance_travelled, hit, miss, square_time))
        myconnection.commit()

    total_attempts = hits + misses
    accuracy_percentage = (hits / total_attempts) * 100 if total_attempts > 0 else 0
    average_square_time = total_square_time / trials

    cursor.execute('''
        INSERT INTO ParticipantSummary (
            participant_id, total_distance, hits, misses,
            accuracy_percentage, average_square_time
        ) VALUES (?, ?, ?, ?, ?, ?)
    ''', (participant_id, total_distance, hits, misses,
          accuracy_percentage, average_square_time))
    myconnection.commit()

    font = pygame.font.SysFont(None, 48)
    text_surface = font.render("Thank you for participating! Your consent has been recorded.", True, BLUE)
    screen.fill(WHITE)
    screen.blit(text_surface, (screen_width // 2 - text_surface.get_width() // 2, screen_height // 2))
    pygame.display.flip()
    time.sleep(3)

    pygame.quit()
    return

# Run experiment
if __name__ == '__main__':
    try:
        print(f"Starting experiment for Participant {next_participant_id}")
        run_experiment(next_participant_id)
        print(f"Experiment completed for Participant {next_participant_id}")
    except Exception as e:
        print("Error:", e)
    finally:
        myconnection.close()
        exit()
