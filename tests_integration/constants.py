from enum import Enum


class CoverageType(Enum):
    LCOV = "lcov"
    COBERTURA = "cobertura"
    JACOCO = "jacoco"


MODEL="gpt-4o-2024-11-20"
MAX_ITERATIONS=3
DESIRED_COVERAGE=70
API_BASE="http://localhost:11434"
MAX_RUN_TIME=30
