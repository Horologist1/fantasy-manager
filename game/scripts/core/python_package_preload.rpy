# Central import barrier for every shipped fm_* module.
# Ren'Py may refuse first-time file imports during screen prediction and leave
# partial modules in sys.modules. Keep these modules pure and import-safe.
init -1 python hide:
    import fm_academy.curriculum
    import fm_autorest.capacity
    import fm_events.building_policy
    import fm_events.earnings
    import fm_events.manager_gating
    import fm_franchise.holdings
    import fm_lanista.arena_feedback
    import fm_orientation.rules
    import fm_performance.reporting
    import fm_roster.autofill
    import fm_roster.presets
    import fm_roster.selection
    import fm_roster.sorting
