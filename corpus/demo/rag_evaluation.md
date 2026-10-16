# Retrieval and RAG evaluation methodology (RAG 自动化评测)
DEMO ONLY — synthetic teaching note, not a paper or a patent; no experimental measurements are claimed.
Domain: RAG evaluation, hit at k, MRR, citation accuracy, benchmark.
Retrieval evaluation can use Hit@k (fraction of queries with an expected source in the first k results) and mean reciprocal rank (MRR), which rewards placing the first relevant document high in the ranking. Gold labels must be created independently of the retrieval algorithm.
Citation validity asks whether cited identifiers exist among returned evidence; this is weaker than factual faithfulness, which additionally asks whether claims are supported by the referenced passages. Question answering should assess abstention on unanswerable queries.
研究要点：RAG 评测要区分检索 Hit@k、MRR、答案正确率、引文有效性和忠实度 Faithfulness；小型合成测试集的成绩不能外推为真实用户效果。
Engineering recommendation: Maintain evaluation data under version control, compare baseline against hybrid search, and record failure cases.
