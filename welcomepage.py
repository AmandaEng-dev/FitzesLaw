import pygame
import sys
from datetime import datetime
import subprocess
import sqlite3
import os
import csv
from pathlib import Path

# Storage mode: choose 'db' or 'csv'
STORAGE_MODE = 'csv'  # Change to 'db' to use SQLite database

# Cross-platform path for CSV file in the same directory as this script
BASE_DIR = Path(__file__).resolve().parent
SCREENINGINFO_CSV_PATH = BASE_DIR / 'ScreeningInfo.csv'
DB_PATH = str(BASE_DIR / 'Fitzesdb.db')

if STORAGE_MODE == 'db':
    myconnection = sqlite3.connect(DB_PATH)
    cursor = myconnection.cursor()
    # Create ParticipantInfo table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ScreeningInfo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            participant_id INTEGER,
            handedness TEXT,
            mouse_usage_hours TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    myconnection.commit()
    # Get the next participant ID
    cursor.execute('SELECT MAX(participant_id) FROM ScreeningInfo')
    result = cursor.fetchone()
    participant_id = 1 if result[0] is None else result[0] + 1
else:
    # CSV mode: determine next_participant_id from CSV
    if not SCREENINGINFO_CSV_PATH.exists():
        with open(SCREENINGINFO_CSV_PATH, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([
                'id', 'participant_id', 'handedness', 'mouse_usage_hours', 'timestamp'
            ])
        participant_id = 1
    else:
        with open(SCREENINGINFO_CSV_PATH, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            participant_ids = [int(row['participant_id']) for row in reader if row['participant_id'].isdigit()]
            participant_id = max(participant_ids) + 1 if participant_ids else 1

# Initialize pygame
pygame.init()

# Set up the window
width, height = 900, 700
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Welcome to the experiment!")

# Set up fonts
font = pygame.font.Font(None, 36)
small_font = pygame.font.Font(None, 24)

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BUTTON_COLOR = (131, 151, 214)
BUTTON_HOVER_COLOR = (93, 103, 135)

consent_message1 = "Greetings, welcome to the Fitts' Law experiment!"
consent_message2  = "Experiment Directions:"
consent_message3  = """
In this experiment, you will be tasked with moving the cursor with a mouse to 
click the circles that vary by size and distance from the center of the screen. 
After clicking a circle, you will have to click the square located in the center of 
the screen to get the next circle to appear. This will be done until all 320 circles 
are clicked. This experiment should take approximately 10-15 minutes to complete. 
You may quit the experiment at any time if you feel uncomfortable. If you have any questions before, during, 
or after the experiment please feel free to contact Amanda Eng at amanda.eng@mnsu.edu.
"""
consent_message4 = "Consent of Participation:"
consent_message5 = """By clicking the 'I Agree' button below, you would be consenting to the 
collection of data that is produced from your participation in the 
experiment. This study is anonymous, your name will not be collected. 
The data will be used for non-commercial and academic purposes only. 
"""

# Button area
button_rect = pygame.Rect(width // 2 - 75, height - 75, 150, 50)


def welcome():
    now = datetime.now()
    current_datetime = now.strftime("%B %d %Y at %I:%M %p")

    with open("consent.txt", 'w') as file:
        file.write('You have constned to the collection of data that is produced from your participation in the experiment.\n This study is anonymous, your name will not be collected.\n The data will be used for non-commercial and academic purposes only.\n\n Your consent has been recorded on ' + current_datetime)
    

    # Display the consent message
    message = "Your consent has been recorded! Thank you for your participation!"
    screen.fill(WHITE)
    display_message(message, font, BLACK, screen, 20, height // 2 - 50)
    pygame.display.flip()

    # Wait 4 seconds before showing the next screen
    pygame.time.delay(2000)

    show_followup_screen()

def show_followup_screen():
    # Define button rectangles
    left_button = pygame.Rect(50, 120, 120, 40)
    right_button = pygame.Rect(200, 120, 120, 40)

    hour_buttons = [
        pygame.Rect(50, 250, 180, 40),  # 0–2 hours
        pygame.Rect(250, 250, 180, 40),  # 3–8 hours
        pygame.Rect(450, 250, 180, 40),  # 8+ hours
    ]

    finish_button = pygame.Rect(width // 2 - 190, 400, 400, 50)

    selected_hand = None
    selected_hours = None

    running = True
    while running:
        screen.fill(WHITE)

        # Questions
        draw_text("Are you left or right handed?", font, BLACK, screen, 50, 50)
        draw_text("How many hours per week do you use a mouse?", font, BLACK, screen, 50, 200)

        # Handedness buttons
        pygame.draw.rect(screen, BUTTON_HOVER_COLOR if selected_hand == "left" else BUTTON_COLOR, left_button)
        pygame.draw.rect(screen, BUTTON_HOVER_COLOR if selected_hand == "right" else BUTTON_COLOR, right_button)

        screen.blit(small_font.render("Left", True, WHITE), (left_button.x + 30, left_button.y + 10))
        screen.blit(small_font.render("Right", True, WHITE), (right_button.x + 30, right_button.y + 10))

        # Hour buttons
        hour_labels = ["0–2 Hours", "3–8 Hours", "8+ Hours"]
        for i, rect in enumerate(hour_buttons):
            color = BUTTON_HOVER_COLOR if selected_hours == i else BUTTON_COLOR
            pygame.draw.rect(screen, color, rect)
            screen.blit(small_font.render(hour_labels[i], True, WHITE), (rect.x + 20, rect.y + 10))

        # Finish button
        pygame.draw.rect(screen, BUTTON_COLOR, finish_button)
        finish_text = font.render("Finish and Go to Experiment", True, WHITE)
        screen.blit(finish_text, finish_text.get_rect(center=finish_button.center))

        # Event loop
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                if left_button.collidepoint(mx, my):
                    selected_hand = "left"
                elif right_button.collidepoint(mx, my):
                    selected_hand = "right"
                for i, rect in enumerate(hour_buttons):
                    if rect.collidepoint(mx, my):
                        selected_hours = i
                if finish_button.collidepoint(mx, my):
                    if selected_hand and selected_hours is not None:
                        mouse_usage_text = hour_labels[selected_hours]
                        timestamp = datetime.now().isoformat()
                        if STORAGE_MODE == 'db':
                            cursor.execute('''
                                INSERT INTO ScreeningInfo (
                                    participant_id, handedness, mouse_usage_hours
                                ) VALUES (?, ?, ?)
                            ''', (participant_id, selected_hand, mouse_usage_text))
                            myconnection.commit()
                        else:
                            # Write to CSV
                            with open(SCREENINGINFO_CSV_PATH, 'a', newline='', encoding='utf-8') as csvfile:
                                writer = csv.writer(csvfile)
                                # id is just the row number (count lines in file minus header)
                                with open(SCREENINGINFO_CSV_PATH, 'r', encoding='utf-8') as readfile:
                                    row_count = sum(1 for _ in readfile) - 1
                                writer.writerow([
                                    row_count + 1, participant_id, selected_hand, mouse_usage_text, timestamp
                                ])
                        pygame.quit()
                        subprocess.Popen([sys.executable, "FitzesLaw/test.py"])

        pygame.display.flip()
        pygame.time.Clock().tick(60)


# Function to draw text
def draw_text(text, font, color, surface, x, y, line_spacing=1.5):
    words = text.split('\n')
    y_offset = 0
    for word in words:
        text_surface = font.render(word, True, color)
        surface.blit(text_surface, (x, y + y_offset))
        y_offset += text_surface.get_height() * line_spacing  # Multiply by line_spacing factor

# Function to display a message in the Pygame window
def display_message(message, font, color, surface, x, y):
    text_surface = font.render(message, True, color)
    surface.blit(text_surface, (x, y))

# Main game loop
def game_loop():
    running = True
    while running:
        screen.fill(WHITE)

        # Draw consent text
        draw_text(consent_message1, font, BLACK, screen, 20, 20, 1.5)
        draw_text(consent_message2, small_font, BLACK, screen, 20, 80, 1.5)
        draw_text(consent_message3, small_font, BLACK, screen, 20, 120, 1.5)
        draw_text(consent_message4, small_font, BLACK, screen, 20, 350, 1.5)
        draw_text(consent_message5, small_font, BLACK, screen, 20, 390, 1.5)

        # Draw button
        mouse_x, mouse_y = pygame.mouse.get_pos()
        if button_rect.collidepoint(mouse_x, mouse_y):
            pygame.draw.rect(screen, BUTTON_HOVER_COLOR, button_rect)
        else:
            pygame.draw.rect(screen, BUTTON_COLOR, button_rect)

        # Draw "I Agree" text on the button
        button_text = font.render("I Agree", True, WHITE)
        screen.blit(button_text, (button_rect.x + 40, button_rect.y + 10))

        # Check for events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if button_rect.collidepoint(mouse_x, mouse_y):
                    welcome()  # Call the function when the button is clicked

        pygame.display.flip()
        pygame.time.Clock().tick(60)

# Start the game loop
game_loop()

