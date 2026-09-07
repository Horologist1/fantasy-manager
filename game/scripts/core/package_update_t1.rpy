# Release-epoch cleanup: remove bytecode left by earlier installations before
# any fm_* module is preloaded at init -1 or later. T3 deliberately advances
# the epoch so installs that already ran the T1/T2 cleanup run it once more.
init -999 python hide:
    import package_update_t1

    _fm_cache_cleanup = package_update_t1.ensure_clean_python_package_cache(config.gamedir, "0.9.6t3-package-cache-v3")
    if _fm_cache_cleanup["errors"]:
        renpy.log("PACKAGE_CACHE_CLEANUP: retry required: %r" % (_fm_cache_cleanup["errors"],))
    elif _fm_cache_cleanup["cleaned"]:
        renpy.log(
            "PACKAGE_CACHE_CLEANUP: removed %d bytecode files and %d cache directories"
            % (_fm_cache_cleanup["removed_files"], _fm_cache_cleanup["removed_dirs"])
        )
