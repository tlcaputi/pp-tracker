#!/bin/bash

# Set the directory to your project
cd /home/theo/pp-tracker

# Initialize the counter
counter=0

# Use the pyenv local Python to run the script
while true; do

    # Run the Python script using the local pyenv Python version
    pyenv exec python /home/theo/pp-tracker/pp-selenium.py

    # Perform git operations every 5 runs
    if ((counter % 1 == 0)); then
        timestamp=$(date '+%Y-%m-%d %H:%M:%S')
        git add .
        git commit -m "updating parlayplay plot for ${timestamp}"
        git push
        echo "Update pushed to git at ${timestamp}"
    fi

    # Increment the counter
    ((counter++))

    # Wait for 3 minutes
    sleep 30
done
