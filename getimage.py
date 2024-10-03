import PIL  # Mempertahankan import PIL jika digunakan di tempat lain dalam proyek
import random

def get(path):
    # Set the size of the image (you can modify this as needed)
    width = 40
    height = 20

    # Characters that can be used in the image
    characters = ['#', '.', '*', ' ']

    # Create a random 2D image array
    image = [[random.choice(characters) for _ in range(width)] for _ in range(height)]

    return image
