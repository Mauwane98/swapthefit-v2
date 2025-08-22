
import sys
import os

print("--- Starting temp_check.py ---")
print(f"Python executable: {sys.executable}")
print(f"Current working directory: {os.getcwd()}")
print(f"Python path: {sys.path}")

try:
    from app import create_app
    print("Successfully imported create_app from app.")
except ImportError as e:
    print(f"Failed to import create_app: {e}")
except Exception as e:
    print(f"An unexpected error occurred during import: {e}")

print("--- Finished temp_check.py ---")
