from apps.seedtest_api.services.adaptive import choose_next_question, simulate_adaptive_run


def test_choose_next_question_with_filters():
    pool = [
        {"question_id": 1, "discrimination": 1.0, "difficulty": -1.0, "guessing": 0.2, "topic_id": 10, "tags": ["algebra"]},
        {"question_id": 2, "discrimination": 1.5, "difficulty": 0.0, "guessing": 0.2, "topic_id": 20, "tags": ["geometry"]},
        {"question_id": 3, "discrimination": 0.5, "difficulty": 1.0, "guessing": 0.2, "topic_id": 10, "tags": ["algebra", "functions"]},
    ]
    # Filter to topic 10 only; id 1 vs 3: near theta=0, id 1 should be more informative
    item, info, idx = choose_next_question(0.0, pool, topic_ids=[10])
    assert item["question_id"] in {1, 3}


def test_simulate_adaptive_run():
    pool = [
        {"question_id": 1, "discrimination": 1.0, "difficulty": -1.0, "guessing": 0.2, "topic_id": 10, "tags": ["algebra"]},
        {"question_id": 2, "discrimination": 1.2, "difficulty": -0.2, "guessing": 0.2, "topic_id": 20, "tags": ["geometry"]},
        {"question_id": 3, "discrimination": 1.1, "difficulty": 0.2, "guessing": 0.2, "topic_id": 10, "tags": ["functions"]},
        {"question_id": 4, "discrimination": 0.8, "difficulty": 0.8, "guessing": 0.2, "topic_id": 30, "tags": ["algebra"]},
        {"question_id": 5, "discrimination": 1.3, "difficulty": 0.4, "guessing": 0.1, "topic_id": 20, "tags": ["geometry"]},
        {"question_id": 6, "discrimination": 0.9, "difficulty": 1.1, "guessing": 0.2, "topic_id": 40, "tags": ["calculus"]},
    ]
    est, ids = simulate_adaptive_run(pool, true_theta=0.3, max_items=5, sem_threshold=0.5)
    assert len(ids) >= 1
    assert -4.0 <= est <= 4.0
