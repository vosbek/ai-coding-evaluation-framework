"""
Timing and performance tracking for evaluation sessions.
"""

import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from collections import defaultdict

from ..database.database import get_db
from ..database.models import TestSession, DevelopmentMilestone, AIInteraction, SystemEvent


@dataclass
class TimingPhase:
    """Represents a development phase with timing information."""
    name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    ai_interactions: int = 0
    code_changes: int = 0
    milestones: List[str] = None
    
    def __post_init__(self):
        if self.milestones is None:
            self.milestones = []
    
    def complete(self):
        """Mark phase as complete and calculate duration."""
        self.end_time = datetime.now()
        if self.start_time:
            self.duration_seconds = (self.end_time - self.start_time).total_seconds()


@dataclass
class SessionTimingAnalysis:
    """Complete timing analysis for a session."""
    session_id: int
    total_duration_seconds: float
    phases: List[TimingPhase]
    ai_interaction_frequency: float  # interactions per minute
    code_change_frequency: float     # changes per minute
    productivity_metrics: Dict[str, float]
    time_distribution: Dict[str, float]  # percentage of time in each phase


class TimingTracker:
    """Tracks timing and performance metrics during evaluation sessions."""
    
    def __init__(self, session_id: int):
        self.session_id = session_id
        self.current_phase: Optional[TimingPhase] = None
        self.completed_phases: List[TimingPhase] = []
        self.session_start: Optional[datetime] = None
        self.milestones_tracker: Dict[str, datetime] = {}
        
        # Load session start time
        self._load_session_info()
    
    def _load_session_info(self):
        """Load session information from database."""
        try:
            with next(get_db()) as db:
                session = db.query(TestSession).filter(
                    TestSession.id == self.session_id
                ).first()
                
                if session:
                    self.session_start = session.start_time
        except Exception as e:
            print(f"Error loading session info: {e}")
    
    def start_phase(self, phase_name: str) -> TimingPhase:
        """Start a new development phase."""
        # Complete current phase if active
        if self.current_phase and self.current_phase.end_time is None:
            self.complete_current_phase()
        
        # Start new phase
        self.current_phase = TimingPhase(
            name=phase_name,
            start_time=datetime.now()
        )
        
        # Log phase start
        self._log_timing_event('phase_start', {
            'phase_name': phase_name,
            'start_time': self.current_phase.start_time.isoformat()
        })
        
        return self.current_phase
    
    def complete_current_phase(self) -> Optional[TimingPhase]:
        """Complete the current development phase."""
        if not self.current_phase:
            return None
        
        self.current_phase.complete()
        
        # Update phase statistics
        self._update_phase_stats(self.current_phase)
        
        # Log phase completion
        self._log_timing_event('phase_complete', {
            'phase_name': self.current_phase.name,
            'duration_seconds': self.current_phase.duration_seconds,
            'ai_interactions': self.current_phase.ai_interactions,
            'code_changes': self.current_phase.code_changes
        })
        
        self.completed_phases.append(self.current_phase)
        completed_phase = self.current_phase
        self.current_phase = None
        
        return completed_phase
    
    def add_milestone(self, milestone_name: str, description: str = None):
        """Add a milestone to the current phase."""
        timestamp = datetime.now()
        self.milestones_tracker[milestone_name] = timestamp
        
        # Add to current phase if active
        if self.current_phase:
            self.current_phase.milestones.append(milestone_name)
        
        # Log milestone
        self._log_timing_event('milestone_reached', {
            'milestone_name': milestone_name,
            'description': description,
            'phase': self.current_phase.name if self.current_phase else None,
            'elapsed_time': self._get_elapsed_time()
        })
    
    def _update_phase_stats(self, phase: TimingPhase):
        """Update phase statistics from database."""
        try:
            with next(get_db()) as db:
                # Count AI interactions in phase
                ai_count = db.query(AIInteraction).filter(
                    AIInteraction.session_id == self.session_id,
                    AIInteraction.timestamp >= phase.start_time,
                    AIInteraction.timestamp <= phase.end_time
                ).count()
                
                phase.ai_interactions = ai_count
                
                # Count code changes in phase (from system events)
                from ..database.models import CodeChange
                changes_count = db.query(CodeChange).filter(
                    CodeChange.session_id == self.session_id,
                    CodeChange.timestamp >= phase.start_time,
                    CodeChange.timestamp <= phase.end_time
                ).count()
                
                phase.code_changes = changes_count
                
        except Exception as e:
            print(f"Error updating phase stats: {e}")
    
    def _get_elapsed_time(self) -> float:
        """Get elapsed time since session start in seconds."""
        if not self.session_start:
            return 0.0
        return (datetime.now() - self.session_start).total_seconds()
    
    def _log_timing_event(self, event_type: str, event_data: Dict):
        """Log a timing-related system event."""
        try:
            with next(get_db()) as db:
                system_event = SystemEvent(
                    session_id=self.session_id,
                    event_type=event_type,
                    timestamp=datetime.now(),
                    event_data=json.dumps(event_data),
                    source='timing_tracker'
                )
                
                db.add(system_event)
                db.commit()
        except Exception as e:
            print(f"Error logging timing event: {e}")
    
    def get_current_stats(self) -> Dict[str, Any]:
        """Get current timing statistics."""
        elapsed = self._get_elapsed_time()
        
        stats = {
            'session_id': self.session_id,
            'elapsed_time_seconds': elapsed,
            'elapsed_time_formatted': str(timedelta(seconds=int(elapsed))),
            'current_phase': self.current_phase.name if self.current_phase else None,
            'completed_phases': len(self.completed_phases),
            'total_milestones': len(self.milestones_tracker)
        }
        
        # Add phase-specific stats
        if self.current_phase:
            phase_elapsed = (datetime.now() - self.current_phase.start_time).total_seconds()
            stats['current_phase_duration'] = phase_elapsed
            stats['current_phase_formatted'] = str(timedelta(seconds=int(phase_elapsed)))
        
        return stats
    
    def generate_analysis(self) -> SessionTimingAnalysis:
        """Generate comprehensive timing analysis for the session."""
        # Complete current phase for analysis
        active_phase = None
        if self.current_phase:
            active_phase = self.current_phase
            self.complete_current_phase()
        
        try:
            # Calculate total duration
            total_duration = self._get_elapsed_time()
            
            # Calculate frequencies
            with next(get_db()) as db:
                total_interactions = db.query(AIInteraction).filter(
                    AIInteraction.session_id == self.session_id
                ).count()
                
                from ..database.models import CodeChange
                total_changes = db.query(CodeChange).filter(
                    CodeChange.session_id == self.session_id
                ).count()
            
            ai_frequency = (total_interactions / (total_duration / 60)) if total_duration > 0 else 0
            change_frequency = (total_changes / (total_duration / 60)) if total_duration > 0 else 0
            
            # Calculate productivity metrics
            productivity_metrics = self._calculate_productivity_metrics(total_duration)
            
            # Calculate time distribution
            time_distribution = self._calculate_time_distribution(total_duration)
            
            analysis = SessionTimingAnalysis(
                session_id=self.session_id,
                total_duration_seconds=total_duration,
                phases=self.completed_phases.copy(),
                ai_interaction_frequency=ai_frequency,
                code_change_frequency=change_frequency,
                productivity_metrics=productivity_metrics,
                time_distribution=time_distribution
            )
            
            return analysis
            
        finally:
            # Restore active phase if it was running
            if active_phase:
                self.current_phase = active_phase
    
    def _calculate_productivity_metrics(self, total_duration: float) -> Dict[str, float]:
        """Calculate productivity metrics."""
        try:
            with next(get_db()) as db:
                # Get all AI interactions
                interactions = db.query(AIInteraction).filter(
                    AIInteraction.session_id == self.session_id
                ).all()
                
                # Get all code changes
                from ..database.models import CodeChange
                changes = db.query(CodeChange).filter(
                    CodeChange.session_id == self.session_id
                ).all()
                
                # Calculate metrics
                metrics = {
                    'lines_per_minute': sum(c.lines_added or 0 for c in changes) / (total_duration / 60) if total_duration > 0 else 0,
                    'interactions_per_hour': len(interactions) / (total_duration / 3600) if total_duration > 0 else 0,
                    'average_interaction_rating': sum(i.quality_rating or 0 for i in interactions) / len(interactions) if interactions else 0,
                    'files_modified_per_hour': len(set(c.file_path for c in changes)) / (total_duration / 3600) if total_duration > 0 else 0,
                    'commits_per_hour': len(set(c.git_commit_hash for c in changes if c.git_commit_hash)) / (total_duration / 3600) if total_duration > 0 else 0
                }
                
                return metrics
                
        except Exception as e:
            print(f"Error calculating productivity metrics: {e}")
            return {}
    
    def _calculate_time_distribution(self, total_duration: float) -> Dict[str, float]:
        """Calculate time distribution across phases."""
        if total_duration == 0:
            return {}
        
        distribution = {}
        for phase in self.completed_phases:
            if phase.duration_seconds:
                percentage = (phase.duration_seconds / total_duration) * 100
                distribution[phase.name] = round(percentage, 2)
        
        return distribution


