from src.generators.vocabulary import load_vocabulary

def test_load_vocabulary():
    vocab = load_vocabulary("seeds/base_data.yaml")
    assert len(vocab.bases) >= 5
    assert len(vocab.ingredients) >= 15
    assert len(vocab.tags) >= 10
    assert len(vocab.actions) >= 10
    assert len(vocab.cities) >= 10
    assert len(vocab.first_names_female) > 0
    assert len(vocab.first_names_male) > 0
    assert len(vocab.last_names) > 0

    # Test city weights sum close to 1.0
    weights_sum = sum(c["weight"] for c in vocab.cities)
    assert 0.95 <= weights_sum <= 1.05
