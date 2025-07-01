#!/bin/bash
# Setup repo

# Create symlink
ln -s ~/.config/auth.cfg source/auth.cfg

# Create a virtual environment
python3 -m venv pyenv

# Activate the virtual environment (MacOS/Linux)
source pyenv/bin/activate

# Install dependencies
pip install -r requirements.txt