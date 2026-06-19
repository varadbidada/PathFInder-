from engines.adaptive_engine import AdaptiveQuestionEngine, TRAITS, trait_question_counts


def test_question_bank_has_ten_questions_per_trait():
    counts = trait_question_counts()
    assert set(counts) == set(TRAITS)
    assert all(count == 10 for count in counts.values())


def test_session_tracks_questions_without_duplicates():
    engine = AdaptiveQuestionEngine(max_questions=6)
    session = engine.create_session()
    engine.select_opening_question(session)

    for _ in range(4):
        result = engine.process_answer(
            session,
            "I enjoy coding, solving logic problems, reading technical papers, and building useful apps.",
        )
        if result["is_complete"]:
            break

    asked_ids = session["asked_question_ids"]
    assert len(asked_ids) == len(set(asked_ids))
    assert len(session["asked_semantic_groups"]) == len(set(session["asked_semantic_groups"]))
    assert not set(asked_ids) & set(session["remaining_question_pool"])


def test_engine_stops_when_max_questions_reached():
    engine = AdaptiveQuestionEngine(max_questions=3)
    session = engine.create_session()
    engine.select_opening_question(session)

    result = None
    for _ in range(3):
        result = engine.process_answer(session, "Maybe. It depends, and I am still exploring.")
        if result["is_complete"]:
            break

    assert result is not None
    assert result["is_complete"] is True
    assert len(session["asked_question_ids"]) == 3


def test_report_returns_top_branches_and_trait_breakdown():
    engine = AdaptiveQuestionEngine(max_questions=4)
    session = engine.create_session()
    engine.select_opening_question(session)

    for _ in range(4):
        result = engine.process_answer(
            session,
            "I love software, automation, algorithms, and research-driven coding work.",
        )
        if result["is_complete"]:
            break

    report = engine.build_report(session)
    assert report["top_branches"]
    assert len(report["top_branches"]) <= 3
    assert set(report["trait_breakdown"]) == set(TRAITS)
    assert isinstance(report["confidence"], float)
