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
        Save audio file to local storage
        Returns: (filename, file_path)
        """
        # Generate unique filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        file_hash = hashlib.md5(file_content[:1024]).hexdigest()[:8]
        extension = Path(original_filename).suffix

        unique_filename = f"{timestamp}_{file_hash}{extension}"
        file_path = self.storage_path / unique_filename

        # Save file asynchronously
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(file_content)

        return unique_filename, str(file_path)

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
