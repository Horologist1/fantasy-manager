# Nivel B del plan de playtest: matriz de save/load jugada en el motor real.
# Se inyecta SOLO en una copia desechable del proyecto (tools/qa_playtest_save.py).
# Cubre los casos 1-10 de PLAYTEST_PLAN_2026-09-28.md.
#
# El fichero se ejecuta dos veces con el MISMO savedir:
#   FM_QA_PHASE=1  siembra, guarda, deforma y carga in-process.
#   FM_QA_PHASE=2  proceso NUEVO que carga lo que dejo la fase 1 (caso 1).

init python:
    import os as _qb_os
    import json as _qb_json
    import copy as _qb_copy

    def _qb_phase():
        return _qb_os.environ.get("FM_QA_PHASE", "1")

    def qb_log(ok, message, actual=None):
        line = ("PASS: " if ok else "FAIL: ") + message
        if not ok and actual is not None:
            line += " -> %r" % (actual,)
        with open(_qb_os.path.join(config.savedir, "save-qa.txt"), "a", encoding="utf-8") as handle:
            handle.write(line + "\n")
        renpy.log("QA-B " + line)
        if not ok:
            raise AssertionError(line)

    def qb_step(name=None):
        if name is not None:
            renpy.session["qb_step"] = name
        return renpy.session.get("qb_step", "")

    # ------------------------------------------------------------------ setup

    def qb_worker(name, folder, gender="female", **extra):
        worker = {"name": name, "folder": folder, "gender": gender, "level": 3,
                  "skills": {"Service": 40, "Combat": 30, "Craft": 20},
                  "traits": ["Human"], "unique": False, "nsfw": False,
                  "assigned_building": "Unassigned", "inventory": []}
        worker.update(extra)
        ensure_worker_defaults(worker)
        return worker

    def qb_building(kind, owned=True):
        return {"price": 0, "base_level": 1, "assigned_servants": [], "servant_jobs": {},
                "type": kind, "reputation": 0, "max_workers": {}, "costs": 0, "owned": owned,
                "skill": 10, "skill_bonus": 0, "event_limit": 0, "training_focus": {}}

    def qb_setup():
        store.main_menu = False
        store.at_main_menu = False
        store.tutorial_active = False
        store.game_initialized = True
        store.is_new_game = False
        store.money = 24000
        store.current_day = 12
        store.current_month = 3
        store.current_year = 1
        persistent.nsfw_enabled = False
        persistent.worker_gender_filter = "both"
        persistent.intro_popups_enabled = False
        store.workers = [qb_worker("QA Margarita", "margarita"),
                         qb_worker("QA Chestnut", "chestnut"),
                         qb_worker("QA Holly", "holly")]
        store.available_workers = []
        store.manager_inventory = [["health_potion", 3, False]]
        store.event_flags = {"qa_b_marker": 7}
        set_save_blocked_context(None)

    # ------------------------------------- caso 6: navegacion con filtro vacio

    def qb_walk(node):
        yield node
        for child in node.visit():
            for descendant in qb_walk(child):
                yield descendant

    def _qb_is_text(value):
        # Duck-typing obligatorio: en el namespace del store, `str`/`list`/`dict`
        # estan ligados a los tipos de renpy.revertable (list.__module__ ==
        # "renpy.revertable"), asi que isinstance(valor_nativo_del_motor, list)
        # es False. Text.text es una lista NATIVA. Ver LA BIBLIA §1.
        return hasattr(value, "strip") and hasattr(value, "encode")

    def qb_captions(node):
        found = []
        for descendant in qb_walk(node):
            text = getattr(descendant, "text", None)
            if text is None:
                continue
            if _qb_is_text(text):
                found.append(text)
            elif hasattr(text, "__iter__"):
                found.extend([part for part in text if _qb_is_text(part)])
        return found

    def qb_button(screen_name, caption):
        """Devuelve (encontrado, accion) del boton cuyo texto es `caption`."""
        screen = renpy.get_screen(screen_name)
        if screen is None:
            return False, None
        for node in qb_walk(screen.child):
            action = getattr(node, "action", None)
            if action is not None and caption in qb_captions(node):
                return True, action
        return False, None

    def qb_dump(screen_name, tag):
        """Diagnostico: que textos y cuantos nodos con accion ve el arnes."""
        screen = renpy.get_screen(screen_name)
        if screen is None:
            qb_log(False, tag + ": la pantalla no esta mostrada")
        nodes = list(qb_walk(screen.child))
        with_action = [n for n in nodes if getattr(n, "action", None) is not None]
        captions = sorted({c for n in nodes for c in qb_captions(n) if isinstance(c, str) and c.strip()})
        with open(_qb_os.path.join(config.savedir, "save-qa.txt"), "a", encoding="utf-8") as handle:
            handle.write("INFO %s: %d nodos, %d con accion, textos=%r\n"
                         % (tag, len(nodes), len(with_action), captions[:40]))

    def qb_show_details(worker):
        renpy.hide_screen("worker_details")
        renpy.show_screen("worker_details", worker=worker, in_roster=True)

    # ------------------------------------------- forma "0.9.6.2" de un snapshot

    def qb_break_to_0962(snap):
        """Devuelve el snapshot con la forma que publique en 0.9.6.2: la prueba
        del progreso esta presente, pero la puerta que deberia abrir esta en False.
        Con la reconciliacion en su sitio anterior, nada de esto se curaba."""
        snap = _qb_copy.deepcopy(snap)
        buildings = dict(snap.get("available_buildings") or {})
        buildings["Academy"] = qb_building("academy")
        buildings["Arena"] = qb_building("arena")
        snap["available_buildings"] = buildings
        snap["owned_buildings"] = list(snap.get("owned_buildings") or []) + ["Academy", "Arena"]
        snap["academy_enrolled"] = False
        snap["arena_unlocked"] = False
        snap["arena_lanista_paid"] = False
        # La regla clave: la charla del libro de cuentas jugada, la via financiera cerrada.
        snap["yvara_s4_talks_done"] = ["s4_t1", "s4_t2"]
        snap["yvara_s4_finance_unlocked"] = False
        snap["current_objective"] = 9
        for number in range(1, 9):
            snap["objective_%d_complete" % number] = False
        return snap

    def qb_assert_healed(tag):
        qb_log(getattr(store, "yvara_s4_finance_unlocked", False),
               tag + ": Yvara S4 finance reconciliada desde s4_t1",
               getattr(store, "yvara_s4_finance_unlocked", None))
        qb_log(getattr(store, "academy_enrolled", False), tag + ": Academy enrolment curada")
        qb_log(getattr(store, "arena_unlocked", False), tag + ": Arena desbloqueada")
        qb_log(getattr(store, "arena_lanista_paid", False), tag + ": permiso de Lanista curado")
        missing = [n for n in range(1, 9) if not getattr(store, "objective_%d_complete" % n, False)]
        qb_log(not missing, tag + ": objetivos 1-8 curados", missing)

    def qb_write_pair(slot_name, snap):
        for path in (_get_snapshot_file_path(slot_name), _get_backup_file_path(slot_name)):
            with open(path, "w", encoding="utf-8") as handle:
                _qb_json.dump(snap, handle)

    def qb_save(slot):
        set_save_blocked_context(None)
        name = _get_current_slot_name(slot)
        before = _native_save_commit_marker(name)
        SnapshotFileSave(slot)()
        qb_log(_native_save_marker_advanced(before, _native_save_commit_marker(name)),
               "Save nativo commiteado en slot %s" % slot)
        return name

    def qb_load(slot):
        renpy.session["qb_slot"] = slot
        CanonicalSnapshotFileLoad(FileLoad(slot, confirm=False), slot, confirm=False)()
        raise AssertionError("la carga canonica no reinicio el motor (slot %s)" % slot)

    # ------------------------------------------------- casos 7, 9 y 10 (directos)

    def qb_case_7():
        broken = {"name": "QA Broken", "folder": "holly", "gender": "female", "level": 2,
                  "skills": {"Service": 10}, "traits": ["Human"],
                  "skill_uses": {"Service": "muchas", "Combat": None},
                  "assigned_building": "Unassigned", "inventory": []}
        ensure_worker_defaults(broken)
        qb_log(broken["skill_uses"].get("Service") == 0,
               "Caso 7: skill_uses de texto normalizado a 0", broken["skill_uses"].get("Service"))
        qb_log(broken["skill_uses"].get("Combat") == 0,
               "Caso 7: skill_uses nulo normalizado a 0", broken["skill_uses"].get("Combat"))

    def qb_case_9():
        catalog = load_workers(include_unique=True, include_encounter_only=True, for_events=True)
        names = [w.get("name") for w in catalog if hasattr(w, "get")]
        qb_log("QA DictRoot" in names,
               "Caso 9: workers.json con raiz dict aporta su worker", len(names))
        qb_log("Margarita" in names, "Caso 9: el catalogo original sigue completo", len(names))

    def qb_case_10():
        persistent.nsfw_enabled = False
        by_name, by_folder = _build_json_template_index()
        qb_log(by_name is not None, "Caso 10: indice de migracion construido")
        nsfw_only = load_workers(include_unique=True, include_encounter_only=True, for_events=True,
                                 apply_content_filters=False)
        # El indice salta a proposito monster/procedural (no son identidades a
        # migrar) y exige name+folder, asi que no entran en la expectativa.
        restricted = [w.get("name") for w in nsfw_only
                      if hasattr(w, "get") and content_object_is_restricted(w)
                      and w.get("name") and w.get("folder")
                      and not w.get("monster", False) and not w.get("procedural", False)]
        qb_log(bool(restricted), "Caso 10: hay workers restringidos en el catalogo canonico")
        absent = [name for name in restricted if name not in by_name]
        qb_log(not absent,
               "Caso 10: el indice ve los workers NSFW en sesion SFW", absent[:5])
        # Y el filtro de genero tampoco debe vaciar el indice.
        persistent.worker_gender_filter = "male"
        by_name_male, _ = _build_json_template_index()
        persistent.worker_gender_filter = "both"
        qb_log(by_name_male is not None and len(by_name_male) == len(by_name),
               "Caso 10: el filtro de genero no recorta el indice",
               (None if by_name_male is None else len(by_name_male), len(by_name)))

    def qb_case_4_seed():
        """Marca los 5 eventos nuevos como vistos para comprobar que viajan."""
        flags = dict(getattr(store, "event_flags", None) or {})
        for event_id in ("unique_margarita_lore_event", "unique_chestnut_lore_event",
                         "margarita_personal_stage_1", "margarita_personal_stage_2",
                         "margarita_personal_stage_3"):
            flags[event_id + "_seen"] = True
        store.event_flags = flags
        occurrences = dict(getattr(store, "event_occurrences", None) or {})
        for event_id in ("unique_margarita_lore_event", "unique_chestnut_lore_event"):
            occurrences[event_id] = 1
        store.event_occurrences = occurrences

    def qb_case_4_check(tag):
        flags = getattr(store, "event_flags", None) or {}
        missing = [key for key in ("unique_margarita_lore_event_seen",
                                   "unique_chestnut_lore_event_seen",
                                   "margarita_personal_stage_1_seen",
                                   "margarita_personal_stage_2_seen",
                                   "margarita_personal_stage_3_seen")
                   if not flags.get(key)]
        qb_log(not missing, tag + ": flags de los 5 eventos nuevos sobreviven", missing)
        occurrences = getattr(store, "event_occurrences", None) or {}
        qb_log(occurrences.get("unique_margarita_lore_event") == 1,
               tag + ": occurrence de Margarita sobrevive", occurrences.get("unique_margarita_lore_event"))
        qb_log(occurrences.get("unique_chestnut_lore_event") == 1,
               tag + ": occurrence de Chestnut sobrevive", occurrences.get("unique_chestnut_lore_event"))
        qb_log(flags.get("qa_b_marker") == 7, tag + ": flag previa intacta", flags.get("qa_b_marker"))


