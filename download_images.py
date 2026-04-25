#!/usr/bin/env python3
"""Download animal images from Wikipedia for each animal."""

import json
import os
import urllib.request
import urllib.parse
import time

from animals import ANIMALS

# Wikipedia article overrides for animals whose name doesn't match their article
WIKI_OVERRIDES = {
    'Hippo': 'Hippopotamus',
    'Urchin': 'Sea urchin',
    'X-ray Fish': 'X-ray tetra',
    'Rhino': 'Rhinoceros',
    'Turkey': 'Turkey (bird)',
    'Bee': 'Honey bee',
    'Ant': 'Ant',
    'Fish': 'Fish',
    'Shark': 'Shark',
    'Gecko': 'Gecko',
}

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(SCRIPT_DIR, 'images')
os.makedirs(IMG_DIR, exist_ok=True)


def get_wikipedia_image_url(article_title, use_thumbnail=False):
    """Get image URL from a Wikipedia article via the REST API."""
    encoded = urllib.parse.quote(article_title)
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded}"
    req = urllib.request.Request(url, headers={'User-Agent': 'BabyAnimalsApp/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            if not use_thumbnail and 'originalimage' in data:
                return data['originalimage']['source']
            if 'thumbnail' in data:
                return data['thumbnail']['source']
    except Exception as e:
        print(f"  API error: {e}")
    return None


def download_image(url, dest_path):
    """Download an image from URL to dest_path."""
    req = urllib.request.Request(url, headers={'User-Agent': 'BabyAnimalsApp/1.0'})
    with urllib.request.urlopen(req, timeout=30) as resp:
        with open(dest_path, 'wb') as f:
            f.write(resp.read())


def safe_filename(name):
    """Convert animal name to a safe filename."""
    return name.lower().replace(' ', '_').replace('-', '_')


def main():
    all_animals = []
    for letter, entries in sorted(ANIMALS.items()):
        for animal_name, _color in entries:
            all_animals.append((letter, animal_name))

    for letter, animal_name in all_animals:
        fname = safe_filename(animal_name)
        dest = os.path.join(IMG_DIR, f"{fname}.jpg")
        if os.path.exists(dest):
            print(f"  {animal_name} — already exists, skipping")
            continue

        wiki_name = WIKI_OVERRIDES.get(animal_name, animal_name)
        print(f"  {animal_name} — fetching from '{wiki_name}'...")

        # Try original first, fall back to thumbnail
        img_url = get_wikipedia_image_url(wiki_name, use_thumbnail=False)

        if img_url and img_url.lower().endswith('.svg'):
            img_url = get_wikipedia_image_url(wiki_name, use_thumbnail=True)

        if not img_url:
            print(f"    No image found")
            continue

        try:
            download_image(img_url, dest)
            print(f"    Saved {fname}.jpg")
        except urllib.error.HTTPError as e:
            if e.code == 429:
                print(f"    Rate limited, trying thumbnail...")
                img_url = get_wikipedia_image_url(wiki_name, use_thumbnail=True)
                if img_url:
                    try:
                        download_image(img_url, dest)
                        print(f"    Saved {fname}.jpg (thumbnail)")
                    except Exception as e2:
                        print(f"    Thumbnail also failed: {e2}")
            else:
                print(f"    Download failed: {e}")
        except Exception as e:
            print(f"    Download failed: {e}")

        time.sleep(1)

    print("\nDone with images!")


def download_voice():
    """Download piper TTS voice model if not present."""
    voice_dir = os.path.join(SCRIPT_DIR, 'voice')
    os.makedirs(voice_dir, exist_ok=True)

    model_path = os.path.join(voice_dir, 'en_US-lessac-medium.onnx')
    config_path = model_path + '.json'

    base_url = 'https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium'

    for path, filename in [(model_path, 'en_US-lessac-medium.onnx'), (config_path, 'en_US-lessac-medium.onnx.json')]:
        if os.path.exists(path):
            print(f"  {filename} — already exists, skipping")
            continue
        url = f"{base_url}/{filename}"
        print(f"  Downloading {filename}...")
        req = urllib.request.Request(url, headers={'User-Agent': 'BabyAnimalsApp/1.0'})
        with urllib.request.urlopen(req, timeout=120) as resp:
            with open(path, 'wb') as f:
                f.write(resp.read())
        print(f"  Saved {filename}")


if __name__ == '__main__':
    main()
    print("\nDownloading voice model...")
    download_voice()
