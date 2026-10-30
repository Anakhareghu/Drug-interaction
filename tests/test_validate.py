"""
tests/test_validate.py
======================
Unit tests for Phase 1 validation module.
"""

import json
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from validate import (
    ValidationResult,
)


class TestValidationResult:
    def test_empty_result_has_no_failures(self):
        vr = ValidationResult("test")
        assert vr.n_failures == 0
        assert vr.n_warnings == 0

    def test_ok_adds_check(self):
        vr = ValidationResult("test")
        vr.ok("some check", "detail")
        assert len(vr.checks) == 1
        assert vr.n_failures == 0
        assert vr.n_warnings == 0

    def test_fail_increments_failures(self):
        vr = ValidationResult("test")
        vr.fail("bad thing")
        assert vr.n_failures == 1
        assert "[FAIL]" in vr.checks[0][0]

    def test_warn_increments_warnings(self):
        vr = ValidationResult("test")
        vr.warn("possible issue")
        assert vr.n_warnings == 1
        assert "[WARN]" in vr.checks[0][0]

    def test_report_contains_name(self):
        vr = ValidationResult("My Section")
        report = vr.report()
        assert "My Section" in report

    def test_report_shows_pass_when_no_failures(self):
        vr = ValidationResult("test")
        vr.ok("all good")
        assert "PASS" in vr.report()

    def test_report_shows_fail_when_failures(self):
        vr = ValidationResult("test")
        vr.fail("something broke")
        assert "FAIL" in vr.report()
