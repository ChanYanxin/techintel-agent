from techintel.evaluation import evaluate


def test_eval_is_reproducible():
    a, b = evaluate(), evaluate()
    assert a == b
    assert a["total_queries"] == 20
    for method in ("word", "hybrid"):
        assert 0 <= a["methods"][method]["hit_at_3"] <= 1
        assert 0 <= a["methods"][method]["mrr"] <= 1
