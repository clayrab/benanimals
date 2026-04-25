#!/usr/bin/env python3
"""Baby Animal Keyboard - Fullscreen app for toddlers to bang on keyboard"""

import pygame
import subprocess
import time
import os

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


SPEECH_FADEOUT_MS = 150  # how quickly an interrupted phrase fades out


def make_speaker(audio_cache):
    """Build a speak(text) callable that fades any prior phrase when interrupted."""
    sounds = {}
    for text, path in audio_cache.items():
        if not os.path.exists(path):
            continue
        try:
            sounds[text] = pygame.mixer.Sound(path)
        except Exception as e:
            print(f"Could not load sound {path}: {e}")
    n_channels = 20
    pygame.mixer.set_num_channels(n_channels)
    channels = [pygame.mixer.Channel(i) for i in range(n_channels)]
    state = {'idx': -1}

    def speak(text):
        sound = sounds.get(text)
        if not sound:
            return
        state['idx'] = (state['idx'] + 1) % n_channels
        target = channels[state['idx']]
        for ch in channels:
            if ch is not target and ch.get_busy():
                ch.fadeout(SPEECH_FADEOUT_MS)
        target.stop()
        target.set_volume(1.0)
        target.play(sound)

    return speak


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


FADE_DURATION = 2.4  # seconds for the letter to fade out


def scale_to_screen(image, screen):
    if not image:
        return None
    width, height = screen.get_size()
    max_w, max_h = int(width * 0.9), int(height * 0.9)
    iw, ih = image.get_size()
    s = min(max_w / iw, max_h / ih)
    return pygame.transform.smoothscale(image, (int(iw * s), int(ih * s)))


def render_frame(screen, scaled_image, letter, color, alpha, big_font):
    """Draw background, the animal image, and the fading letter overlay."""
    screen.fill((240, 248, 255))
    width, height = screen.get_size()
    if scaled_image:
        screen.blit(scaled_image, scaled_image.get_rect(center=(width // 2, height // 2)))
    if alpha > 0 and letter:
        text = big_font.render(letter.upper(), True, color)
        text.set_alpha(alpha)
        screen.blit(text, text.get_rect(center=(width // 2, height // 2)))
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
    pygame.mixer.init()

    info = pygame.display.Info()
    screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
    pygame.display.set_caption('Baby Animals')
    pygame.mouse.set_visible(False)

    images = load_images()
    print(f"Loaded {len(images)} animal images")

    audio_cache = generate_audio_cache()
    speak = make_speaker(audio_cache)

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
    speak("Press any letter!")

    clock = pygame.time.Clock()
    running = True
    last_activity = time.time()
    timeout = 600
    exit_combo_start = None

    cycle_indices = {letter: 0 for letter in ANIMALS}
    letters_in_order = list(ANIMALS.keys())
    fallback_letter_idx = 0

    big_font = pygame.font.Font(None, min(info.current_w, info.current_h))
    current_letter = None
    current_color = None
    current_scaled_image = None
    letter_fade_start = None
    last_drawn_alpha = -1

    def show_animal(letter, animal_name, color):
        nonlocal current_letter, current_color, current_scaled_image, letter_fade_start, last_drawn_alpha
        current_letter = letter
        current_color = color
        current_scaled_image = scale_to_screen(images.get(animal_name), screen)
        letter_fade_start = time.time()
        last_drawn_alpha = -1

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
                        entries = ANIMALS[key_name]
                        idx = cycle_indices[key_name]
                        animal_name, color = entries[idx]
                        cycle_indices[key_name] = (idx + 1) % len(entries)
                        show_animal(key_name, animal_name, color)
                        speak(f"{key_name.upper()} is for {animal_name}")
                    exit_combo_start = None
                elif len(key_name) == 1 and key_name.isdigit():
                    digit = int(key_name)
                    draw_number(screen, digit)
                    speak(NUMBER_WORDS[digit])
                    current_letter = None
                    exit_combo_start = None
                else:
                    letter = letters_in_order[fallback_letter_idx]
                    fallback_letter_idx = (fallback_letter_idx + 1) % len(letters_in_order)
                    entries = ANIMALS[letter]
                    idx = cycle_indices[letter]
                    animal_name, color = entries[idx]
                    cycle_indices[letter] = (idx + 1) % len(entries)
                    show_animal(letter, animal_name, color)
                    speak(f"{letter.upper()} is for {animal_name}")
                    exit_combo_start = None

            elif event.type == pygame.KEYUP:
                key_name = pygame.key.name(event.key).lower()
                if key_name == 'q':
                    exit_combo_start = None

        if current_letter is not None:
            elapsed = time.time() - letter_fade_start
            alpha = max(0, int(255 * (1 - elapsed / FADE_DURATION)))
            if alpha != last_drawn_alpha:
                render_frame(screen, current_scaled_image, current_letter, current_color, alpha, big_font)
                last_drawn_alpha = alpha

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
