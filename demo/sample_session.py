#!/usr/bin/env python3
"""
Sample demonstration script showing automated session creation and analysis.
This simulates a complete evaluation workflow for demonstration purposes.
"""

import sys
import os
import time
from datetime import datetime, timedelta
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from database.database import init_database, get_db
from logging.logger import EvaluationLogger
from monitoring.session_manager import EvaluationSessionManager
from analysis.metrics_calculator import MetricsCalculator
from analysis.report_generator import ReportGenerator


def create_sample_data():
    """Create sample evaluation data for demonstration."""
    print("🎯 Creating Sample Evaluation Data...")
    
    # Initialize database
    init_database()
    
    logger = EvaluationLogger()
    calculator = MetricsCalculator()
    
    # Sample evaluation sessions
    sessions_data = [
        {
            "name": "Bug Fix - Cursor Evaluation",
            "tool": "cursor",
            "type": "bug_fix",
            "developer": "alice_smith",
            "duration_minutes": 23.4,
            "ai_interactions": [
                {"prompt": "Help me understand this React error", "rating": 4, "tokens": 85, "cost": 0.012},
                {"prompt": "Fix null pointer in UserProfile", "rating": 5, "tokens": 210, "cost": 0.031},
                {"prompt": "Add error boundary for safety", "rating": 4, "tokens": 150, "cost": 0.022}
            ],
            "satisfaction": 5,
            "lines_added": 15,
            "files_modified": 2
        },
        {
            "name": "Bug Fix - GitHub Copilot Evaluation", 
            "tool": "github_copilot",
            "type": "bug_fix",
            "developer": "alice_smith",
            "duration_minutes": 27.8,
            "ai_interactions": [
                {"prompt": "Explain React null reference error", "rating": 3, "tokens": 120, "cost": 0.018},
                {"prompt": "Generate safe component code", "rating": 4, "tokens": 280, "cost": 0.042},
                {"prompt": "Add defensive programming patterns", "rating": 4, "tokens": 190, "cost": 0.028}
            ],
            "satisfaction": 4,
            "lines_added": 18,
            "files_modified": 2
        },
        {
            "name": "New Feature - Cursor Evaluation",
            "tool": "cursor", 
            "type": "new_feature",
            "developer": "bob_jones",
            "duration_minutes": 45.2,
            "ai_interactions": [
                {"prompt": "Create user authentication system", "rating": 5, "tokens": 340, "cost": 0.051},
                {"prompt": "Generate login form component", "rating": 4, "tokens": 220, "cost": 0.033},
                {"prompt": "Add JWT token handling", "rating": 5, "tokens": 180, "cost": 0.027},
                {"prompt": "Write authentication tests", "rating": 4, "tokens": 200, "cost": 0.030}
            ],
            "satisfaction": 5,
            "lines_added": 85,
            "files_modified": 6
        },
        {
            "name": "New Feature - GitHub Copilot Evaluation",
            "tool": "github_copilot",
            "type": "new_feature", 
            "developer": "bob_jones",
            "duration_minutes": 52.1,
            "ai_interactions": [
                {"prompt": "Build authentication system", "rating": 3, "tokens": 300, "cost": 0.045},
                {"prompt": "Create login UI components", "rating": 4, "tokens": 250, "cost": 0.037},
                {"prompt": "Implement JWT authentication", "rating": 3, "tokens": 220, "cost": 0.033},
                {"prompt": "Add auth unit tests", "rating": 4, "tokens": 240, "cost": 0.036}
            ],
            "satisfaction": 4,
            "lines_added": 92,
            "files_modified": 7
        }
    ]
    
    session_ids = []
    
    for session_data in sessions_data:
        print(f"  📝 Creating session: {session_data['name']}")
        
        # Create session
        session_start = datetime.now() - timedelta(minutes=session_data['duration_minutes'])
        session_id = logger.start_session(
            session_name=session_data['name'],
            tool_name=session_data['tool'],
            test_case_type=session_data['type'],
            developer_id=session_data['developer']
        )
        
        # Update session timing
        with next(get_db()) as db:
            session = db.query(logger.TestSession).filter(
                logger.TestSession.id == session_id
            ).first()
            session.start_time = session_start
            session.end_time = session_start + timedelta(minutes=session_data['duration_minutes'])
            session.status = 'completed'
            db.commit()
        
        # Add AI interactions
        for i, interaction in enumerate(session_data['ai_interactions']):
            interaction_time = session_start + timedelta(minutes=i * 5)
            
            with next(get_db()) as db:
                from database.models import AIInteraction
                ai_interaction = AIInteraction(
                    session_id=session_id,
                    interaction_sequence=i + 1,
                    timestamp=interaction_time,
                    prompt_text=interaction['prompt'],
                    response_text=f"AI response for: {interaction['prompt']}",
                    interaction_type='code_generation',
                    quality_rating=interaction['rating'],
                    was_helpful=True,
                    tokens_used=interaction['tokens'],
                    cost_estimate=interaction['cost']
                )
                db.add(ai_interaction)
                db.commit()
        
        # Add code changes
        with next(get_db()) as db:
            from database.models import CodeChange
            for i in range(session_data['files_modified']):
                code_change = CodeChange(
                    session_id=session_id,
                    file_path=f"src/components/File{i+1}.jsx",
                    change_type='modify',
                    timestamp=session_start + timedelta(minutes=10 + i*5),
                    lines_added=session_data['lines_added'] // session_data['files_modified'],
                    lines_deleted=2,
                    lines_modified=1,
                    ai_generated=True
                )
                db.add(code_change)
            db.commit()
        
        # Add developer feedback
        with next(get_db()) as db:
            from database.models import DeveloperFeedback
            feedback = DeveloperFeedback(
                session_id=session_id,
                timestamp=session.end_time,
                ease_of_use_rating=session_data['satisfaction'],
                code_quality_rating=session_data['satisfaction'],
                productivity_rating=session_data['satisfaction'],
                learning_curve_rating=session_data['satisfaction'],
                overall_satisfaction=session_data['satisfaction'],
                would_recommend=session_data['satisfaction'] >= 4,
                likes=f"Great experience with {session_data['tool']}",
                dislikes="Minor suggestions for improvement"
            )
            db.add(feedback)
            db.commit()
        
        session_ids.append(session_id)
        print(f"    ✅ Session {session_id} created")
    
    return session_ids


