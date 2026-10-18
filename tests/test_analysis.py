import csv
import pytest
from sciwork.analysis import analyze_experiments


def test_sort_and_threshold():
    result = analyze_experiments(0.0005)
    assert result["total_matching"] == 3
    assert result["samples"][0]["sample_id"] == "EX-003"


def test_non_comparable_temperatures_flagged():
    assert not analyze_experiments()["comparable_temperatures"]


def test_only_25_degree_measurements_can_be_compared_if_preselected():
    samples = [s for s in analyze_experiments()["samples"] if s["temperature_c"] == 25]
    assert len(samples) == 4


@pytest.mark.parametrize("threshold", [-1.0, float("inf"), float("nan")])
def test_invalid_filter_rejected(threshold):
    with pytest.raises(ValueError):
        analyze_experiments(threshold)


def test_invalid_csv_schema(tmp_path):
    file = tmp_path / "wrong.csv"
    file.write_text("x,y\n1,2\n", encoding="utf-8")
    with pytest.raises(ValueError, match="headers"):
        analyze_experiments(path=file)


def test_empty_filter_stable():
    assert analyze_experiments(1)["samples"] == []
