#!/usr/bin/env bash
set -euo pipefail

# Pre-commit setup script for repository integrity checks
echo "🛡️ Setting up pre-commit hooks for repository integrity..."

# Check if pre-commit is installed
if ! command -v pre-commit &> /dev/null; then
    echo "📦 Installing pre-commit..."
    if command -v pip &> /dev/null; then
        pip install pre-commit
    elif command -v pip3 &> /dev/null; then
        pip3 install pre-commit
    else
        echo "❌ pip not found. Please install Python and pip first."
        echo "   Then run: pip install pre-commit"
        exit 1
    fi
else
    echo "✅ pre-commit is already installed"
fi

# Install pre-commit hooks
echo "🔧 Installing pre-commit hooks..."
pre-commit install

# Run pre-commit on all files to test
echo "🧪 Testing pre-commit hooks..."
if pre-commit run --all-files; then
    echo "✅ Pre-commit hooks are working correctly!"
else
    echo "⚠️  Some pre-commit hooks failed. This is normal for the first run."
    echo "   The hooks will now run automatically on future commits."
fi

echo ""
echo "🎉 Pre-commit setup complete!"
echo ""
echo "📋 What this does:"
echo "   • Automatically checks for legacy repository paths before each commit"
echo "   • Verifies Git remote URL is correct"
echo "   • Runs standard code quality checks"
echo ""
echo "💡 To run manually: pre-commit run --all-files"
echo "💡 To skip hooks: git commit --no-verify"
