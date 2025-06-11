# Architecture Documentation

## Project Structure

```
ai-coding-evaluation-framework/
├── src/
│   ├── backend/           # Backend services and APIs
│   ├── frontend/          # User interface components
│   ├── database/          # Database schemas and migrations
│   ├── logging/           # Logging system components
│   ├── analysis/          # Data analysis and metrics
│   └── reporting/         # Report generation
├── tests/                 # Test suites
├── docs/                  # Documentation
│   ├── api/              # API documentation
│   └── setup/            # Setup and installation guides
├── config/               # Configuration files
├── data/                 # Data storage
│   ├── raw/              # Raw test data
│   └── processed/        # Processed analysis data
├── reports/              # Generated reports
│   └── generated/        # Auto-generated reports
└── templates/            # Test case templates
```

## Database Design

### Core Tables

#### test_sessions
Primary table for tracking individual evaluation runs with AI tools.
- Links to all other data through foreign keys
- Tracks tool name, test case type, duration, and status
- Stores environment information and developer notes

#### test_cases
Defines the scenarios being evaluated (bug fixes, new features, refactoring).
- Contains standardized requirements and success criteria
- Links to golden repository information
- Includes estimated duration and difficulty ratings

#### ai_interactions
Captures each prompt/response cycle during testing.
- Tracks sequence of interactions within a session
- Records quality ratings and helpfulness assessments
- Monitors token usage and cost estimates

#### code_changes
Monitors file modifications during evaluation sessions.
- Tracks file paths, change types, and line counts
- Links to git commits for version control
- Identifies AI-generated vs manual changes

#### quality_metrics
Stores before/after code quality measurements.
- Includes complexity metrics, test coverage, and quality ratings
- Captures build results and performance data
- Extensible JSON field for additional metrics

### Views and Analysis

#### session_summary
Aggregated view of session data for quick analysis:
- Duration calculations
- Interaction and change counts
- Average satisfaction ratings

#### tool_comparison
Comparative analysis across different AI tools:
- Performance metrics by tool and test case type
- Statistical summaries for decision support

## Data Flow

```
Test Execution → Manual Logging → Database Storage
     ↓              ↓                 ↓
File Changes → Auto Monitoring → Real-time Updates
     ↓              ↓                 ↓
Completion → Quality Analysis → Report Generation
```

## Integration Points

1. **File System Monitoring**: Automated tracking of code changes
2. **Git Integration**: Version control and diff analysis
3. **Build System Integration**: Automated quality metric collection
4. **Screen Recording**: Session documentation and review
5. **IDE Integration**: AI interaction tracking

## Extensibility

The framework is designed to support:
- Additional AI coding tools
- New test case types
- Custom quality metrics
- Different programming languages
- Various development environments

## Configuration

Database and system configuration is managed through JSON files in the `config/` directory:
- `database.json`: Database connection and backup settings
- Future: `logging.json`, `analysis.json`, `reporting.json`

## Components Built

### ✅ Core Infrastructure
- **Database Layer**: SQLAlchemy models, schema, and connection management
- **Logging System**: Manual interaction tracking with rich CLI interface
- **File Monitoring**: Real-time file change detection with git integration
- **Timing Tracker**: Development phase tracking and productivity metrics
- **Session Manager**: Integrated coordination of all monitoring systems

### ✅ Analysis Engine
- **Metrics Calculator**: Comprehensive session and comparison metrics
- **Report Generator**: HTML/JSON reports with visualizations
- **CLI Reports**: Terminal-based analysis and report generation

### ✅ Setup and Installation
- **Cross-platform setup scripts**: Linux/macOS (`setup.sh`) and Windows (`setup.bat`)
- **Virtual environment management**: Automated dependency installation
- **Database initialization**: One-command setup with validation

## Available CLI Commands

### Session Management
```bash
eval-framework start-session    # Start evaluation with monitoring
eval-framework end-session      # Complete session with summary
eval-framework status          # Show current session status
```

### Development Tracking
```bash
eval-framework start-phase     # Begin development phase
eval-framework complete-phase  # End current phase
eval-framework log-ai         # Log AI interaction with metrics
eval-framework milestone      # Add development milestone
```

### Monitoring Control
```bash
eval-framework monitor-start  # Start file monitoring
eval-framework monitor-stop   # Stop monitoring with summary
```

### Analysis and Reporting
```bash
eval-framework reports quick-analysis      # Terminal analysis
eval-framework reports session-report     # Detailed session report
eval-framework reports comparison-report  # Tool comparison analysis
eval-framework reports executive-summary  # High-level overview
eval-framework reports list-sessions      # Show all sessions
```

### Data Management
```bash
eval-framework backup         # Database backup
eval-framework info          # Database information
eval-framework list          # List recent sessions
```