# Usage Guide

## Quick Start

After installation, the framework provides a comprehensive CLI for conducting AI coding assistant evaluations.

### 1. Initialize the Framework

```bash
# Activate environment
source activate.sh  # Linux/macOS
# or
activate.bat        # Windows

# Initialize database
eval-framework init
```

### 2. Start an Evaluation Session

```bash
# Interactive session start
eval-framework start-session

# Or with parameters
eval-framework start-session \
  --name "Cursor vs Copilot Bug Fix Test" \
  --tool cursor \
  --type bug_fix \
  --developer john_doe \
  --enable-monitoring
```

### 3. Development Process with Monitoring

```bash
# Start a development phase
eval-framework start-phase requirements_analysis

# Log AI interactions as you work
eval-framework log-ai \
  --prompt "Fix the null pointer exception in UserService" \
  --response "Here's the fix..." \
  --rating 4 \
  --helpful true \
  --tokens 150 \
  --cost 0.02 \
  --ai-generated

# Complete current phase
eval-framework complete-phase

# Continue with next phases...
eval-framework start-phase initial_implementation
# ... work and log interactions ...
eval-framework complete-phase
```

### 4. Session Management

```bash
# Check current session status
eval-framework status

# Add milestones manually
eval-framework milestone --name "tests_passing" --description "All unit tests now pass"

# Monitor file changes (if not auto-started)
eval-framework monitor-start
eval-framework monitor-stop

# End session with feedback
eval-framework feedback
eval-framework end-session --notes "Cursor was more helpful for debugging"
```

### 5. Generate Reports

```bash
# Quick analysis in terminal
eval-framework reports quick-analysis --session-id 1

# Generate detailed session report
eval-framework reports session-report --session-id 1 --open-browser

# Compare two tools
eval-framework reports comparison-report \
  --tool-a cursor \
  --tool-b github_copilot \
  --test-case-type bug_fix \
  --open-browser

# Executive summary
eval-framework reports executive-summary --open-browser
```

## Detailed Workflows

### Complete Evaluation Workflow

Here's a complete workflow for evaluating two AI tools on the same task:

#### Phase 1: Setup
```bash
# Initialize if not done
eval-framework init

# Backup existing database
eval-framework backup
```

#### Phase 2: First Tool Evaluation
```bash
# Start session for first tool
eval-framework start-session \
  --name "Feature X Implementation - Cursor" \
  --tool cursor \
  --type new_feature \
  --developer jane_smith \
  --watch-path ./my-project \
  --enable-monitoring

# Begin development process
eval-framework start-phase requirements_analysis

# Work on understanding requirements
# Log AI interactions as you use the tool
eval-framework log-ai \
  --prompt "Help me understand this feature specification" \
  --response "The feature should..." \
  --type explanation \
  --rating 5 \
  --helpful true

eval-framework complete-phase

# Continue through implementation phases
eval-framework start-phase initial_implementation

# Log code generation interactions
eval-framework log-ai \
  --prompt "Generate a React component for user profile" \
  --response "Here's the component..." \
  --type code_generation \
  --rating 4 \
  --tokens 250 \
  --cost 0.03 \
  --ai-generated

# Mark specific files as AI-generated when prompted
# The system will automatically track file changes

eval-framework complete-phase

# Continue with other phases: debugging, testing, etc.
# Log all AI interactions and mark AI-generated code

# Provide final feedback
eval-framework feedback

# End session
eval-framework end-session --notes "Cursor provided excellent autocompletion"
```

#### Phase 3: Second Tool Evaluation
```bash
# Reset your codebase to initial state
# Start session for second tool
eval-framework start-session \
  --name "Feature X Implementation - GitHub Copilot" \
  --tool github_copilot \
  --type new_feature \
  --developer jane_smith \
  --watch-path ./my-project \
  --enable-monitoring

# Repeat the same development process
# Follow identical steps but using the second AI tool
# Log interactions and mark AI-generated code
# Provide feedback and end session
```

#### Phase 4: Analysis
```bash
# Quick comparison
eval-framework reports quick-analysis --tool cursor
eval-framework reports quick-analysis --tool github_copilot

# Generate detailed comparison report
eval-framework reports comparison-report \
  --tool-a cursor \
  --tool-b github_copilot \
  --test-case-type new_feature \
  --open-browser

# List all sessions for review
eval-framework reports list-sessions
```

