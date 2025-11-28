"""
Pytest configuration and fixtures for the partnership analysis test suite.
"""

import pytest


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "extensive: marks tests as extensive (time-consuming) - run with -m extensive"
    )


@pytest.fixture(autouse=True)
def skip_extensive_by_default(request):
    """Skip extensive tests by default unless explicitly requested."""
    if request.node.get_closest_marker("extensive"):
        if not request.config.getoption("-m").startswith("extensive"):
            pytest.skip("Extensive test - run with -m extensive to include")