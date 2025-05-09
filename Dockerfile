# Dockerfile to build installer for Cover Agent
FROM python:3.12-bookworm

WORKDIR /app

# Copy all files
COPY . .

# Install required packages
RUN make setup-installer
RUN poetry install

# Run the make installer as a CMD
CMD ["make", "installer"]