### Standard Development Phases

The framework provides standardized phases for consistent tracking:

1. **requirements_analysis** - Understanding requirements and acceptance criteria
2. **design_planning** - Planning implementation approach and architecture  
3. **initial_implementation** - Writing initial code structure
4. **ai_assisted_coding** - Using AI assistant for code generation and improvements
5. **debugging** - Identifying and fixing bugs
6. **testing** - Writing and running tests
7. **refactoring** - Improving code quality and structure
8. **documentation** - Writing documentation and comments
9. **completion** - Final validation and cleanup

Use these phases consistently across evaluations for better comparison.

### AI Interaction Logging Best Practices

#### Interaction Types
- `code_generation` - AI generating new code
- `explanation` - AI explaining concepts or code
- `debug` - AI helping identify or fix bugs
- `refactor` - AI suggesting code improvements
- `other` - Other types of assistance

#### Quality Ratings (1-5 scale)
- **5** - Excellent, solved problem completely
- **4** - Good, mostly correct with minor issues
- **3** - Average, partially helpful
- **2** - Poor, not very helpful
- **1** - Terrible, incorrect or unhelpful

#### Token and Cost Tracking
```bash
# Log with token/cost information for budget analysis
eval-framework log-ai \
  --prompt "Generate authentication middleware" \
  --tokens 380 \
  --cost 0.05 \
  --rating 4
```

### File Monitoring Features

The framework automatically tracks:
- File creations, modifications, deletions
- Line count changes (added/deleted/modified)
- Git commit information and diffs
- File timestamps and checksums

Manual controls:
```bash
# Start/stop monitoring
eval-framework monitor-start
eval-framework monitor-stop

# Mark recent changes as AI-generated
eval-framework log-ai --ai-generated
# (will prompt for file path)
```

### Report Types

#### Session Reports
Detailed analysis of individual evaluation sessions:
- Duration and phase breakdowns
- AI interaction patterns
- Code change metrics
- Quality and productivity measurements

#### Comparison Reports  
Side-by-side analysis of two AI tools:
- Performance comparisons (speed, productivity, quality)
- Cost analysis (tokens, estimated costs)
- Developer satisfaction differences
- Statistical significance indicators

#### Executive Summaries
High-level overview across all evaluations:
- Tool performance rankings
- ROI analysis and recommendations
- Trend analysis over time
- Key insights and decision support

### Data Export and Integration

```bash
# Export session data as JSON
eval-framework reports session-report --session-id 1 --format json

# Export comparison data
eval-framework reports comparison-report \
  --tool-a cursor \
  --tool-b copilot \
  --format json

# Database backup for external analysis
eval-framework backup
```

### Troubleshooting

#### Common Issues

**"No active session" errors**
```bash
# Check current status
eval-framework status

# Start a new session if needed
eval-framework start-session
```

**File monitoring not working**
```bash
# Verify git repository
git status

# Check file permissions
ls -la

# Restart monitoring
eval-framework monitor-stop
eval-framework monitor-start
```

**Missing data in reports**
```bash
# Verify session completion
eval-framework reports list-sessions

# Check for incomplete sessions
eval-framework list --limit 20
```

**Charts not displaying in reports**
```bash
# Ensure matplotlib backend is available
python -c "import matplotlib.pyplot as plt; plt.figure()"

# Check output directory permissions
ls -la reports/generated/
```

### Tips for Effective Evaluations

1. **Consistency**: Use the same test cases and evaluation criteria across different tools
2. **Documentation**: Log detailed notes about your experience with each tool
3. **Multiple Sessions**: Run multiple evaluations to account for variability
4. **Realistic Tasks**: Use representative real-world development tasks
5. **Environment Control**: Keep development environment consistent across evaluations
6. **Feedback Quality**: Provide thoughtful, specific feedback for each session

### Advanced Usage

#### Custom Metrics
The framework is extensible. You can add custom metrics by extending the database schema and metrics calculator.

#### Automated Integration
Integrate with CI/CD pipelines to automatically capture build results and test outcomes.

#### Team Evaluations
Multiple developers can use the same framework instance, allowing for team-wide tool evaluations and aggregated insights.