screen qb_gate():
    zorder 1000
    timer 0.3 action Return()


label splashscreen:
    if _qb_phase() == "2":
        jump qb_phase_two
    $ qb_setup()
    $ qb_log(True, "--- Fase 1 (proceso A) ---")

    # Casos que no necesitan ciclo de guardado.
    $ qb_case_7()
    $ qb_case_9()
    $ qb_case_10()

    # Caso 6: roster entero oculto por el filtro de genero. El fallo era en la
    # CONSTRUCCION de la pantalla: If() es una funcion y sus argumentos (el
    # modulo % len(_nav_names)) se evaluaban aunque la lista estuviese vacia.
    $ persistent.worker_gender_filter = "male"
    $ qb_show_details(store.workers[0])
    call screen qb_gate
    $ qb_log(renpy.get_screen("worker_details") is not None,
             "Caso 6: worker_details construye con el roster vaciado por el filtro")
    $ _qb_found, _qb_action = qb_button("worker_details", "Next")
    $ qb_log(_qb_action is None, "Caso 6: con lista vacia el boton Next queda inerte")
    $ renpy.hide_screen("worker_details")
    $ persistent.worker_gender_filter = "both"
    $ qb_show_details(store.workers[0])
    call screen qb_gate
    $ qb_dump("worker_details", "caso6-sin-filtro")
    $ _qb_found, _qb_action = qb_button("worker_details", "Next")
    $ qb_log(_qb_found and _qb_action is not None, "Caso 6: sin filtro el boton Next existe")
    $ renpy.run(_qb_action)
    call screen qb_gate
    $ qb_log(renpy.get_screen("worker_details") is not None, "Caso 6: Next navega sin crash")
    $ renpy.hide_screen("worker_details")

    # Caso 2: la reconciliacion dentro de _apply_snapshot, con las listas de arco
    # ya aplicadas. Es el bug de orden que publique en 0.9.6.2.
    $ qb_case_4_seed()
    python:
        _qb_base = _build_snapshot()
        _qb_broken = qb_break_to_0962(_qb_base)
        qb_log(_apply_snapshot(_qb_broken), "Caso 2: _apply_snapshot acepta la forma 0.9.6.2")
    $ qb_assert_healed("Caso 2")
    $ qb_case_4_check("Caso 2")

    # Caso 3: la misma forma, pero por una carga canonica REAL, para que corra la
    # pasada de reparacion tardia de after_load (la que reescribe los campos
    # curados desde el snapshot y vuelve a reconciliar).
    python:
        qb_setup()
        qb_case_4_seed()
        _qb_name = qb_save(91)
        _qb_disk = _read_snapshot_file(_get_snapshot_file_path(_qb_name))
        _qb_broken = qb_break_to_0962(_qb_disk)
        qb_log(_snapshot_is_complete_for_canonical_load(_qb_broken),
               "Caso 3: la forma 0.9.6.2 sigue siendo cargable")
        qb_write_pair(_qb_name, _qb_broken)
        qb_step("caso3")
        qb_load(91)


