"""Gender-split daily stories must not change how often a worker sees a story.

`event_daily_exec.rpy` filters `worker_gender_requirement` strictly: a story
requiring "male" is dropped for every female worker and vice versa (line 517 in
the picker, line 912 in the manager path). Weighted selection then runs over
whatever survived.

So a single genderless story of weight W can be replaced by a `_male` and a
`_female` variant of weight W each, and every worker still sees exactly one of
them at exactly weight W. That is what makes the prose able to name anatomy
instead of writing around an unknown body.

It only holds while three things stay true, which is what this module pins:

1. Both twins carry the same weight and the same mechanics. A drifting weight
   silently makes one gender's version rarer.
2. The genderless original is gone. Keeping it eligible alongside the twins
   would add W back on top and skew the pool - the failure mode the editorial
   spec calls out by name.
3. Orientation filters partition rather than overlap. A worker must never match
   both the straight variant and its Gay/Lesbian counterpart.
"""

import json
import os
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILDING_TYPES = os.path.join(
    REPO_ROOT, "game", "data", "buildings", "building_types.json"
)

# Everything a story split off a single genderless original inherited from it.
# These twins started as byte copies, so they must stay mechanically identical;
# only the prose may diverge.
# `report` is deliberately absent: it names the act, and the act is anatomical.
# The pre-existing hand pair already establishes the convention - the male
# variant reports "Client paid for Fingering" and the female one "Client paid
# for a Handjob" - so an oral pair must be free to say "Oral" for one and
# "a Blowjob" for the other rather than mislabelling one gender's scene.
COPY_FIELDS = (
    "weight",
    "skill_options",
    "earnings",
    "consequences",
    "difficulty_modifier",
    "story_image",
    "failure_image",
    "positive_traits",
    "negative_traits",
)

# Gender pairs that were authored separately (anal, hand, homo) are NOT copies of
# each other and legitimately differ: "Client paid for Fingering" against "Client
# paid for a Handjob", a health cost for the receiving partner that the giving
# one does not carry, its own art, its own relevant traits. Only `weight` governs
# how often the pool offers the story, so only `weight` has to match for the
# distribution argument to hold.
DISTRIBUTION_FIELD = "weight"

# Stories that were genderless before 2026-09-10 and were split so the text could
# be explicit. The originals must stay gone.
SPLIT_ORIGINALS = (
    "prostitute_vanilla_client",
    "prostitute_oral_client",
    "prostitute_libido20_too_eager",
    "masseuse_oral_steam_and_mouth",
    "masseuse_hand_oil_edge",
    "ea_prostitute_vanilla_client",
    "ea_prostitute_bdsm_client",
    "ea_prostitute_oral_client",
    "ea_prostitute_group_clients",
    "ea_prostitute_vip_client",
    "ea_prostitute_extreme_client",
    "expert_libido20_lost_control",
    "stripper_lapdance_escalation",
    "monster_taming_seduction",
    "courtesan_seduction_nsfw",
    "courtesan_vip_private_chamber",
    "pleasure_servant_noble_client",
    "pleasure_servant_libido20_overwhelming_desire",
)

GENDERS = ("male", "female")


def load_professions():
    with open(BUILDING_TYPES, encoding="utf-8") as handle:
        data = json.load(handle)
    for building in data["building_types"]:
        for profession in building["professions"]:
            yield building["id"], profession


def story_index():
    out = {}
    for building_id, profession in load_professions():
        for story in profession.get("daily_stories", []):
            out[story["id"]] = (building_id, profession["id"], story)
    return out


def worker_matches(story, gender, traits):
    """Mirror of the engine's eligibility filter for the fields under test."""
    requirement = story.get("worker_gender_requirement")
    if requirement is not None and requirement != gender:
        return False
    excluded = set(story.get("excluded_traits") or [])
    if excluded & traits:
        return False
    required = set(story.get("required_traits") or [])
    if required and not required.issubset(traits):
        return False
    return True


