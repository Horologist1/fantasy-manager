"""The merchant's Elite Emporium offer: same grace period for late openers, honest cost, and a return date."""
import json
from pathlib import Path
import textwrap
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "game/scripts/events/events_logic.rpy").read_text(encoding="utf-8")


def function(name):
    lines = SOURCE.splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith("    def " + name + "("))
    end = start + 1
    while end < len(lines):
        line = lines[end]
        if line.strip() and not line.lstrip().startswith("#") and len(line) - len(line.lstrip()) <= 4:
            break
        end += 1
    return textwrap.dedent("\n".join(lines[start:end]))


def load(name):
    env = {"renpy": SimpleNamespace(log=lambda m: None),
           "ELITE_EMPORIUM_OFFER_EVENT_IDS": ("shop_owner_expansion", "shop_owner_expansion_retry", "shop_owner_expansion_guaranteed"),
           "ELITE_EMPORIUM_RETURN_COOLDOWN_DAYS": 21}
    exec(function(name), env)
    return env[name]


def events():
    return {e["id"]: e for e in json.loads((ROOT / "game/data/events/events_shops.json").read_text(encoding="utf-8"))}


def test_guaranteed_offer_waits_twenty_days_after_the_market_opens():
    start = events()["shop_owner_expansion_guaranteed"]["conditions"]["start_when"]
    assert start == "after_days:120 AND after_days_from_flag:shop2_unlock_timestamp,20"
    first = events()["shop_owner_expansion"]["conditions"]["start_when"]
    assert "after_days_from_flag:shop2_unlock_timestamp,20" in first


def test_decline_options_say_when_the_merchant_returns():
    table = events()
    declines = [c["option"] for eid in ("shop_owner_expansion", "shop_owner_expansion_retry", "shop_owner_expansion_guaranteed")
                for c in table[eid]["choices"] if "money" not in (c.get("effect") or {})]
    assert len(declines) == 3
    assert all("returns in about three weeks" in text for text in declines)


def test_cost_warning_only_when_the_player_cannot_pay():
    warn = load("event_choice_cost_warning")
    assert warn({"money": -10000}, 10000) == ""
    assert warn({"money": -10000}, 12000) == ""
    assert warn({"money": 500}, 0) == ""
    assert warn({}, 0) == "" and warn(None, 0) == "" and warn({"money": "x"}, 0) == ""
    assert warn({"money": -10000}, 9000) == "You have 9000 coins: this puts you 1000 in debt"
    assert warn({"money": -10000}, 3000) == "You have 3000 coins: this leaves you at -7000, past the bankruptcy line"
    assert warn({"money": -10000}, 5000) == "You have 5000 coins: this leaves you at -5000, past the bankruptcy line"
    assert warn({"money": -800}, 500, -5000) == "You have 500 coins: this puts you 300 in debt"


def test_return_hint_appears_only_after_an_offer():
    hint = load("elite_emporium_return_hint")
    assert hint({}, {}, {}, 130) == ""
    assert hint({"shop2_unlocked": True}, {}, {}, 130) == ""
    assert hint({"shop3_unlocked": True, "shop_expansion_declined": True}, {"shop_owner_expansion": 100}, {}, 130) == ""
    assert hint(None, None, None, 130) == ""


def test_return_hint_counts_down_from_the_last_offer():
    hint = load("elite_emporium_return_hint")
    assert hint({}, {"shop_owner_expansion_guaranteed": 121}, {}, 122) == "The merchant returns with her offer in about 20 days."
    assert hint({}, {"shop_owner_expansion_guaranteed": 121}, {}, 141) == "The merchant returns with her offer in about 1 day."
    assert hint({}, {"shop_owner_expansion_guaranteed": 121}, {}, 142) == "The merchant may return with her offer any day now."
    assert hint({"shop_expansion_declined": True, "shop_expansion_decline_timestamp": 50}, {}, {}, 60) == "The merchant returns with her offer in about 11 days."
    # Occurrence recorded but no day stamp (very old save): still says she returns.
    assert hint({}, {}, {"shop_owner_expansion": 1}, 60) == "The merchant will return with her offer."
    # A literal string stamp (failed eval in an old save) is ignored, not crashed on.
    assert hint({"shop_expansion_declined": True, "shop_expansion_decline_timestamp": "[calculate_total_days()]"}, {}, {}, 60) == "The merchant will return with her offer."
