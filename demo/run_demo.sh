#!/bin/bash

# AI Coding Assistant Evaluation Framework - Interactive Demo
# This script demonstrates the complete framework capabilities

echo "🚀 AI Coding Assistant Evaluation Framework - LIVE DEMO"
echo "========================================================"

# Check if framework is set up
if [ ! -d "venv" ]; then
    echo "❌ Framework not set up. Please run ./setup.sh first"
    exit 1
fi

# Activate environment
source venv/bin/activate
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

echo "📋 DEMONSTRATION SCENARIO:"
echo "Comparing Cursor vs GitHub Copilot for bug fix tasks"
echo ""

# Run the demonstration script
echo "🎯 Running automated demonstration..."
python demo/sample_session.py

echo ""
echo "📊 AVAILABLE CLI COMMANDS FOR REAL USAGE:"
echo ""
echo "Session Management:"
echo "  eval-framework start-session --help"
echo "  eval-framework end-session --help"
echo ""
echo "Analysis Commands:"
echo "  eval-framework reports quick-analysis --help"
echo "  eval-framework reports session-report --help"
echo "  eval-framework reports comparison-report --help"
echo ""
echo "🔍 Try these commands now:"
echo ""
echo "# Quick analysis of sample data"
echo "python -m src.analysis.cli_reports quick-analysis --tool cursor"
echo ""
echo "# List all sessions"
echo "python -m src.analysis.cli_reports list-sessions"
echo ""
echo "# Available tools"
echo "python -m src.analysis.cli_reports available-tools"
echo ""
echo "💡 TIP: Use --help on any command to see all options"