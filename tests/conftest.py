"""
tests/conftest.py
=================
Shared pytest configuration and fixtures for Phase 1 tests.
"""

import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="Run integration tests that require network access.",
    )


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "integration: mark test as requiring network access (deselected by default).",
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--run-integration"):
        return  # run everything
    skip_integration = pytest.mark.skip(reason="Add --run-integration to run network tests")
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_integration)
