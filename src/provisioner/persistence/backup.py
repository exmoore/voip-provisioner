"""Backup utilities for YAML files."""

import shutil
from datetime import datetime
from pathlib import Path


class BackupManager:
    """Manages backups of YAML files."""

    def __init__(self, backup_dir: Path, max_backups: int = 10):
        """Initialize backup manager.

        Args:
            backup_dir: Directory to store backups
            max_backups: Maximum number of backups to keep per file
        """
        self.backup_dir = Path(backup_dir)
        self.max_backups = max_backups
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(self, file_path: Path) -> Path:
        """Create a timestamped backup of a file.

        Args:
            file_path: Path to file to backup

        Returns:
            Path to created backup file
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Cannot backup non-existent file: {file_path}")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
        backup_path = self.backup_dir / backup_name

        shutil.copy2(file_path, backup_path)

        # Cleanup old backups
        self._cleanup_old_backups(file_path.stem, file_path.suffix)

        return backup_path

    def _cleanup_old_backups(self, file_stem: str, file_suffix: str) -> None:
        """Remove old backups, keeping only the most recent ones.

        Args:
            file_stem: Base name of the file (without extension)
            file_suffix: File extension
        """
        # Find all backups for this file
        pattern = f"{file_stem}_*{file_suffix}"
        backups = sorted(self.backup_dir.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)

        # Remove old backups beyond max_backups
        for old_backup in backups[self.max_backups:]:
            old_backup.unlink()

    def restore_backup(self, backup_path: Path, target_path: Path) -> None:
        """Restore a backup file to target location.

        Args:
            backup_path: Path to backup file
            target_path: Path to restore to
        """
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_path}")

        shutil.copy2(backup_path, target_path)

    def list_backups(self, file_stem: str, file_suffix: str) -> list[Path]:
        """List all backups for a given file.

        Args:
            file_stem: Base name of the file
            file_suffix: File extension

        Returns:
            List of backup paths, sorted by modification time (newest first)
        """
        pattern = f"{file_stem}_*{file_suffix}"
        backups = sorted(
            self.backup_dir.glob(pattern),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        return backups