class GenderSplitPreservesDistribution(unittest.TestCase):
    def test_split_originals_are_no_longer_eligible(self):
        index = story_index()
        still_present = [sid for sid in SPLIT_ORIGINALS if sid in index]
        self.assertEqual(
            [],
            still_present,
            "A genderless original is still in the pool alongside its gendered "
            "twins, which adds its weight back on top and skews selection: %s"
            % still_present,
        )

    def test_split_originals_have_both_variants(self):
        index = story_index()
        missing = [
            "%s_%s" % (sid, gender)
            for sid in SPLIT_ORIGINALS
            for gender in GENDERS
            if "%s_%s" % (sid, gender) not in index
        ]
        self.assertEqual([], missing, "Missing gender variant(s): %s" % missing)

    def test_split_twins_remain_faithful_copies(self):
        """Each story split on 2026-09-10 began as a byte copy of one original."""
        index = story_index()
        problems = []
        for base in SPLIT_ORIGINALS:
            male = index.get("%s_male" % base)
            female = index.get("%s_female" % base)
            if not male or not female:
                continue
            for field in COPY_FIELDS:
                if male[2].get(field) != female[2].get(field):
                    problems.append(
                        "%s :: _male vs _female differ on %r (%r != %r)"
                        % (base, field, male[2].get(field), female[2].get(field))
                    )
        self.assertEqual(
            [],
            problems,
            "A split twin drifted from its copy; only prose may differ:\n  "
            + "\n  ".join(problems),
        )

    def test_every_gender_pair_shares_its_weight(self):
        """Weight is what decides frequency, so twins must not drift on it."""
        index = story_index()
        problems = []
        for story_id, (building_id, profession_id, story) in sorted(index.items()):
            if not story_id.endswith("_male"):
                continue
            twin_id = story_id[: -len("_male")] + "_female"
            if twin_id not in index:
                continue
            twin = index[twin_id][2]
            if story.get(DISTRIBUTION_FIELD) != twin.get(DISTRIBUTION_FIELD):
                problems.append(
                    "%s/%s :: %s weight %r vs %s weight %r"
                    % (
                        building_id,
                        profession_id,
                        story_id,
                        story.get(DISTRIBUTION_FIELD),
                        twin_id,
                        twin.get(DISTRIBUTION_FIELD),
                    )
                )
        self.assertEqual(
            [],
            problems,
            "One gender would see the act more often than the other:\n  "
            + "\n  ".join(problems),
        )

    def test_each_worker_profile_sees_one_variant_of_each_split_story(self):
        """The whole point: same weight reaches every worker, exactly once."""
        index = story_index()
        profiles = (
            ("male", frozenset()),
            ("female", frozenset()),
            ("male", frozenset({"Gay"})),
            ("female", frozenset({"Lesbian"})),
        )
        for base in SPLIT_ORIGINALS:
            variants = [
                story for sid, (_b, _p, story) in index.items()
                if sid == base or sid.startswith(base + "_")
            ]
            for gender, traits in profiles:
                eligible = [s for s in variants if worker_matches(s, gender, traits)]
                self.assertEqual(
                    1,
                    len(eligible),
                    "%s: worker (%s, %s) matches %d variants (%s); it must match "
                    "exactly one, or the act becomes more or less frequent for "
                    "that worker than before the split."
                    % (
                        base,
                        gender,
                        sorted(traits) or "no orientation trait",
                        len(eligible),
                        [s["id"] for s in eligible],
                    ),
                )

    def test_orientation_variants_do_not_overlap_with_their_straight_twin(self):
        """A Gay worker must not match both the straight and the _gay variant."""
        index = story_index()
        problems = []
        for story_id, (_b, _p, story) in sorted(index.items()):
            for suffix, trait, gender in (
                ("_gay", "Gay", "male"),
                ("_lesbian", "Lesbian", "female"),
            ):
                if not story_id.endswith(suffix):
                    continue
                base = story_id[: -len(suffix)]
                for twin_id in ("%s_male" % base, "%s_female" % base, base):
                    twin = index.get(twin_id)
                    if not twin:
                        continue
                    traits = frozenset({trait})
                    if worker_matches(story, gender, traits) and worker_matches(
                        twin[2], gender, traits
                    ):
                        problems.append(
                            "%s worker matches both %s and %s"
                            % (trait, story_id, twin_id)
                        )
        self.assertEqual(
            [],
            problems,
            "Orientation filters must partition the roster, not overlap:\n  "
            + "\n  ".join(problems),
        )


if __name__ == "__main__":
    unittest.main()
