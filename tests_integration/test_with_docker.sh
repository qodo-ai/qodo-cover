#!/bin/bash

set -e  # Exit immediately if a command exits with a non-zero status
set -x

# Initialize variables
MODEL=""
API_BASE=""
OPENAI_API_KEY="${OPENAI_API_KEY:-}"
ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:-}"
DOCKERFILE=""
DOCKER_IMAGE=""
SOURCE_FILE_PATH=""
TEST_FILE_PATH=""
TEST_COMMAND=""
COVERAGE_TYPE="cobertura"
CODE_COVERAGE_REPORT_PATH="coverage.xml"
MAX_ITERATIONS=3  # Default value
DESIRED_COVERAGE=70  # Default value
LOG_DB_PATH="${LOG_DB_PATH:-}"
SUPPRESS_LOG_FILES=""

# Function to clean up Docker container
cleanup() {
  if [ -n "$CONTAINER_ID" ]; then
    echo "Cleaning up..."
    docker stop "$CONTAINER_ID" || true
    docker rm "$CONTAINER_ID" || true
  fi
}

# Trap any errors or exits and run cleanup
trap cleanup EXIT

# Parse arguments
while [ "$#" -gt 0 ]; do
  case $1 in
    --model) MODEL="$2"; shift ;;
    --api-base) API_BASE="$2"; shift ;;
    --openai-api-key) OPENAI_API_KEY="$2"; shift ;;
    --dockerfile) DOCKERFILE="$2"; shift ;;
    --docker-image) DOCKER_IMAGE="$2"; shift ;;
    --source-file-path) SOURCE_FILE_PATH="$2"; shift ;;
    --test-file-path) TEST_FILE_PATH="$2"; shift ;;
    --test-command) TEST_COMMAND="$2"; shift ;;
    --coverage-type) COVERAGE_TYPE="$2"; shift ;;
    --code-coverage-report-path) CODE_COVERAGE_REPORT_PATH="$2"; shift ;;
    --max-iterations) MAX_ITERATIONS="$2"; shift ;;
    --desired-coverage) DESIRED_COVERAGE="$2"; shift ;;
    --log-db-path) LOG_DB_PATH="$2"; shift ;;
    --suppress-log-files) SUPPRESS_LOG_FILES="--suppress-log-files" ;;
    *) echo "Unknown parameter passed: $1"; exit 1 ;;
  esac
  shift
done

# Ensure mandatory arguments are provided
if [ -z "$SOURCE_FILE_PATH" ] || [ -z "$TEST_FILE_PATH" ] || [ -z "$TEST_COMMAND" ]; then
  echo "Missing required parameters: --source-file-path, --test-file-path, or --test-command"
  exit 1
fi

# Ensure either DOCKERFILE or DOCKER_IMAGE is provided
if [ -z "$DOCKERFILE" ] && [ -z "$DOCKER_IMAGE" ]; then
  echo "Missing required parameters: either --dockerfile or --docker-image must be provided"
  exit 1
fi

# Build or pull the Docker image
if [ -n "$DOCKERFILE" ]; then
  echo "Building the Docker image..."
  docker build --platform linux/amd64 -t cover-agent-image -f "$DOCKERFILE" "$(dirname "$DOCKERFILE")"
else
  echo "Pulling the Docker image..."
  docker pull "$DOCKER_IMAGE"
  docker tag "$DOCKER_IMAGE" cover-agent-image
fi

if [ -n "$OPENAI_API_KEY" ]; then
  ARGS="$ARGS -e OPENAI_API_KEY=$OPENAI_API_KEY"
fi

if [ -n "$ANTHROPIC_API_KEY" ]; then
  ARGS="$ARGS -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY"
fi

if [ -n "$LOG_DB_PATH" ]; then
  LOG_DB_NAME=$(basename "$LOG_DB_PATH")
  ARGS="$ARGS --volume $LOG_DB_PATH:/$LOG_DB_NAME"
fi

# Start the container in detached mode with the environment variable if set
echo "Starting the container..."
CONTAINER_ID=$(sh -c "docker run -d $ARGS cover-agent-image tail -f /dev/null")

# Ensure the container started successfully
if [ -z "$CONTAINER_ID" ]; then
  echo "Failed to start the container."
  exit 1
fi

# Copy the cover-agent binary into the running container
echo "Copying cover-agent binary into the container..."
docker cp dist/cover-agent "$CONTAINER_ID":/usr/local/bin/cover-agent

# Run the cover-agent command inside the running container
echo "Running the cover-agent command..."
COMMAND="/usr/local/bin/cover-agent \
  --source-file-path \"$SOURCE_FILE_PATH\" \
  --test-file-path \"$TEST_FILE_PATH\" \
  --code-coverage-report-path \"$CODE_COVERAGE_REPORT_PATH\" \
  --test-command \"$TEST_COMMAND\" \
  --coverage-type \"$COVERAGE_TYPE\" \
  --desired-coverage $DESIRED_COVERAGE \
  --max-iterations $MAX_ITERATIONS \
  --strict-coverage"

if [ -n "$MODEL" ]; then
  COMMAND="$COMMAND --model \"$MODEL\""
fi

if [ -n "$API_BASE" ]; then
  COMMAND="$COMMAND --api-base \"$API_BASE\""
fi

if [ -n "$LOG_DB_PATH" ]; then
  COMMAND="$COMMAND --log-db-path \"/$LOG_DB_NAME\""
fi

if [ -n "$SUPPRESS_LOG_FILES" ]; then
  COMMAND="$COMMAND $SUPPRESS_LOG_FILES"
fi

if [ -n "$OPENAI_API_KEY" ] && [ -n "$ANTHROPIC_API_KEY" ]; then
  docker exec -e OPENAI_API_KEY="$OPENAI_API_KEY" -e ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" "$CONTAINER_ID" bash -c "$COMMAND"
elif [ -n "$OPENAI_API_KEY" ]; then
  docker exec -e OPENAI_API_KEY="$OPENAI_API_KEY" "$CONTAINER_ID" bash -c "$COMMAND"
elif [ -n "$ANTHROPIC_API_KEY" ]; then
  docker exec -e ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" "$CONTAINER_ID" bash -c "$COMMAND"
else
  docker exec "$CONTAINER_ID" bash -c "$COMMAND"
fi

echo "Done."
