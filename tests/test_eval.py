from sciwork.evaluation import evaluate


def test_evaluation_counts_are_consistent():
    x = evaluate()
    assert x["queries"] == len(x["breakdown"])
    assert 0 <= x["hit_or_abstention_rate"] <= 1


def test_eval_rejects_empty_fixture(tmp_path):
    from pytest import raises
    p = tmp_path / "empty.jsonl"
    p.write_text("")
    with raises(ValueError):
        evaluate(p)
