import os

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

OUTPUT_DIR = os.path.join(ROOT_DIR, os.pardir, "outputs")
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

