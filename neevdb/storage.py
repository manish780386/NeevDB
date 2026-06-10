"""
NeevDB - Storage Layer
Handles all file reading and writing operations.
"""

import json
import os


class Storage:
    """Manages reading and writing the database to a JSON file."""

    def __init__(self, filepath: str):
        """
        Initialize storage with a file path.

        Args:
            filepath: Path to the JSON file where data will be stored.
        """
        self.filepath = filepath
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        """Create the database file if it does not exist."""
        if not os.path.exists(self.filepath):
            self._write({"tables": {}})

    def read(self) -> dict:
        """
        Read all data from the database file.

        Returns:
            A dictionary containing all database tables and records.
        """
        with open(self.filepath, "r", encoding="utf-8") as file:
            return json.load(file)

    def _write(self, data: dict):
        """
        Write data to the database file.

        Args:
            data: The complete database dictionary to write.
        """
        with open(self.filepath, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=2, ensure_ascii=False)

    def save(self, data: dict):
        """
        Save updated data back to the database file.

        Args:
            data: The updated database dictionary to persist.
        """
        self._write(data)