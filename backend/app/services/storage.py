import aiofiles
from pathlib import Path
from datetime import datetime
import hashlib

from app.core.config import settings


class StorageService:
    def __init__(self):
        self.storage_path = settings.AUDIO_STORAGE_PATH
        self.storage_path.mkdir(parents=True, exist_ok=True)

    async def save_audio_file(
        self,
        file_content: bytes,
        original_filename: str
    ) -> tuple[str, str]:
        """
        Save audio file to local storage with atomic write operation

        Args:
            file_content: Raw bytes of the audio file
            original_filename: Original filename from upload (used for extension)

        Returns:
            tuple[str, str]: (unique_filename, absolute_file_path)

        Raises:
            ValueError: If file_content is empty or original_filename is invalid
            OSError: If file write fails
        """
        # Validate inputs
        if not file_content:
            raise ValueError("file_content cannot be empty")

        if not original_filename:
            raise ValueError("original_filename cannot be empty")

        # Generate deterministic unique filename
        # Format: YYYYMMDD_HHMMSS_<hash>.<ext>
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

        # Use first 1KB for hash to balance uniqueness and performance
        file_hash = hashlib.md5(file_content[:1024]).hexdigest()[:8]

        extension = Path(original_filename).suffix.lower()
        if not extension:
            raise ValueError("original_filename must have a file extension")

        unique_filename = f"{timestamp}_{file_hash}{extension}"
        file_path = self.storage_path / unique_filename

        # Check if file already exists (collision detection)
        if file_path.exists():
            # Add microseconds to ensure uniqueness
            timestamp_micro = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
            unique_filename = f"{timestamp_micro}_{file_hash}{extension}"
            file_path = self.storage_path / unique_filename

        # Write file atomically using temp file + rename pattern
        temp_path = file_path.with_suffix(f"{extension}.tmp")

        try:
            # Write to temporary file first
            async with aiofiles.open(temp_path, 'wb') as f:
                await f.write(file_content)

            # Atomic rename (on same filesystem)
            temp_path.rename(file_path)

            return unique_filename, str(file_path.absolute())

        except Exception as e:
            # Clean up temp file if it exists
            if temp_path.exists():
                temp_path.unlink()
            raise OSError(f"Failed to save audio file: {str(e)}") from e

    def delete_audio_file(self, filename: str) -> bool:
        """Delete audio file from storage"""
        file_path = self.storage_path / filename
        if file_path.exists():
            file_path.unlink()
            return True
        return False

    def get_file_path(self, filename: str) -> Path:
        """Get full path for audio file"""
        return self.storage_path / filename
