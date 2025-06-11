"""
Automated file monitoring system for tracking code changes during evaluation sessions.
"""

import os
import json
import time
import hashlib
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Set, Callable
from dataclasses import dataclass
from threading import Thread, Event

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent, FileDeletedEvent, FileMovedEvent

from ..database.database import get_db
from ..database.models import CodeChange, SystemEvent


@dataclass
class FileChangeInfo:
    """Information about a file change."""
    file_path: str
    change_type: str  # 'create', 'modify', 'delete', 'rename'
    timestamp: datetime
    lines_added: int = 0
    lines_deleted: int = 0
    lines_modified: int = 0
    diff_content: Optional[str] = None
    git_commit_hash: Optional[str] = None
    file_size: Optional[int] = None
    checksum: Optional[str] = None


class GitIntegration:
    """Git integration for tracking commits and generating diffs."""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self._verify_git_repo()
    
    def _verify_git_repo(self) -> bool:
        """Verify that the path is a git repository."""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--git-dir'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def get_current_commit(self) -> Optional[str]:
        """Get the current commit hash."""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
        return None
    
    def get_file_diff(self, file_path: str, staged: bool = False) -> Optional[str]:
        """Get diff for a specific file."""
        try:
            cmd = ['git', 'diff']
            if staged:
                cmd.append('--staged')
            cmd.append('--')
            cmd.append(file_path)
            
            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                return result.stdout.strip() if result.stdout.strip() else None
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
        return None
    
    def get_line_changes(self, file_path: str) -> Dict[str, int]:
        """Get line change statistics for a file."""
        try:
            result = subprocess.run(
                ['git', 'diff', '--numstat', '--', file_path],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0 and result.stdout.strip():
                parts = result.stdout.strip().split('\t')
                if len(parts) >= 2:
                    added = int(parts[0]) if parts[0] != '-' else 0
                    deleted = int(parts[1]) if parts[1] != '-' else 0
                    return {'added': added, 'deleted': deleted, 'modified': min(added, deleted)}
        except (subprocess.SubprocessError, FileNotFoundError, ValueError):
            pass
        return {'added': 0, 'deleted': 0, 'modified': 0}
    
    def get_staged_files(self) -> List[str]:
        """Get list of staged files."""
        try:
            result = subprocess.run(
                ['git', 'diff', '--staged', '--name-only'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return [f.strip() for f in result.stdout.split('\n') if f.strip()]
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
        return []


class CodeChangeAnalyzer:
    """Analyzes code changes for metrics and patterns."""
    
    def __init__(self):
        self.file_checksums: Dict[str, str] = {}
        self.file_sizes: Dict[str, int] = {}
    
    def calculate_checksum(self, file_path: str) -> Optional[str]:
        """Calculate MD5 checksum of a file."""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except (IOError, OSError):
            return None
    
    def get_file_size(self, file_path: str) -> Optional[int]:
        """Get file size in bytes."""
        try:
            return os.path.getsize(file_path)
        except (IOError, OSError):
            return None
    
    def analyze_change(self, file_path: str, change_type: str) -> FileChangeInfo:
        """Analyze a file change and extract metrics."""
        file_path_obj = Path(file_path)
        
        change_info = FileChangeInfo(
            file_path=str(file_path_obj),
            change_type=change_type,
            timestamp=datetime.now()
        )
        
        if change_type != 'delete':
            change_info.file_size = self.get_file_size(file_path)
            change_info.checksum = self.calculate_checksum(file_path)
        
        return change_info


class EvaluationFileHandler(FileSystemEventHandler):
    """File system event handler for evaluation sessions."""
    
    def __init__(
        self,
        session_id: int,
        git_integration: Optional[GitIntegration] = None,
        change_callback: Optional[Callable[[FileChangeInfo], None]] = None
    ):
        super().__init__()
        self.session_id = session_id
        self.git_integration = git_integration
        self.analyzer = CodeChangeAnalyzer()
        self.change_callback = change_callback
        self.ignored_patterns = {
            '.git', '.gitignore', '__pycache__', '.pyc', '.DS_Store',
            'node_modules', '.vscode', '.idea', '*.tmp', '*.log'
        }
        self.processing_events: Set[str] = set()
    
    def _should_ignore(self, file_path: str) -> bool:
        """Check if file should be ignored."""
        path_obj = Path(file_path)
        
        # Ignore hidden files and directories
        if any(part.startswith('.') for part in path_obj.parts):
            return True
        
        # Ignore common development files
        for pattern in self.ignored_patterns:
            if pattern in str(path_obj):
                return True
        
        return False
    
    def _process_change(self, event_type: str, src_path: str, dest_path: str = None):
        """Process a file system change event."""
        if self._should_ignore(src_path):
            return
        
        # Prevent duplicate processing
        event_key = f"{event_type}:{src_path}:{dest_path or ''}"
        if event_key in self.processing_events:
            return
        
        self.processing_events.add(event_key)
        
        try:
            # Analyze the change
            change_info = self.analyzer.analyze_change(src_path, event_type)
            
            # Get git information if available
            if self.git_integration:
                change_info.git_commit_hash = self.git_integration.get_current_commit()
                
                # Get line changes for modifications
                if event_type in ['modify', 'create']:
                    line_changes = self.git_integration.get_line_changes(src_path)
                    change_info.lines_added = line_changes['added']
                    change_info.lines_deleted = line_changes['deleted']
                    change_info.lines_modified = line_changes['modified']
                    
                    # Get diff content
                    change_info.diff_content = self.git_integration.get_file_diff(src_path)
            
            # Store in database
            self._store_change(change_info)
            
            # Call callback if provided
            if self.change_callback:
                self.change_callback(change_info)
                
        finally:
            # Clean up processing set after a delay
            def cleanup():
                time.sleep(1)  # Allow for duplicate events to settle
                self.processing_events.discard(event_key)
            
            Thread(target=cleanup, daemon=True).start()
    
    def _store_change(self, change_info: FileChangeInfo):
        """Store change information in database."""
        try:
            with next(get_db()) as db:
                code_change = CodeChange(
                    session_id=self.session_id,
                    file_path=change_info.file_path,
                    change_type=change_info.change_type,
                    timestamp=change_info.timestamp,
                    lines_added=change_info.lines_added,
                    lines_deleted=change_info.lines_deleted,
                    lines_modified=change_info.lines_modified,
                    git_commit_hash=change_info.git_commit_hash,
                    diff_content=change_info.diff_content,
                    ai_generated=False  # Will be updated if AI-generated
                )
                
                db.add(code_change)
                db.commit()
                
                # Also log as system event
                system_event = SystemEvent(
                    session_id=self.session_id,
                    event_type='file_change',
                    timestamp=change_info.timestamp,
                    event_data=json.dumps({
                        'file_path': change_info.file_path,
                        'change_type': change_info.change_type,
                        'file_size': change_info.file_size,
                        'checksum': change_info.checksum
                    }),
                    source='file_watcher'
                )
                
                db.add(system_event)
                db.commit()
                
        except Exception as e:
            print(f"Error storing file change: {e}")
    
    def on_modified(self, event):
        """Handle file modification events."""
        if not event.is_directory:
            self._process_change('modify', event.src_path)
    
    def on_created(self, event):
        """Handle file creation events."""
        if not event.is_directory:
            self._process_change('create', event.src_path)
    
    def on_deleted(self, event):
        """Handle file deletion events."""
        if not event.is_directory:
            self._process_change('delete', event.src_path)
    
    def on_moved(self, event):
        """Handle file move/rename events."""
        if not event.is_directory:
            self._process_change('rename', event.src_path, event.dest_path)


class FileMonitor:
    """Main file monitoring system for evaluation sessions."""
    
    def __init__(self, watch_path: str, session_id: int):
        self.watch_path = Path(watch_path).resolve()
        self.session_id = session_id
        self.observer = Observer()
        self.git_integration = None
        self.event_handler = None
        self.is_monitoring = False
        self.stop_event = Event()
        
        # Initialize git integration if available
        try:
            self.git_integration = GitIntegration(self.watch_path)
        except Exception:
            print("Git integration not available")
    
    def start_monitoring(self, change_callback: Optional[Callable[[FileChangeInfo], None]] = None):
        """Start monitoring file changes."""
        if self.is_monitoring:
            return
        
        self.event_handler = EvaluationFileHandler(
            session_id=self.session_id,
            git_integration=self.git_integration,
            change_callback=change_callback
        )
        
        self.observer.schedule(
            self.event_handler,
            str(self.watch_path),
            recursive=True
        )
        
        self.observer.start()
        self.is_monitoring = True
        
        # Log monitoring start
        self._log_system_event('file_monitoring_start', {
            'watch_path': str(self.watch_path),
            'git_available': self.git_integration is not None
        })
        
        print(f"Started monitoring: {self.watch_path}")
    
    def stop_monitoring(self):
        """Stop monitoring file changes."""
        if not self.is_monitoring:
            return
        
        self.observer.stop()
        self.observer.join(timeout=5)
        self.is_monitoring = False
        
        # Log monitoring stop
        self._log_system_event('file_monitoring_stop', {
            'watch_path': str(self.watch_path)
        })
        
        print("Stopped monitoring file changes")
    
    def _log_system_event(self, event_type: str, event_data: Dict):
        """Log a system event."""
        try:
            with next(get_db()) as db:
                system_event = SystemEvent(
                    session_id=self.session_id,
                    event_type=event_type,
                    timestamp=datetime.now(),
                    event_data=json.dumps(event_data),
                    source='file_monitor'
                )
                
                db.add(system_event)
                db.commit()
        except Exception as e:
            print(f"Error logging system event: {e}")
    
    def get_monitoring_stats(self) -> Dict:
        """Get monitoring statistics for current session."""
        try:
            with next(get_db()) as db:
                changes = db.query(CodeChange).filter(
                    CodeChange.session_id == self.session_id
                ).all()
                
                stats = {
                    'total_changes': len(changes),
                    'files_created': len([c for c in changes if c.change_type == 'create']),
                    'files_modified': len([c for c in changes if c.change_type == 'modify']),
                    'files_deleted': len([c for c in changes if c.change_type == 'delete']),
                    'files_renamed': len([c for c in changes if c.change_type == 'rename']),
                    'total_lines_added': sum(c.lines_added or 0 for c in changes),
                    'total_lines_deleted': sum(c.lines_deleted or 0 for c in changes),
                    'unique_files': len(set(c.file_path for c in changes)),
                    'git_commits': len(set(c.git_commit_hash for c in changes if c.git_commit_hash))
                }
                
                return stats
        except Exception as e:
            print(f"Error getting monitoring stats: {e}")
            return {}
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop_monitoring()