class StandardizedPhases:
    """Standard development phases for consistent tracking."""
    
    REQUIREMENTS_ANALYSIS = "requirements_analysis"
    DESIGN_PLANNING = "design_planning"
    INITIAL_IMPLEMENTATION = "initial_implementation"
    AI_ASSISTED_CODING = "ai_assisted_coding"
    DEBUGGING = "debugging"
    TESTING = "testing"
    REFACTORING = "refactoring"
    DOCUMENTATION = "documentation"
    COMPLETION = "completion"
    
    @classmethod
    def get_all_phases(cls) -> List[str]:
        """Get all standard phase names."""
        return [
            cls.REQUIREMENTS_ANALYSIS,
            cls.DESIGN_PLANNING,
            cls.INITIAL_IMPLEMENTATION,
            cls.AI_ASSISTED_CODING,
            cls.DEBUGGING,
            cls.TESTING,
            cls.REFACTORING,
            cls.DOCUMENTATION,
            cls.COMPLETION
        ]
    
    @classmethod
    def get_phase_descriptions(cls) -> Dict[str, str]:
        """Get descriptions for all phases."""
        return {
            cls.REQUIREMENTS_ANALYSIS: "Understanding requirements and acceptance criteria",
            cls.DESIGN_PLANNING: "Planning implementation approach and architecture",
            cls.INITIAL_IMPLEMENTATION: "Writing initial code structure",
            cls.AI_ASSISTED_CODING: "Using AI assistant for code generation and improvements",
            cls.DEBUGGING: "Identifying and fixing bugs",
            cls.TESTING: "Writing and running tests",
            cls.REFACTORING: "Improving code quality and structure",
            cls.DOCUMENTATION: "Writing documentation and comments",
            cls.COMPLETION: "Final validation and cleanup"
        }


def create_timing_tracker(session_id: int) -> TimingTracker:
    """Factory function to create a timing tracker."""
    return TimingTracker(session_id)