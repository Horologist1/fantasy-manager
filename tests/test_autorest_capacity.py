"""Job capacity rules: only active workers hold a slot; Rest reservations never block."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "game/python-packages"))
from fm_autorest.capacity import can_restore_reserved_job, claim_job_slot, count_job_slots


def brothel(limit=7):
    """Seven strippers at capacity, then one of them moved to Rest."""
    workers = [{"name": "W%d" % i} for i in range(limit)] + [{"name": "New"}, {"name": "Extra"}]
    jobs = {"W%d" % i: "stripper" for i in range(limit)}
    jobs["W0"] = "rest"
    workers[0]["previous_profession"] = "stripper"
    return workers, jobs


def test_reservation_is_counted_but_not_a_holder():
    workers, jobs = brothel()
    assert count_job_slots(jobs, workers, "stripper") == 7
    assert count_job_slots(jobs, workers, "stripper", include_reservations=False) == 6


def test_rested_worker_does_not_block_another_worker():
    """The reported bug: (6/7) shown, yet nobody could be assigned to the job."""
    workers, jobs = brothel()
    occupied = count_job_slots(jobs, workers, "stripper")
    active = count_job_slots(jobs, workers, "stripper", include_reservations=False)
    allowed, occupied, active = claim_job_slot(workers[7], None, "stripper", occupied, active, 7)
    assert allowed and active == 7
    # Now the job is genuinely full.
    allowed, _, _ = claim_job_slot(workers[8], None, "stripper", occupied, active, 7)
    assert not allowed


def test_two_rested_workers_leave_two_free_slots():
    workers, jobs = brothel()
    jobs["W1"] = "rest"
    workers[1]["previous_profession"] = "stripper"
    active = count_job_slots(jobs, workers, "stripper", include_reservations=False)
    assert active == 5
    allowed, _, active = claim_job_slot(workers[7], None, "stripper", 7, active, 7)
    assert allowed and active == 6
    allowed, _, active = claim_job_slot(workers[8], None, "stripper", 7, active, 7)
    assert allowed and active == 7


def test_rested_worker_returns_only_when_room_remains():
    workers, jobs = brothel()
    assert can_restore_reserved_job(jobs, workers, "stripper", 7)
    jobs["New"] = "stripper"
    assert not can_restore_reserved_job(jobs, workers, "stripper", 7)
    allowed, _, _ = claim_job_slot(workers[0], "rest", "stripper", 7, 7, 7)
    assert not allowed


def test_rested_worker_can_take_own_slot_back():
    workers, jobs = brothel()
    allowed, occupied, active = claim_job_slot(workers[0], "rest", "stripper", 7, 6, 7)
    assert allowed and occupied == 7 and active == 7


def test_same_job_and_rest_targets_are_free():
    workers, jobs = brothel()
    assert claim_job_slot(workers[1], "stripper", "stripper", 7, 7, 7)[0]
    assert not claim_job_slot(workers[1], "stripper", "rest", 7, 7, 7)[0]
    assert not claim_job_slot(workers[7], None, "stripper", 0, 0, 0)[0]