def demonstrate_analysis(session_ids):
    """Demonstrate analysis capabilities."""
    print("\n📊 Demonstrating Analysis Capabilities...")
    
    calculator = MetricsCalculator()
    
    # Calculate metrics for each session
    print("\n  🔍 Session Metrics:")
    for session_id in session_ids:
        metrics = calculator.calculate_session_metrics(session_id)
        if metrics:
            print(f"    Session {session_id} ({metrics.tool_name}):")
            print(f"      Duration: {metrics.total_duration_minutes:.1f} minutes")
            print(f"      AI Interactions: {metrics.total_ai_interactions}")
            print(f"      Lines Added: {metrics.lines_added}")
            print(f"      Satisfaction: {metrics.satisfaction_rating}/5")
            print(f"      Cost: ${metrics.total_cost_estimate:.3f}")
    
    # Tool comparison
    print("\n  ⚖️  Tool Comparison:")
    comparison = calculator.calculate_tool_comparison("cursor", "github_copilot", "bug_fix")
    if comparison:
        print(f"    Bug Fix Comparison (Cursor vs GitHub Copilot):")
        print(f"      Speed improvement: {comparison.speed_improvement_percentage:.1f}%")
        print(f"      Productivity improvement: {comparison.productivity_improvement_percentage:.1f}%")
        print(f"      Quality improvement: {comparison.code_quality_improvement_percentage:.1f}%")
        print(f"      Satisfaction difference: {comparison.satisfaction_difference:.1f} points")
        print(f"      Winner: {comparison.preference_winner}")
    
    # Summary statistics
    print("\n  📈 Summary Statistics:")
    cursor_stats = calculator.get_session_summary_stats("cursor")
    copilot_stats = calculator.get_session_summary_stats("github_copilot")
    
    if cursor_stats:
        print(f"    Cursor - {cursor_stats['total_sessions']} sessions:")
        print(f"      Avg Duration: {cursor_stats['duration']['mean']:.1f} minutes")
        print(f"      Avg Satisfaction: {cursor_stats['satisfaction']['mean']:.1f}/5")
    
    if copilot_stats:
        print(f"    GitHub Copilot - {copilot_stats['total_sessions']} sessions:")
        print(f"      Avg Duration: {copilot_stats['duration']['mean']:.1f} minutes")
        print(f"      Avg Satisfaction: {copilot_stats['satisfaction']['mean']:.1f}/5")


def demonstrate_reports(session_ids):
    """Demonstrate report generation."""
    print("\n📄 Demonstrating Report Generation...")
    
    try:
        generator = ReportGenerator()
        
        # Generate session report
        print("\n  📝 Generating Session Report...")
        if session_ids:
            session_report = generator.generate_session_report(session_ids[0], 'html')
            print(f"    ✅ Session report: {session_report}")
        
        # Generate comparison report
        print("\n  ⚖️  Generating Comparison Report...")
        comparison_report = generator.generate_comparison_report("cursor", "github_copilot", "bug_fix", 'html')
        print(f"    ✅ Comparison report: {comparison_report}")
        
        # Generate JSON reports for API access
        print("\n  🔌 Generating JSON Reports...")
        if session_ids:
            json_report = generator.generate_session_report(session_ids[0], 'json')
            print(f"    ✅ JSON session report: {json_report}")
        
        json_comparison = generator.generate_comparison_report("cursor", "github_copilot", "bug_fix", 'json')
        print(f"    ✅ JSON comparison report: {json_comparison}")
        
    except Exception as e:
        print(f"    ⚠️  Report generation requires matplotlib. Install with: pip install matplotlib seaborn")
        print(f"    Error: {e}")


def main():
    """Run the complete demonstration."""
    print("🚀 AI Coding Assistant Evaluation Framework - DEMONSTRATION")
    print("=" * 60)
    
    # Create sample data
    session_ids = create_sample_data()
    
    # Demonstrate analysis
    demonstrate_analysis(session_ids)
    
    # Demonstrate reports
    demonstrate_reports(session_ids)
    
    print("\n" + "=" * 60)
    print("✅ DEMONSTRATION COMPLETE!")
    print("\nWhat you've seen:")
    print("  • Automated session creation and data tracking")
    print("  • Comprehensive metrics calculation")
    print("  • Tool comparison analysis")
    print("  • Professional report generation")
    print("\nNext steps:")
    print("  • Use the CLI to create real evaluation sessions")
    print("  • Generate reports with: eval-framework reports")
    print("  • Start evaluating AI tools with real data!")
    print("\nFramework files:")
    print("  • Reports: reports/generated/")
    print("  • Database: data/evaluation_framework.db")
    print("  • Documentation: docs/")


if __name__ == "__main__":
    main()