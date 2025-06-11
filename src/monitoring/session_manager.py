"""
Integrated session manager that coordinates file monitoring, timing tracking, and logging.
"""

import json
from datetime import datetime
from typing import Optional, Dict, Any, Callable
from pathlib import Path

from ..database.database import get_db
from ..database.models import TestSession, SystemEvent
from .file_watcher import FileMonitor, FileChangeInfo
from .timing_tracker import TimingTracker, StandardizedPhases


class EvaluationSessionManager:
    """
    Integrated manager for evaluation sessions that coordinates:
    - File monitoring
    - Timing tracking  
    - AI interaction logging
    - Session state management
    """
    
    def __init__(self, session_id: int, watch_path: str = None):
        self.session_id = session_id
        self.watch_path = watch_path or "."
        
        # Core components
        self.file_monitor: Optional[FileMonitor] = None
        self.timing_tracker: Optional[TimingTracker] = None
        
        # State tracking
        self.is_active = False
        self.session_info: Optional[TestSession] = None
        
        # Callbacks
        self.change_callback: Optional[Callable[[FileChangeInfo], None]] = None
        
        # Load session information
        self._load_session()
    
    def _load_session(self):
        """Load session information from database."""
        try:
            with next(get_db()) as db:
                self.session_info = db.query(TestSession).filter(
                    TestSession.id == self.session_id
                ).first()
                
                if not self.session_info:
                    raise ValueError(f"Session {self.session_id} not found")
                    
        except Exception as e:
            print(f"Error loading session: {e}")
            raise
    
    def start_monitoring(self, 
                        enable_file_monitoring: bool = True,
                        enable_timing_tracking: bool = True,
                        change_callback: Optional[Callable[[FileChangeInfo], None]] = None) -> None:
        """Start comprehensive monitoring for the evaluation session."""
        
        if self.is_active:
            print("Session monitoring already active")
            return
        
        print(f"Starting monitoring for session {self.session_id}")
        
        # Set up timing tracker
        if enable_timing_tracking:
            self.timing_tracker = TimingTracker(self.session_id)
            print("Timing tracker initialized")
        
        # Set up file monitor
        if enable_file_monitoring:
            self.file_monitor = FileMonitor(self.watch_path, self.session_id)
            self.change_callback = change_callback or self._default_change_callback
            self.file_monitor.start_monitoring(self.change_callback)
            print(f"File monitoring started for: {self.watch_path}")
        
        self.is_active = True
        
        # Log session monitoring start
        self._log_session_event('monitoring_start', {
            'file_monitoring': enable_file_monitoring,
            'timing_tracking': enable_timing_tracking,
            'watch_path': self.watch_path
        })
        
        print("✅ Session monitoring active")
    
    def stop_monitoring(self) -> Dict[str, Any]:
        """Stop monitoring and return session summary."""
        
        if not self.is_active:
            print("Session monitoring not active")
            return {}
        
        print("Stopping session monitoring...")
        
        # Get final statistics
        summary = self.get_session_summary()
        
        # Stop file monitoring
        if self.file_monitor:
            self.file_monitor.stop_monitoring()
            print("File monitoring stopped")
        
        # Complete timing tracking
        if self.timing_tracker:
            if self.timing_tracker.current_phase:
                self.timing_tracker.complete_current_phase()
            print("Timing tracking completed")
        
        self.is_active = False
        
        # Log session monitoring stop
        self._log_session_event('monitoring_stop', summary)
        
        print("✅ Session monitoring stopped")
        return summary
    
    def start_phase(self, phase_name: str) -> None:
        """Start a new development phase."""
        if not self.timing_tracker:
            print("Timing tracker not initialized")
            return
        
        phase = self.timing_tracker.start_phase(phase_name)
        print(f"Started phase: {phase_name}")
        
        # Log milestone
        from ..logging.logger import EvaluationLogger
        logger = EvaluationLogger()
        logger.current_session_id = self.session_id
        logger.log_milestone(
            milestone_name=f"phase_start_{phase_name}",
            description=f"Started development phase: {phase_name}"
        )
    
    def complete_current_phase(self) -> Optional[str]:
        """Complete the current development phase."""
        if not self.timing_tracker:
            return None
        
        completed_phase = self.timing_tracker.complete_current_phase()
        if completed_phase:
            print(f"Completed phase: {completed_phase.name} ({completed_phase.duration_seconds:.1f}s)")
            
            # Log milestone
            from ..logging.logger import EvaluationLogger
            logger = EvaluationLogger()
            logger.current_session_id = self.session_id
            logger.log_milestone(
                milestone_name=f"phase_complete_{completed_phase.name}",
                description=f"Completed development phase: {completed_phase.name}",
                developer_notes=f"Duration: {completed_phase.duration_seconds:.1f}s, "
                              f"AI interactions: {completed_phase.ai_interactions}, "
                              f"Code changes: {completed_phase.code_changes}"
            )
            
            return completed_phase.name
        
        return None
    
    def add_milestone(self, milestone_name: str, description: str = None):
        """Add a milestone to the current session."""
        if self.timing_tracker:
            self.timing_tracker.add_milestone(milestone_name, description)
        
        # Also log through the main logger
        from ..logging.logger import EvaluationLogger
        logger = EvaluationLogger()
        logger.current_session_id = self.session_id
        logger.log_milestone(milestone_name, description)
        
        print(f"Milestone added: {milestone_name}")
    
    def log_ai_interaction(self,
                          prompt_text: str,
                          response_text: str = None,
                          interaction_type: str = 'code_generation',
                          quality_rating: int = None,
                          was_helpful: bool = None,
                          tokens_used: int = None,
                          cost_estimate: float = None) -> None:
        """Log an AI interaction with integrated tracking."""
        
        # Log through main logger
        from ..logging.logger import EvaluationLogger
        logger = EvaluationLogger()
        logger.current_session_id = self.session_id
        logger.log_ai_interaction(
            prompt_text=prompt_text,
            response_text=response_text,
            interaction_type=interaction_type,
            quality_rating=quality_rating,
            was_helpful=was_helpful,
            tokens_used=tokens_used,
            cost_estimate=cost_estimate
        )
        
        print(f"AI interaction logged: {interaction_type}")
    
    def mark_code_as_ai_generated(self, file_path: str, commit_hash: str = None):
        """Mark recent code changes as AI-generated."""
        try:
            with next(get_db()) as db:
                from ..database.models import CodeChange
                
                # Find recent changes to this file
                query = db.query(CodeChange).filter(
                    CodeChange.session_id == self.session_id,
                    CodeChange.file_path.like(f"%{file_path}%")
                )
                
                if commit_hash:
                    query = query.filter(CodeChange.git_commit_hash == commit_hash)
                else:
                    # Mark changes from last 5 minutes
                    from datetime import timedelta
                    recent_time = datetime.now() - timedelta(minutes=5)
                    query = query.filter(CodeChange.timestamp >= recent_time)
                
                changes = query.all()
                
                for change in changes:
                    change.ai_generated = True
                
                db.commit()
                
                print(f"Marked {len(changes)} changes as AI-generated for {file_path}")
                
        except Exception as e:
            print(f"Error marking code as AI-generated: {e}")
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get comprehensive session summary."""
        summary = {
            'session_id': self.session_id,
            'session_info': {
                'name': self.session_info.session_name,
                'tool': self.session_info.tool_name,
                'type': self.session_info.test_case_type,
                'status': self.session_info.status
            },
            'monitoring': {
                'is_active': self.is_active,
                'watch_path': self.watch_path,
                'file_monitoring': self.file_monitor is not None,
                'timing_tracking': self.timing_tracker is not None
            }
        }
        
        # Add timing statistics
        if self.timing_tracker:
            timing_stats = self.timing_tracker.get_current_stats()
            summary['timing'] = timing_stats
        
        # Add file monitoring statistics
        if self.file_monitor:
            monitoring_stats = self.file_monitor.get_monitoring_stats()
            summary['file_changes'] = monitoring_stats
        
        # Add database statistics
        try:
            with next(get_db()) as db:
                from ..database.models import AIInteraction, CodeChange, DevelopmentMilestone
                
                ai_interactions = db.query(AIInteraction).filter(
                    AIInteraction.session_id == self.session_id
                ).count()
                
                code_changes = db.query(CodeChange).filter(
                    CodeChange.session_id == self.session_id
                ).count()
                
                milestones = db.query(DevelopmentMilestone).filter(
                    DevelopmentMilestone.session_id == self.session_id
                ).count()
                
                summary['statistics'] = {
                    'ai_interactions': ai_interactions,
                    'code_changes': code_changes,
                    'milestones': milestones
                }
                
        except Exception as e:
            print(f"Error getting database statistics: {e}")
            summary['statistics'] = {}
        
        return summary
    
    def _default_change_callback(self, change_info: FileChangeInfo):
        """Default callback for file changes."""
        print(f"File {change_info.change_type}: {change_info.file_path}")
        if change_info.lines_added or change_info.lines_deleted:
            print(f"  +{change_info.lines_added} -{change_info.lines_deleted} lines")
    
    def _log_session_event(self, event_type: str, event_data: Dict):
        """Log a session management event."""
        try:
            with next(get_db()) as db:
                system_event = SystemEvent(
                    session_id=self.session_id,
                    event_type=event_type,
                    timestamp=datetime.now(),
                    event_data=json.dumps(event_data),
                    source='session_manager'
                )
                
                db.add(system_event)
                db.commit()
        except Exception as e:
            print(f"Error logging session event: {e}")
    
    def list_standard_phases(self) -> Dict[str, str]:
        """List standard development phases."""
        return StandardizedPhases.get_phase_descriptions()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.is_active:
            self.stop_monitoring()