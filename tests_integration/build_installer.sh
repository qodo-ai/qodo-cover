#!/bin/bash

## Utility script to build the installer for the cover-agent project
# This should be run from the root of the repository

set -e  # Exit immediately if a command exits with a non-zero status
set -o pipefail  # Exit if any command in a pipeline fails
# set -x  # Print commands and their arguments as they are executed

echo "Building cover-agent-installer..."
# Build the installer within a Docker container
docker build --platform linux/amd64 -t cover-agent-installer -f Dockerfile .

# Create dist directory if it doesn't exist
mkdir -p dist

# Run the container and mount the dist directory
docker run --platform linux/amd64 --rm --volume "$(pwd)/dist:/app/dist" cover-agent-installer
