"""
Analyzer provider contract verification tests.

These tests verify the Analyzer service satisfies the contract expected
by the Backend service (LotusBackend consumer).

To run:
    1. Generate pact files: cd services/backend && go test ./internal/grpc/contract_test/ -v -run TestBackendAnalyzerContract
    2. Start analyzer dependencies: make ci-analyzer-up
    3. Start the analyzer: cd services/analyzer && PACT_TESTING=true uv run uvicorn src.main:app --port 8083
    4. Run verification: cd services/analyzer && uv run pytest tests/contract/ -v

For CI, use the Pact Broker instead of local files.
"""

import os
from pathlib import Path
import socket

from pact import Verifier
import pytest

PACT_DIR = Path(__file__).resolve().parents[3] / "backend" / "pacts"
PACT_FILE = PACT_DIR / "LotusBackend-LotusAnalyzer.json"


@pytest.fixture(scope="module")
def pact_file():
    """Return the path to the pact file, or skip if it doesn't exist."""
    if not PACT_FILE.exists():
        pytest.skip(
            f"Pact file not found at {PACT_FILE}. "
            "Generate it by running backend consumer contract tests first: "
            "cd services/backend && go test ./internal/grpc/contract_test/ -v"
        )
    return PACT_FILE


@pytest.fixture(scope="module", autouse=True)
def require_contract_env_and_provider():
    """Skip by default unless contract verification is explicitly requested."""
    if os.environ.get("RUN_PACT_PROVIDER_VERIFY", "").lower() not in {"1", "true", "yes"}:
        pytest.skip(
            "Skipping provider contract verification. Set RUN_PACT_PROVIDER_VERIFY=true to enable."
        )

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        if sock.connect_ex(("127.0.0.1", 8083)) != 0:
            pytest.skip(
                "Analyzer provider is not running on localhost:8083. "
                "Start it with PACT_TESTING=true before running this test."
            )


def test_analyzer_satisfies_backend_contract(pact_file):
    """Verify the Analyzer satisfies the Backend's consumer contract.

    This test requires:
    - A running Analyzer service at http://localhost:8083 with PACT_TESTING=true
    - The pact file from backend consumer tests at services/backend/pacts/
    """
    verifier = (
        Verifier("LotusAnalyzer")
        .add_transport(url="http://localhost:8083")
        .add_source(str(pact_file))
        .state_handler(
            "http://localhost:8083/v1/pact/provider-states",
            teardown=True,
            body=True,
        )
    )

    verifier.verify()
