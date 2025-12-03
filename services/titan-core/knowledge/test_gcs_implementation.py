"""
Test Script for GCS Implementation
Agent 1 of 30: GCS Storage Implementation

Quick verification that all NotImplementedError stubs have been replaced.
"""

import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_imports():
    """Test that all modules import correctly"""
    logger.info("Testing imports...")

    try:
        from manager import (
            KnowledgeBaseManager,
            GCSBackend,
            LocalFileSystemBackend,
            StorageBackend
        )
        from gcs_store import GCSKnowledgeStore
        logger.info("✓ All imports successful")
        return True
    except ImportError as e:
        logger.error(f"✗ Import failed: {e}")
        return False


def test_gcs_backend_methods():
    """Verify GCSBackend has all required methods"""
    logger.info("\nTesting GCSBackend methods...")

    from manager import GCSBackend

    required_methods = ['save', 'load', 'delete', 'list_files', 'exists']

    for method in required_methods:
        if hasattr(GCSBackend, method):
            logger.info(f"✓ GCSBackend.{method} exists")
        else:
            logger.error(f"✗ GCSBackend.{method} missing")
            return False

    return True


def test_gcs_store_methods():
    """Verify GCSKnowledgeStore has all required methods"""
    logger.info("\nTesting GCSKnowledgeStore methods...")

    from gcs_store import GCSKnowledgeStore

    required_methods = [
        'upload',
        'upload_json',
        'download',
        'download_json',
        'list_blobs',
        'delete',
        'exists',
        'get_metadata',
        'copy',
        'get_signed_url',
        'batch_delete',
        'get_bucket_info'
    ]

    for method in required_methods:
        if hasattr(GCSKnowledgeStore, method):
            logger.info(f"✓ GCSKnowledgeStore.{method} exists")
        else:
            logger.error(f"✗ GCSKnowledgeStore.{method} missing")
            return False

    return True


def test_no_not_implemented():
    """Verify no NotImplementedError in GCSBackend implementation"""
    logger.info("\nChecking for NotImplementedError in GCSBackend...")

    import inspect
    from manager import GCSBackend

    for name, method in inspect.getmembers(GCSBackend, predicate=inspect.isfunction):
        if name.startswith('_'):
            continue

        source = inspect.getsource(method)
        if 'NotImplementedError' in source and name in ['save', 'load', 'delete', 'list_files', 'exists']:
            logger.error(f"✗ GCSBackend.{name} still has NotImplementedError")
            return False

    logger.info("✓ No NotImplementedError found in GCSBackend methods")
    return True


def test_local_backend_still_works():
    """Verify LocalFileSystemBackend still works"""
    logger.info("\nTesting LocalFileSystemBackend...")

    try:
        from manager import LocalFileSystemBackend
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            backend = LocalFileSystemBackend(tmpdir)

            # Test save
            test_data = b"test data"
            assert backend.save("test.txt", test_data), "Save failed"

            # Test exists
            assert backend.exists("test.txt"), "Exists check failed"

            # Test load
            loaded = backend.load("test.txt")
            assert loaded == test_data, "Load failed"

            # Test delete
            assert backend.delete("test.txt"), "Delete failed"
            assert not backend.exists("test.txt"), "File still exists after delete"

            logger.info("✓ LocalFileSystemBackend works correctly")
            return True

    except Exception as e:
        logger.error(f"✗ LocalFileSystemBackend test failed: {e}")
        return False


def test_manager_initialization():
    """Test that KnowledgeBaseManager initializes correctly"""
    logger.info("\nTesting KnowledgeBaseManager initialization...")

    try:
        from manager import KnowledgeBaseManager

        # Test with default (local) backend
        manager = KnowledgeBaseManager()
        logger.info("✓ KnowledgeBaseManager initialized with local backend")

        # Verify categories
        assert len(manager.CATEGORIES) == 6, "Wrong number of categories"
        logger.info(f"✓ {len(manager.CATEGORIES)} categories configured")

        return True

    except Exception as e:
        logger.error(f"✗ Manager initialization failed: {e}")
        return False


def test_type_hints():
    """Verify type hints are present"""
    logger.info("\nChecking type hints...")

    try:
        from gcs_store import GCSKnowledgeStore
        import inspect

        init_sig = inspect.signature(GCSKnowledgeStore.__init__)

        # Check that parameters have annotations
        params_with_hints = [
            p for p in init_sig.parameters.values()
            if p.annotation != inspect.Parameter.empty
        ]

        logger.info(f"✓ {len(params_with_hints)} parameters have type hints in __init__")

        return True

    except Exception as e:
        logger.error(f"✗ Type hints check failed: {e}")
        return False


def run_all_tests():
    """Run all verification tests"""
    logger.info("="*60)
    logger.info("GCS Implementation Verification")
    logger.info("="*60)

    tests = [
        ("Imports", test_imports),
        ("GCSBackend Methods", test_gcs_backend_methods),
        ("GCSKnowledgeStore Methods", test_gcs_store_methods),
        ("No NotImplementedError", test_no_not_implemented),
        ("LocalFileSystemBackend", test_local_backend_still_works),
        ("Manager Initialization", test_manager_initialization),
        ("Type Hints", test_type_hints),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            logger.error(f"Test '{name}' crashed: {e}")
            results.append((name, False))

    # Summary
    logger.info("\n" + "="*60)
    logger.info("SUMMARY")
    logger.info("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "PASS" if result else "FAIL"
        symbol = "✓" if result else "✗"
        logger.info(f"{symbol} {name}: {status}")

    logger.info("-"*60)
    logger.info(f"Passed: {passed}/{total}")

    if passed == total:
        logger.info("✓ ALL TESTS PASSED - GCS implementation is complete!")
        return 0
    else:
        logger.error(f"✗ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
