def should_stop(
    num_answered: int,
    max_questions: int,
    elapsed_time_sec: float,
    time_limit_sec: float | None,
    std_error: float,
    threshold: float = 0.3,
) -> bool:
    """Termination conditions for an adaptive test.

    - Max question count reached
    - Time limit exceeded
    - Standard error below threshold
    """
    if num_answered >= max_questions:
        return True
    if time_limit_sec is not None and elapsed_time_sec >= time_limit_sec:
        return True
    if std_error <= threshold:
        return True
    return False