label qb_phase_two:
    $ qb_log(True, "--- Fase 2 (proceso B, motor nuevo) ---")
    $ store.main_menu = False
    $ store.at_main_menu = False
    python:
        qb_log(snapshot_slot_has_any_data(1), "Caso 1: el slot 1 de la fase 1 existe en disco")
        qb_log(_prepare_canonical_snapshot_load(1), "Caso 1: el par snapshot/nativo verifica")
        persistent._canonical_snapshot_load_pending = None
        qb_step("caso1")
        qb_load(1)


label qa_save_loaded:
    $ _qb_at = qb_step()

    if _qb_at == "caso3":
        $ qb_log(True, "Caso 3: carga canonica completada")
        $ qb_assert_healed("Caso 3")
        $ qb_case_4_check("Caso 3")
        # Caso 5: sobrescribir un slot que ya tenia datos y volver a cargarlo.
        python:
            store.money = 31337
            store.current_day = 19
            qb_save(91)
            qb_step("caso5")
            qb_load(91)

    elif _qb_at == "caso5":
        $ qb_log(store.money == 31337, "Caso 5: el slot sobrescrito carga el valor nuevo", store.money)
        $ qb_log(store.current_day == 19, "Caso 5: el dia sobrescrito carga", store.current_day)
        $ qb_case_4_check("Caso 5")
        # Deja el slot 1 listo para el proceso B.
        python:
            store.money = 44444
            store.current_day = 23
            store.current_month = 4
            store.event_flags = dict(getattr(store, "event_flags", None) or {}, qa_b_crossprocess=True)
            qb_save(1)
            qb_log(True, "Fase 1 completada; slot 1 preparado para la fase 2")
            renpy.quit(status=0)

    elif _qb_at == "caso1":
        $ qb_log(store.money == 44444, "Caso 1: dinero tras cerrar y relanzar", store.money)
        $ qb_log(store.current_day == 23, "Caso 1: dia tras cerrar y relanzar", store.current_day)
        $ qb_log(store.current_month == 4, "Caso 1: mes tras cerrar y relanzar", store.current_month)
        $ qb_log((getattr(store, "event_flags", None) or {}).get("qa_b_crossprocess") is True,
                 "Caso 1: flag escrita por el proceso A sobrevive al relanzado")
        $ qb_log(len(store.workers) == 3, "Caso 1: roster completo tras relanzar", len(store.workers))
        $ qb_log(sorted([w.get("name") for w in store.workers]) ==
                 ["QA Chestnut", "QA Holly", "QA Margarita"], "Caso 1: nombres del roster intactos")
        $ qb_case_4_check("Caso 1")
        $ qb_assert_healed("Caso 1")
        $ qb_log(True, "Fase 2 completada")
        $ renpy.quit(status=0)

    else:
        $ qb_log(False, "estado de QA desconocido tras la carga", _qb_at)
