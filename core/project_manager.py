"""
ClipGenius - Project Manager
Handles project folder structure and organization
"""
import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, List
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.constants import APP_NAME, OUTPUT_BASE_DIR


class ProjectManager:
    """Manages project folders and organization."""
    
    def __init__(self, base_dir: str = None):
        """Initialize project manager.
        
        Args:
            base_dir: Base directory for all projects. Defaults to Desktop/ClipGenius
        """
        self.base_dir = Path(base_dir) if base_dir else Path(OUTPUT_BASE_DIR)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.current_project = None
    
    def create_project(self, name: str, video_path: str = None) -> dict:
        """Create a new project with folder structure.
        
        Args:
            name: Project name
            video_path: Optional path to source video
            
        Returns:
            Project metadata dictionary
        """
        # Sanitize project name
        safe_name = self._sanitize_name(name)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        project_folder = f"{safe_name}_{timestamp}"
        
        project_path = self.base_dir / project_folder
        
        # Create folder structure
        folders = {
            'root': project_path,
            'source': project_path / 'source',
            'clips': project_path / 'clips',
            'exports': project_path / 'exports',
            'audio': project_path / 'audio'
        }
        
        for folder in folders.values():
            folder.mkdir(parents=True, exist_ok=True)
        
        # Create project metadata
        metadata = {
            'name': name,
            'folder_name': project_folder,
            'created_at': datetime.now().isoformat(),
            'status': 'created',
            'source_video': None,
            'clips': [],
            'settings': {
                'min_duration': 60,
                'max_duration': 120,
                'enable_captions': False,
                'enable_music': False,
                'music_volume': 30,
                'enhance_video': True,
                'enhance_audio': True
            }
        }
        
        # Copy source video if provided
        if video_path and os.path.exists(video_path):
            video_name = os.path.basename(video_path)
            dest_path = folders['source'] / video_name
            shutil.copy2(video_path, dest_path)
            metadata['source_video'] = str(dest_path)
        
        # Save metadata
        self._save_metadata(project_path, metadata)
        
        self.current_project = metadata
        return metadata
    
    def load_project(self, project_path: str) -> dict:
        """Load an existing project.
        
        Args:
            project_path: Path to project folder
            
        Returns:
            Project metadata dictionary
        """
        project_path = Path(project_path)
        metadata_file = project_path / 'project.json'
        
        if not metadata_file.exists():
            raise FileNotFoundError(f"Project metadata not found: {metadata_file}")
        
        with open(metadata_file, 'r', encoding='utf-8') as f:
            self.current_project = json.load(f)
        
        return self.current_project
    
    def save_project(self, metadata: dict = None) -> bool:
        """Save current project metadata.
        
        Args:
            metadata: Optional metadata to save. Uses current project if not provided.
            
        Returns:
            True if successful
        """
        if metadata:
            self.current_project = metadata
        
        if not self.current_project:
            return False
        
        folder_name = self.current_project.get('folder_name')
        project_path = self.base_dir / folder_name
        
        return self._save_metadata(project_path, self.current_project)
    
    def list_projects(self) -> List[dict]:
        """List all projects in base directory.
        
        Returns:
            List of project metadata dictionaries
        """
        projects = []
        
        if not self.base_dir.exists():
            return projects
        
        for item in self.base_dir.iterdir():
            if item.is_dir():
                metadata_file = item / 'project.json'
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            project_data = json.load(f)
                            project_data['path'] = str(item)
                            projects.append(project_data)
                    except (json.JSONDecodeError, IOError):
                        continue
        
        # Sort by creation date, newest first
        projects.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return projects
    
    def delete_project(self, project_path: str) -> bool:
        """Delete a project and all its files.
        
        Args:
            project_path: Path to project folder
            
        Returns:
            True if successful
        """
        project_path = Path(project_path)
        
        if not project_path.exists():
            return False
        
        try:
            shutil.rmtree(project_path)
            return True
        except IOError:
            return False
    
    def add_clip(self, clip_data: dict) -> None:
        """Add a clip to current project.
        
        Args:
            clip_data: Clip metadata (start_time, end_time, title, etc.)
        """
        if self.current_project:
            if 'clips' not in self.current_project:
                self.current_project['clips'] = []
            self.current_project['clips'].append(clip_data)
            self.save_project()
    
    def update_settings(self, settings: dict) -> None:
        """Update project settings.
        
        Args:
            settings: Settings dictionary to merge
        """
        if self.current_project:
            self.current_project.setdefault('settings', {}).update(settings)
            self.save_project()
    
    def get_clips_folder(self) -> str:
        """Get path to clips folder for current project."""
        if self.current_project:
            folder_name = self.current_project.get('folder_name')
            return str(self.base_dir / folder_name / 'clips')
        return None
    
    def get_exports_folder(self) -> str:
        """Get path to exports folder for current project."""
        if self.current_project:
            folder_name = self.current_project.get('folder_name')
            return str(self.base_dir / folder_name / 'exports')
        return None
    
    def get_source_folder(self) -> str:
        """Get path to source folder for current project."""
        if self.current_project:
            folder_name = self.current_project.get('folder_name')
            return str(self.base_dir / folder_name / 'source')
        return None
    
    def _sanitize_name(self, name: str) -> str:
        """Sanitize string for use as folder name."""
        # Remove or replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, '_')
        # Limit length and strip whitespace
        return name.strip()[:50]
    
    def _save_metadata(self, project_path: Path, metadata: dict) -> bool:
        """Save metadata to project.json file."""
        try:
            metadata_file = project_path / 'project.json'
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            return True
        except IOError:
            return False
