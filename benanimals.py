#!/usr/bin/env python3
"""Baby Animal Keyboard - Fullscreen app for toddlers to bang on keyboard"""

import pygame
import subprocess
import threading
import time
import os
import random

from animals import ANIMALS

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(SCRIPT_DIR, 'images')
AUDIO_DIR = os.path.join(SCRIPT_DIR, 'audio_cache')

VOICE_MODEL = os.path.join(SCRIPT_DIR, 'voice', 'en_US-lessac-medium.onnx')


def generate_audio_cache():
    """Pre-generate WAV files for all animal phrases."""
    os.makedirs(AUDIO_DIR, exist_ok=True)
    phrases = {}
    for letter, entries in ANIMALS.items():
        for animal_name, _color in entries:
            text = f"{letter.upper()} is for {animal_name}"
            key = safe_filename(f"{letter}_{animal_name}")
            phrases[text] = key
    # Add number phrases
    number_words = ['Zero', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine']
    for i, word in enumerate(number_words):
        phrases[word] = f"number_{i}"
    # Add misc phrases
    phrases["uh oh!"] = "uh_oh"
    phrases["Press any letter!"] = "intro"

    # Find which phrases need generating
    to_generate = {}
    for text, key in phrases.items():
        path = os.path.join(AUDIO_DIR, f"{key}.wav")
        if not os.path.exists(path):
            to_generate[text] = key

    if to_generate:
        print(f"Generating {len(to_generate)} audio clips...")
        # Feed all texts to a single piper process, one per line
        for text, key in to_generate.items():
            path = os.path.join(AUDIO_DIR, f"{key}.wav")
            try:
                proc = subprocess.run(
                    ['piper', '--model', VOICE_MODEL, '--output_file', path],
                    input=text.encode(),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=30,
                )
            except Exception as e:
                print(f"Failed to generate audio for '{text}': {e}")
        print("Audio generation complete.")

    return {text: os.path.join(AUDIO_DIR, f"{key}.wav") for text, key in phrases.items()}


def speak(text, audio_cache):
    """Play pre-generated audio in a background thread."""
    path = audio_cache.get(text)
    if not path or not os.path.exists(path):
        return
    def _play():
        try:
            subprocess.run(
                ['aplay', '-q', path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=10,
            )
        except:
            pass
    threading.Thread(target=_play, daemon=True).start()


def safe_filename(name):
    return name.lower().replace(' ', '_').replace('-', '_')


def load_images():
    """Pre-load all animal images keyed by animal name."""
    images = {}
    for letter, entries in ANIMALS.items():
        for animal_name, _color in entries:
            fname = safe_filename(animal_name)
            path = os.path.join(IMG_DIR, f"{fname}.jpg")
            if os.path.exists(path):
                try:
                    images[animal_name] = pygame.image.load(path).convert()
                except Exception as e:
                    print(f"Could not load {path}: {e}")
    return images


def draw_animal(screen, letter, animal_name, color, image=None):
    """Draw the animal image, letter, and name on screen"""
    screen.fill((240, 248, 255))  # Light blue background

    width, height = screen.get_size()

    if image:
        # Scale image to fit top ~65% of screen, preserving aspect ratio
        max_img_w = int(width * 0.8)
        max_img_h = int(height * 0.6)
        img_w, img_h = image.get_size()
        scale = min(max_img_w / img_w, max_img_h / img_h)
        new_w = int(img_w * scale)
        new_h = int(img_h * scale)
        scaled = pygame.transform.smoothscale(image, (new_w, new_h))
        img_rect = scaled.get_rect(center=(width // 2, int(height * 0.35)))
        screen.blit(scaled, img_rect)

        # Draw "L is for Animal" below the image
        font_name = pygame.font.Font(None, min(width, height) // 10)
        combo_text = f"{letter.upper()} is for {animal_name}"
        combo_surface = font_name.render(combo_text, True, color)
        combo_rect = combo_surface.get_rect(center=(width // 2, int(height * 0.78)))
        screen.blit(combo_surface, combo_rect)
    else:
        # Fallback: text-only
        font_big = pygame.font.Font(None, min(width, height) // 2)
        letter_surface = font_big.render(letter.upper(), True, color)
        letter_rect = letter_surface.get_rect(center=(width // 2, height // 3))
        screen.blit(letter_surface, letter_rect)

        font_medium = pygame.font.Font(None, min(width, height) // 6)
        name_surface = font_medium.render(animal_name, True, color)
        name_rect = name_surface.get_rect(center=(width // 2, height * 2 // 3))
        screen.blit(name_surface, name_rect)

    pygame.display.flip()


NUMBER_WORDS = ['Zero', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine']
NUMBER_COLORS = [
    (200, 50, 50), (50, 50, 200), (50, 180, 50), (200, 150, 0), (180, 50, 180),
    (0, 160, 160), (220, 120, 30), (140, 80, 160), (200, 80, 80), (60, 130, 60),
]


def draw_number(screen, digit):
    """Draw a number and its word on screen."""
    screen.fill((240, 248, 255))
    width, height = screen.get_size()
    color = NUMBER_COLORS[digit]

    font_big = pygame.font.Font(None, min(width, height) // 2)
    digit_surface = font_big.render(str(digit), True, color)
    digit_rect = digit_surface.get_rect(center=(width // 2, height // 3))
    screen.blit(digit_surface, digit_rect)

    font_medium = pygame.font.Font(None, min(width, height) // 6)
    word_surface = font_medium.render(NUMBER_WORDS[digit], True, color)
    word_rect = word_surface.get_rect(center=(width // 2, height * 2 // 3))
    screen.blit(word_surface, word_rect)

    pygame.display.flip()


def main():
    os.environ.setdefault('SDL_VIDEO_X11_DGAMOUSE', '0')

    pygame.init()
    pygame.mixer.quit()

    info = pygame.display.Info()
    screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
    pygame.display.set_caption('Baby Animals')
    pygame.mouse.set_visible(False)

    images = load_images()
    print(f"Loaded {len(images)} animal images")

    audio_cache = generate_audio_cache()

    pygame.event.set_grab(True)

    # Initial screen
    screen.fill((240, 248, 255))
    font = pygame.font.Font(None, 80)
    text = font.render("Press any letter key!", True, (100, 100, 200))
    rect = text.get_rect(center=(info.current_w // 2, info.current_h // 2))
    screen.blit(text, rect)

    font_small = pygame.font.Font(None, 30)
    exit_text = font_small.render("Parent exit: Hold Ctrl+Shift+Q for 2 seconds", True, (150, 150, 150))
    exit_rect = exit_text.get_rect(center=(info.current_w // 2, info.current_h - 50))
    screen.blit(exit_text, exit_rect)

    pygame.display.flip()
    speak("Press any letter!", audio_cache)

    clock = pygame.time.Clock()
    running = True
    last_activity = time.time()
    timeout = 600
    exit_combo_start = None

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                last_activity = time.time()
                key_name = pygame.key.name(event.key).lower()

                mods = pygame.key.get_mods()
                if key_name == 'q' and (mods & pygame.KMOD_CTRL) and (mods & pygame.KMOD_SHIFT):
                    if exit_combo_start is None:
                        exit_combo_start = time.time()
                elif key_name == 'escape' and (mods & pygame.KMOD_CTRL) and (mods & pygame.KMOD_SHIFT):
                    running = False
                elif len(key_name) == 1 and key_name.isalpha():
                    if key_name in ANIMALS:
                        animal_name, color = random.choice(ANIMALS[key_name])
                        draw_animal(screen, key_name, animal_name, color, images.get(animal_name))
                        speak(f"{key_name.upper()} is for {animal_name}", audio_cache)
                    exit_combo_start = None
                elif len(key_name) == 1 and key_name.isdigit():
                    digit = int(key_name)
                    draw_number(screen, digit)
                    speak(NUMBER_WORDS[digit], audio_cache)
                    exit_combo_start = None
                else:
                    speak("uh oh!", audio_cache)
                    exit_combo_start = None

            elif event.type == pygame.KEYUP:
                key_name = pygame.key.name(event.key).lower()
                if key_name == 'q':
                    exit_combo_start = None

        if exit_combo_start and (time.time() - exit_combo_start) > 2.0:
            running = False

        if time.time() - last_activity > timeout:
            running = False

        clock.tick(30)

    pygame.event.set_grab(False)
    pygame.quit()
    print("Baby Animals closed. Goodbye!")

if __name__ == '__main__':
    main()
