#!/usr/bin/env python3
"""Baby Animal Keyboard - Fullscreen app for toddlers to bang on keyboard"""

import pygame
import subprocess
import time
import os
import random

# Animal data: letter -> (animal_name, color)
ANIMALS = {
    'a': ('Alligator', (0, 100, 0)),
    'b': ('Bear', (139, 69, 19)),
    'c': ('Cat', (255, 165, 0)),
    'd': ('Dog', (210, 180, 140)),
    'e': ('Elephant', (128, 128, 128)),
    'f': ('Frog', (0, 255, 0)),
    'g': ('Giraffe', (255, 215, 0)),
    'h': ('Horse', (139, 90, 43)),
    'i': ('Iguana', (50, 205, 50)),
    'j': ('Jaguar', (255, 200, 0)),
    'k': ('Kangaroo', (210, 150, 100)),
    'l': ('Lion', (255, 180, 0)),
    'm': ('Monkey', (160, 82, 45)),
    'n': ('Newt', (255, 100, 0)),
    'o': ('Owl', (180, 160, 140)),
    'p': ('Penguin', (0, 0, 0)),
    'q': ('Quail', (165, 120, 80)),
    'r': ('Rabbit', (255, 255, 255)),
    's': ('Snake', (0, 128, 0)),
    't': ('Tiger', (255, 140, 0)),
    'u': ('Urchin', (128, 0, 128)),
    'v': ('Vulture', (80, 80, 80)),
    'w': ('Whale', (0, 0, 200)),
    'x': ('X-ray Fish', (200, 200, 255)),
    'y': ('Yak', (100, 70, 50)),
    'z': ('Zebra', (50, 50, 50)),
}

def speak(text):
    """Speak text using espeak"""
    try:
        subprocess.Popen(['espeak', '-s', '120', text], 
                        stdout=subprocess.DEVNULL, 
                        stderr=subprocess.DEVNULL)
    except:
        pass

def draw_animal(screen, letter, animal_name, color):
    """Draw the letter and animal name on screen"""
    screen.fill((240, 248, 255))  # Light blue background
    
    width, height = screen.get_size()
    
    # Draw big letter
    font_big = pygame.font.Font(None, min(width, height) // 2)
    letter_surface = font_big.render(letter.upper(), True, color)
    letter_rect = letter_surface.get_rect(center=(width // 2, height // 3))
    screen.blit(letter_surface, letter_rect)
    
    # Draw animal name
    font_medium = pygame.font.Font(None, min(width, height) // 6)
    name_surface = font_medium.render(animal_name, True, color)
    name_rect = name_surface.get_rect(center=(width // 2, height * 2 // 3))
    screen.blit(name_surface, name_rect)
    
    # Draw some simple decorations (circles as "bubbles")
    for _ in range(10):
        x = random.randint(50, width - 50)
        y = random.randint(50, height - 50)
        r = random.randint(10, 40)
        pygame.draw.circle(screen, (*color, 100), (x, y), r, 3)
    
    pygame.display.flip()

def main():
    # Set environment for better keyboard grab on X11
    os.environ.setdefault('SDL_VIDEO_X11_DGAMOUSE', '0')
    
    pygame.init()
    pygame.mixer.quit()  # We don't need sound mixer
    
    # Get display info and go fullscreen
    info = pygame.display.Info()
    screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
    pygame.display.set_caption('Baby Animals')
    pygame.mouse.set_visible(False)
    
    # IMPORTANT: Grab all input to prevent WM shortcuts
    pygame.event.set_grab(True)
    
    # Initial screen
    screen.fill((240, 248, 255))
    font = pygame.font.Font(None, 80)
    text = font.render("Press any letter key!", True, (100, 100, 200))
    rect = text.get_rect(center=(info.current_w // 2, info.current_h // 2))
    screen.blit(text, rect)
    
    # Show exit instructions smaller at bottom
    font_small = pygame.font.Font(None, 30)
    exit_text = font_small.render("Parent exit: Hold Ctrl+Shift+Q for 2 seconds", True, (150, 150, 150))
    exit_rect = exit_text.get_rect(center=(info.current_w // 2, info.current_h - 50))
    screen.blit(exit_text, exit_rect)
    
    pygame.display.flip()
    
    speak("Press any letter!")
    
    clock = pygame.time.Clock()
    running = True
    last_activity = time.time()
    timeout = 600  # 10 minute timeout
    
    # For tracking held exit combo
    exit_combo_start = None
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            elif event.type == pygame.KEYDOWN:
                last_activity = time.time()
                key_name = pygame.key.name(event.key).lower()
                
                # Check for exit combo: Ctrl+Shift+Q held for 2 seconds
                mods = pygame.key.get_mods()
                if key_name == 'q' and (mods & pygame.KMOD_CTRL) and (mods & pygame.KMOD_SHIFT):
                    if exit_combo_start is None:
                        exit_combo_start = time.time()
                elif key_name == 'escape' and (mods & pygame.KMOD_CTRL) and (mods & pygame.KMOD_SHIFT):
                    # Alternative: Ctrl+Shift+Escape
                    running = False
                elif len(key_name) == 1 and key_name.isalpha():
                    # It's a letter!
                    if key_name in ANIMALS:
                        animal_name, color = ANIMALS[key_name]
                        draw_animal(screen, key_name, animal_name, color)
                        speak(f"{key_name.upper()} is for {animal_name}")
                    exit_combo_start = None
                else:
                    exit_combo_start = None
            
            elif event.type == pygame.KEYUP:
                key_name = pygame.key.name(event.key).lower()
                if key_name == 'q':
                    exit_combo_start = None
        
        # Check if exit combo held long enough
        if exit_combo_start and (time.time() - exit_combo_start) > 2.0:
            running = False
        
        # Timeout check
        if time.time() - last_activity > timeout:
            running = False
        
        clock.tick(30)
    
    # Cleanup
    pygame.event.set_grab(False)
    pygame.quit()
    print("Baby Animals closed. Goodbye!")

if __name__ == '__main__':
    main()
