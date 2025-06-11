#!/bin/bash

# AI Coding Assistant Evaluation Framework - Linux/macOS Setup Script
# This script sets up the development environment and installs dependencies

set -e  # Exit on any error

echo "🚀 AI Coding Assistant Evaluation Framework Setup"
echo "=================================================="

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running on supported OS
check_os() {
    print_status "Checking operating system..."
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
        print_success "Detected Linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        print_success "Detected macOS"
    else
        print_error "Unsupported operating system: $OSTYPE"
        print_error "This script supports Linux and macOS. For Windows, use setup.bat"
        exit 1
    fi
}

# Check Python installation
check_python() {
    print_status "Checking Python installation..."
    
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        print_success "Python $PYTHON_VERSION found"
        
        # Check if Python version is 3.8 or higher
        PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
        PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
        
        if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
            print_error "Python 3.8 or higher is required. Found: $PYTHON_VERSION"
            exit 1
        fi
    else
        print_error "Python 3 is not installed"
        print_status "Installing Python 3..."
        
        if [ "$OS" = "linux" ]; then
            # Detect Linux distribution
            if command -v apt &> /dev/null; then
                sudo apt update
                sudo apt install -y python3 python3-pip python3-venv
            elif command -v yum &> /dev/null; then
                sudo yum install -y python3 python3-pip python3-venv
            elif command -v pacman &> /dev/null; then
                sudo pacman -S python python-pip
            else
                print_error "Unsupported Linux distribution. Please install Python 3.8+ manually."
                exit 1
            fi
        elif [ "$OS" = "macos" ]; then
            if command -v brew &> /dev/null; then
                brew install python3
            else
                print_error "Homebrew not found. Please install Python 3.8+ manually or install Homebrew first."
                exit 1
            fi
        fi
        
        print_success "Python 3 installed"
    fi
}

# Check pip installation
check_pip() {
    print_status "Checking pip installation..."
    
    if python3 -m pip --version &> /dev/null; then
        PIP_VERSION=$(python3 -m pip --version | cut -d' ' -f2)
        print_success "pip $PIP_VERSION found"
    else
        print_status "Installing pip..."
        
        if [ "$OS" = "linux" ]; then
            if command -v apt &> /dev/null; then
                sudo apt install -y python3-pip
            elif command -v yum &> /dev/null; then
                sudo yum install -y python3-pip
            elif command -v pacman &> /dev/null; then
                sudo pacman -S python-pip
            fi
        elif [ "$OS" = "macos" ]; then
            # pip should come with Python 3 on macOS
            print_warning "pip not found. Python installation may be incomplete."
        fi
        
        print_success "pip installed"
    fi
}

# Create virtual environment
setup_venv() {
    print_status "Setting up virtual environment..."
    
    if [ -d "venv" ]; then
        print_warning "Virtual environment already exists. Removing old environment..."
        rm -rf venv
    fi
    
    python3 -m venv venv
    print_success "Virtual environment created"
    
    # Activate virtual environment
    source venv/bin/activate
    print_success "Virtual environment activated"
    
    # Upgrade pip in virtual environment
    print_status "Upgrading pip in virtual environment..."
    python -m pip install --upgrade pip
    print_success "pip upgraded"
}

# Install dependencies
install_dependencies() {
    print_status "Installing Python dependencies..."
    
    if [ ! -f "requirements.txt" ]; then
        print_error "requirements.txt not found"
        exit 1
    fi
    
    # Install dependencies
    pip install -r requirements.txt
    print_success "Dependencies installed"
}

# Initialize database
init_database() {
    print_status "Initializing database..."
    
    # Create data directories
    mkdir -p data/raw data/processed data/backups
    mkdir -p reports/generated
    
    # Initialize database
    python -m src.database.database
    print_success "Database initialized"
}

# Create startup scripts
create_scripts() {
    print_status "Creating startup scripts..."
    
    # Create activation script
    cat > activate.sh << 'EOF'
#!/bin/bash
# Activate the AI Coding Evaluation Framework environment

echo "🔧 Activating AI Coding Evaluation Framework..."

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ Virtual environment activated"
    
    # Add current directory to Python path
    export PYTHONPATH="${PYTHONPATH}:$(pwd)"
    
    echo "🚀 Framework ready! Available commands:"
    echo "  python -m src.logging.cli --help    # Show CLI help"
    echo "  python -m src.logging.cli init      # Initialize database"
    echo "  python -m src.logging.cli start     # Start evaluation session"
    echo ""
    echo "📖 See docs/ARCHITECTURE.md for more information"
else
    echo "❌ Virtual environment not found. Run setup.sh first."
fi
EOF
    
    chmod +x activate.sh
    print_success "Activation script created (activate.sh)"
}

# Test installation
test_installation() {
    print_status "Testing installation..."
    
    # Test database module
    if python -m src.database.database &> /dev/null; then
        print_success "Database module working"
    else
        print_error "Database module test failed"
        exit 1
    fi
    
    # Test CLI module
    if python -m src.logging.cli --help &> /dev/null; then
        print_success "CLI module working"
    else
        print_error "CLI module test failed"
        exit 1
    fi
    
    print_success "Installation test passed"
}

# Main setup process
main() {
    echo ""
    print_status "Starting setup process..."
    echo ""
    
    check_os
    check_python
    check_pip
    setup_venv
    install_dependencies
    init_database
    create_scripts
    test_installation
    
    echo ""
    echo "🎉 Setup completed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Run: source activate.sh"
    echo "2. Test: python -m src.logging.cli init"
    echo "3. Start using: python -m src.logging.cli start"
    echo ""
    echo "📚 Documentation: docs/ARCHITECTURE.md"
    echo "🐛 Issues: Create an issue in the project repository"
    echo ""
}

# Run main function
main