"""Phase 0 Gate Test: Scaffold & Monorepo Package Health."""

import backend
import benchmarks
import data
import twin


def test_packages_importable():
    """Verify that all core monorepo packages are properly structured and importable."""
    assert backend.__version__ is not None
    assert twin.__version__ is not None
    assert data.__version__ is not None
    assert benchmarks.__version__ is not None
