from pipeline.embeddings.tfidf import TfidfEmbedder


def test_tfidf_fit_and_query_are_close_for_same_text():
    embedder = TfidfEmbedder(max_features=64)
    corpus = [
        "SQL injection parameterized queries interpreter",
        "broken access control insecure direct object references",
    ]
    embedder.fit(corpus)
    docs = embedder.embed_documents(corpus)
    query = embedder.embed_query("parameterized SQL injection")
    assert embedder.dimensions > 0
    assert len(docs[0]) == embedder.dimensions
    # First document should be closer to the injection query than the second.
    def dot(a, b):
        return sum(x * y for x, y in zip(a, b))
    assert dot(query, docs[0]) > dot(query, docs[1])
