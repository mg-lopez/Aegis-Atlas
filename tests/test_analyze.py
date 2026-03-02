"""Unit tests for analyze helper functions."""

from __future__ import annotations

import numpy as np
import pytest

import analyze


def test_compute_simple_cloud_mask_marks_expected_classes():
    scl = np.array([[1, 8, 9], [10, 11, 4]])
    mask = analyze.compute_simple_cloud_mask(scl)
    assert np.array_equal(mask, np.array([[False, True, True], [True, True, False]]))


def test_detect_change_from_band_difference_returns_alert_and_score():
    before = np.array([[1.0, 1.0], [1.0, 1.0]])
    after = np.array([[2.0, 2.0], [2.0, 2.0]])

    result = analyze.detect_change_from_band_difference(before, after, change_threshold=0.2)

    assert result["change_score"] == pytest.approx(1 / 3)
    assert result["alert"] is True
    assert result["threshold"] == 0.2


def test_change_score_honors_cloud_masks():
    baseline = np.array([[[1, 1, 1], [10, 10, 10]]], dtype=np.float32)
    recent = np.array([[[2, 2, 2], [100, 100, 100]]], dtype=np.float32)
    baseline_cloud = np.array([[False, True]])
    recent_cloud = np.array([[False, True]])

    score = analyze.change_score(baseline, recent, baseline_cloud, recent_cloud)
    assert score == pytest.approx((2 - 1) / (2 + 1), rel=1e-5)
