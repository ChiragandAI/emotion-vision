from src.tracking.smoother import SimpleTracker


def test_tracker_assigns_track_ids() -> None:
    tracker = SimpleTracker(alpha=0.5, max_missing=2)
    first = tracker.update([(0, 0, 10, 10)], [[0.1, 0.9]])
    second = tracker.update([(1, 1, 11, 11)], [[0.2, 0.8]])
    assert first[0][0] == second[0][0]
