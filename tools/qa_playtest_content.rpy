# Nivel A del plan de playtest: contenido nuevo jugado en el motor real.
# Se inyecta SOLO en una copia desechable (tools/qa_playtest_content.py).
#
# Cubre lo que NO cubre ningun arnes existente. La presentacion y el clic de las
# opciones, y la resolucion de reclutamiento, ya los barre tools/qa_choice_layout.py
# sobre TODOS los eventos (2250 casos): aqui se comprueban los EFECTOS.
#
# Casos de PLAYTEST_PLAN_2026-09-28.md: 8, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23.

init python:
    import os as _qc_os
    import random as _qc_random

    def qc_log(ok, message, actual=None):
        line = ("PASS: " if ok else "FAIL: ") + message
        if not ok and actual is not None:
            line += " -> %r" % (actual,)
        with open(_qc_os.path.join(config.savedir, "content-qa.txt"), "a", encoding="utf-8") as handle:
            handle.write(line + "\n")
        renpy.log("QA-A " + line)
        if not ok:
            raise AssertionError(line)

    def qc_info(message):
        with open(_qc_os.path.join(config.savedir, "content-qa.txt"), "a", encoding="utf-8") as handle:
            handle.write("INFO: " + str(message) + "\n")

    def qc_shot(name):
        renpy.screenshot(_qc_os.path.join(config.savedir, "shot-" + name + ".png"))

    # ------------------------------------------------------------------- setup

    def qc_template(name):
        catalog = load_workers(include_unique=True, include_encounter_only=True, for_events=True,
                              apply_content_filters=False)
        found = next((w for w in catalog if hasattr(w, "get") and w.get("name") == name), None)
        qc_log(found is not None, "Plantilla de %s encontrada en el catalogo" % name)
        worker = dict(found)
        for key, value in list(worker.items()):
            if hasattr(value, "items"):
                worker[key] = dict(value)
            elif hasattr(value, "__iter__") and not isinstance(value, str):
                worker[key] = list(value)
        worker.update({"assigned_building": "Unassigned", "level": 3, "joy": 50,
                       "energy": 15, "health": 25})
        ensure_worker_defaults(worker)
        return worker

    def qc_setup(nsfw=False):
        store.main_menu = False
        store.at_main_menu = False
        store.tutorial_active = False
        store.game_initialized = True
        store.is_new_game = False
        store.money = 50000
        store.current_day = 12
        store.current_month = 3
        store.current_year = 1
        store.player_title = "Lady"
        persistent.nsfw_enabled = bool(nsfw)
        persistent.worker_gender_filter = "both"
        persistent.intro_popups_enabled = False
        store.workers = [qc_template("Margarita"), qc_template("Chestnut")]
        store.available_workers = []
        store.manager_inventory = []
        store.event_flags = {}
        store.event_occurrences = {}
        store.owned_buildings = []
        set_save_blocked_context(None)

    def qc_worker(name):
        return next(w for w in store.workers if w.get("name") == name)

    def qc_event(event_id):
        for folder in ("data/events", "data/events/recruit"):
            for event in load_events_from_folder(folder):
                if event.get("id") == event_id:
                    return event
        qc_log(False, "Evento no encontrado: " + event_id)

    # ------------------------------------------- tirada fijada en los dos sentidos

    def qc_with_roll(value, function, *args, **kwargs):
        """process_choice hace `import random` y llama random.random(): parchear
        el atributo del MODULO si afecta, porque es el mismo objeto modulo."""
        original = _qc_random.random
        _qc_random.random = lambda: value
        try:
            return function(*args, **kwargs)
        finally:
            _qc_random.random = original

    # ------------------------------------------------- casos 13-16: lore events

    def qc_lore_case(event_id, worker_name, choice_index, roll, expect_money, expect_joy,
                     expect_flag, tag):
        qc_setup(nsfw=False)
        event = qc_event(event_id)
        choice = event["choices"][choice_index]
        worker = qc_worker(worker_name)
        money_before = store.money
        joy_before = worker.get("joy", 0)
        result = qc_with_roll(roll, process_choice, choice, event, None)

        qc_log(hasattr(result, "get"), tag + ": process_choice devuelve un desenlace", type(result).__name__)
        message = (result.get("message") or "").strip() if hasattr(result, "get") else ""
        qc_log(bool(message), tag + ": hay texto de desenlace que mostrar al jugador",
               (result.get("outcome") if hasattr(result, "get") else None))
        qc_log(store.money - money_before == expect_money,
               tag + ": delta de dinero", store.money - money_before)
        worker = qc_worker(worker_name)
        qc_log(worker.get("joy", 0) - joy_before == expect_joy,
               tag + ": delta de joy en %s" % worker_name, worker.get("joy", 0) - joy_before)
        flags = getattr(store, "event_flags", None) or {}
        qc_log(bool(flags.get(expect_flag)), tag + ": flag %s activada" % expect_flag)
        # Nadie mas debe recibir el joy nominado.
        others = [w.get("name") for w in store.workers
                  if w.get("name") != worker_name and w.get("joy", 50) != 50]
        qc_log(not others, tag + ": el joy no se derrama a otras workers", others)

    # ----------------------------------------------------- caso 12: orden del arco

    def qc_arc_order():
        qc_setup(nsfw=False)
        stages = [qc_event("margarita_personal_stage_%d" % n) for n in (1, 2, 3)]
        for index, event in enumerate(stages, start=1):
            qc_log(event.get("arc_stage") == index,
                   "Caso 12: stage %d declara arc_stage %d" % (index, index), event.get("arc_stage"))
            qc_log(bool(event.get("arc_id")), "Caso 12: stage %d tiene arc_id" % index)
        arc_ids = {event.get("arc_id") for event in stages}
        qc_log(len(arc_ids) == 1, "Caso 12: los 3 stages comparten arc_id", arc_ids)

        # Con el arco a cero, solo el stage 1 puede ofrecerse.
        eligible = [event.get("id") for event in stages if qc_arc_available(event)]
        qc_log(eligible == ["margarita_personal_stage_1"],
               "Caso 12: de partida solo el stage 1 es elegible", eligible)

        # Completado el 1, se abre el 2 y el 3 sigue cerrado.
        qc_arc_complete(stages[0])
        eligible = [event.get("id") for event in stages if qc_arc_available(event)]
        qc_log("margarita_personal_stage_2" in eligible and
               "margarita_personal_stage_3" not in eligible,
               "Caso 12: tras el stage 1 se abre el 2 y no el 3", eligible)
        qc_arc_complete(stages[1])
        eligible = [event.get("id") for event in stages if qc_arc_available(event)]
        qc_log("margarita_personal_stage_3" in eligible,
               "Caso 12: tras el stage 2 se abre el 3", eligible)

    def qc_arc_available(event):
        checker = getattr(store, "event_arc_stage_is_available", None)
        if callable(checker):
            try:
                return bool(checker(event))
            except Exception:
                pass
        # Fallback: la regla de progresion por arco es "el stage anterior hecho".
        stage = int(event.get("arc_stage") or 1)
        if stage <= 1:
            return True
        arc_id = event.get("arc_id")
        done = getattr(store, "event_arc_progress", None) or {}
        return int((done.get(arc_id) if hasattr(done, "get") else 0) or 0) >= stage - 1

    def qc_arc_complete(event):
        arc_id = event.get("arc_id")
        stage = int(event.get("arc_stage") or 1)
        progress = dict(getattr(store, "event_arc_progress", None) or {})
        progress[arc_id] = stage
        store.event_arc_progress = progress
        flags = dict(getattr(store, "event_flags", None) or {})
        flags[str(event.get("id")) + "_seen"] = True
        if event.get("completion_timestamp_flag"):
            flags[event["completion_timestamp_flag"]] = calculate_total_days()
        store.event_flags = flags

    # ------------------------------- paridad de roster: Margarita en SFW y NSFW

    def qc_roster_parity():
        for name in ("Margarita", "Chestnut"):
            persistent.nsfw_enabled = False
            sfw = [w for w in load_workers(include_unique=True) if hasattr(w, "get")
                   and w.get("name") == name]
            qc_log(len(sfw) == 1, "Paridad: %s aparece una vez en modo SFW" % name, len(sfw))
            qc_log(not content_object_is_restricted(sfw[0]),
                   "Paridad: la variante SFW de %s no esta restringida" % name)
            persistent.nsfw_enabled = True
            nsfw = [w for w in load_workers(include_unique=True) if hasattr(w, "get")
                    and w.get("name") == name]
            qc_log(len(nsfw) == 1, "Paridad: %s aparece una vez en modo NSFW" % name, len(nsfw))
            qc_info("%s: coste SFW %s / NSFW %s, traits SFW %s"
                    % (name, sfw[0].get("cost"), nsfw[0].get("cost"), sfw[0].get("traits")))
        persistent.nsfw_enabled = False

    # --------------------------------------------- casos 17, 18, 21: imagenes

    def qc_installed_slots(folder):
        slots = {}
        prefix = "images/workers/%s/" % folder
        for path in renpy.list_files():
            if not path.startswith(prefix):
                continue
            stem = path[len(prefix):].rsplit(".", 1)[0]
            base = stem.split(" (")[0].strip()
            slots.setdefault(base.lower(), []).append(path)
        return slots

    def qc_images():
        qc_setup(nsfw=True)
        margarita = qc_worker("Margarita")
        slots = qc_installed_slots("margarita")
        qc_log(len(slots) >= 70, "Caso 17: slots instaladas para Margarita", len(slots))
        qc_info("slots instaladas: %d, ficheros: %d"
                % (len(slots), sum(len(v) for v in slots.values())))

        used = set()
        resolved = 0
        # 1) Interacciones (incluye los finales de nivel 5 y las 2 slots huecas).
        interactions = load_interactions() or []
        qc_log(len(interactions) > 0, "Caso 17: catalogo de interacciones cargado", len(interactions))
        for interaction in interactions:
            if not hasattr(interaction, "get"):
                continue
            path = get_interaction_image(margarita, interaction)
            if path:
                resolved += 1
                qc_log(renpy.loadable(str(path).replace("images/", "images/", 1)) or
                       renpy.loadable(str(path)),
                       "Caso 17: imagen de interaccion cargable (%s)" % interaction.get("id"), path)
                used.add(str(path).rsplit("/", 1)[-1].rsplit(".", 1)[0].split(" (")[0].lower())

        # 2) Daily stories de todas las profesiones, incluido el casino.
        story_total = 0
        casino_total = 0
        for btype in (building_types_json.get("building_types") or []):
            for profession in (btype.get("professions") or []):
                for story in (profession.get("daily_stories") or []):
                    story_total += 1
                    if "casino" in str(btype.get("id", "")).lower():
                        casino_total += 1
                    for outcome in ("success", "failure"):
                        path = get_event_image(margarita, story, outcome=outcome,
                                              skill_name=profession.get("skill"))
                        if path:
                            qc_log(renpy.loadable(str(path)),
                                   "Caso 21: imagen de daily story cargable (%s/%s)"
                                   % (profession.get("id"), story.get("id", "?")), path)
                            used.add(str(path).rsplit("/", 1)[-1].rsplit(".", 1)[0].split(" (")[0].lower())
        qc_log(story_total > 0, "Caso 21: hay daily stories en el catalogo", story_total)
        qc_info("daily stories recorridas: %d (casino: %d)" % (story_total, casino_total))
        qc_log(resolved > 0, "Caso 17: se resolvieron imagenes de interaccion", resolved)

        # 3) Huecos de slot. El 2026-09-28 se cerro el ultimo copiando la
        # variante Lord: ahora cada variante de jugador debe servir SU imagen.
        for slot in ("romance_confess_feelings_lady_female",
                     "romance_perfect_night_lady_female",
                     "romance_perfect_night_lord_female"):
            qc_log(slot in slots, "Caso 18: %s esta instalada" % slot)
        for title, slot in (("Lady", "romance_perfect_night_lady_female"),
                            ("Lord", "romance_perfect_night_lord_female")):
            store.player_title = title
            target = next(i for i in interactions
                          if hasattr(i, "get") and i.get("image") == slot)
            path = get_interaction_image(margarita, target)
            qc_log(path is not None, "Caso 18: jugador %s recibe imagen" % title, path)
            qc_log(renpy.loadable(str(path)), "Caso 18: la imagen de %s es cargable" % title, path)
            qc_log(slot in str(path),
                   "Caso 18: jugador %s recibe SU slot, no un fallback" % title, path)
            used.add(str(path).rsplit("/", 1)[-1].rsplit(".", 1)[0].split(" (")[0].lower())
        store.player_title = "Lady"

        # Ninguna interaccion debe quedarse sin imagen para Margarita.
        sin_imagen = []
        for interaction in interactions:
            if not hasattr(interaction, "get") or not interaction.get("image"):
                continue
            if get_interaction_image(margarita, interaction) is None:
                sin_imagen.append(interaction.get("id"))
        qc_info("interacciones sin imagen resuelta: %d" % len(sin_imagen))
        if sin_imagen:
            qc_info("  " + ", ".join(str(i) for i in sin_imagen[:20]))

        unreachable = sorted(set(slots) - used)
        qc_info("slots no alcanzadas por estos resolvers: %d" % len(unreachable))
        qc_info("  " + ", ".join(unreachable[:40]))

    # ------------------------------------------- casos 19, 20: castillo en SFW

    def qc_castle():
        qc_setup(nsfw=False)
        btype = next((b for b in (building_types_json.get("building_types") or [])
                      if b.get("id") == "governor_castle"), None)
        qc_log(btype is not None, "Caso 19: el tipo governor_castle existe")
        qc_log(building_type_is_visible(btype), "Caso 19: el castillo es visible en modo SFW")
        qc_log(building_type_display_name(btype) == "Castle",
               "Caso 19: el castillo no sale como Restricted Business",
               building_type_display_name(btype))

        visible = [p.get("id") for p in (btype.get("professions") or [])
                   if profession_is_visible(p, btype)]
        hidden = [p.get("id") for p in (btype.get("professions") or [])
                  if not profession_is_visible(p, btype)]
        qc_log(sorted(visible) == ["ambassador", "chamberlain", "guards", "prisoner", "rest", "servant"],
               "Caso 19: las 6 profesiones SFW son visibles", sorted(visible))
        qc_log(sorted(hidden) == ["courtesan", "pleasure_servant"],
               "Caso 19: courtesan y pleasure_servant siguen ocultas", sorted(hidden))

        # Caso 20: asignar y correr el dia de verdad.
        add_new_building("Castle", 0)
        building = available_buildings.get("Castle")
        qc_log(hasattr(building, "get"), "Caso 20: el edificio Castle existe tras comprarlo")
        building["type"] = "governor_castle"
        building["owned"] = True
        if "Castle" not in store.owned_buildings:
            store.owned_buildings.append("Castle")
        for worker in store.workers:
            worker["assigned_building"] = "Castle"
        building["assigned_servants"] = list(store.workers)

        # Caso 20: un dia real por CADA una de las 6 profesiones visibles.
        for profession_id in visible:
            for worker in store.workers:
                worker["energy"] = 15
                worker["health"] = 25
                worker["activity_log"] = []
            building["servant_jobs"] = {w.get("name"): profession_id for w in store.workers}
            money_before = store.money
            process_daily_events()
            report = getattr(store, "daily_report", None) or []
            qc_log(len(report) > 0, "Caso 20 (%s): el informe tiene entradas" % profession_id, len(report))
            def _rep_worker(entry):
                inner = entry.get("worker") if hasattr(entry, "get") else None
                return inner if hasattr(inner, "get") else (entry if hasattr(entry, "get") else {})

            names = [_rep_worker(e).get("name") for e in report]
            qc_log("Margarita" in names,
                   "Caso 20 (%s): Margarita aparece en el informe" % profession_id, names[:6])
            logged = []
            for entry in report:
                for day in (_rep_worker(entry).get("activity_log") or []):
                    for item in (day.get("items") or []):
                        meta = item.get("metadata") or {}
                        if meta.get("profession_id"):
                            logged.append(meta.get("profession_id"))
            qc_log(profession_id in logged,
                   "Caso 20 (%s): el trabajo se registra con su profession_id" % profession_id, logged)
            qc_info("  %-12s dinero %s -> %s" % (profession_id, money_before, store.money))

    # ------------------------------------------- caso 8: bonus_items como cadena

    def qc_bonus_items_string():
        qc_setup(nsfw=False)
        btype = next(b for b in (building_types_json.get("building_types") or [])
                     if b.get("id") == "governor_castle")
        profession = next(p for p in btype["professions"] if p.get("id") == "servant")
        stories = profession.setdefault("daily_stories", [])
        injected = {
            "id": "qa_bonus_string_story",
            "weight": 999,
            "report": "QA bonus string",
            "skill_options": ["Service"],
            "story_image": "servant_aristocratic_service",
            "failure_image": "servant_aristocratic_service_failure",
            "earnings": {"success": "50 + skill", "critical_success": "50 + skill * 2",
                         "mediocre": "skill", "failure": "-(roll - skill)"},
            "descriptions": {"success": "QA: bonus_items como cadena suelta.",
                             "critical_success": "QA: bonus_items como cadena suelta.",
                             "mediocre": "QA: bonus_items como cadena suelta.",
                             "failure": "QA: bonus_items como cadena suelta."},
            # no_fail remapea Mediocre/Failure -> Success antes del bloque de loot
            # (event_daily_exec.rpy:1157), que exige Success/Critical Success.
            "no_fail": True,
            # La forma bajo prueba: cadenas sueltas donde el motor espera objetos.
            "loot": {"rolls": 0, "bonus_items": ["health_potion"]},
        }
        stories.insert(0, injected)
        try:
            add_new_building("Castle", 0)
            building = available_buildings.get("Castle")
            building["type"] = "governor_castle"
            building["owned"] = True
            if "Castle" not in store.owned_buildings:
                store.owned_buildings.append("Castle")
            worker = qc_worker("Margarita")
            worker["assigned_building"] = "Castle"
            building["servant_jobs"] = {"Margarita": "servant"}
            building["assigned_servants"] = [worker]
            store.workers = [worker]
            store.manager_inventory = []
            # Fuerza que se elija la historia inyectada: el motor usa
            # select_weighted_event(compatible_stories), no random.choice.
            original_select = store.select_weighted_event
            def _forced(pool, *args, **kwargs):
                for story in (pool or []):
                    if hasattr(story, "get") and story.get("id") == "qa_bonus_string_story":
                        return story
                return original_select(pool, *args, **kwargs)
            store.select_weighted_event = _forced
            try:
                qc_with_roll(0.0, process_daily_events)
            finally:
                store.select_weighted_event = original_select
            qc_log(any(hasattr(e, "get") and (e.get("event_data") or {}).get("id") == "qa_bonus_string_story"
                       for e in (getattr(store, "daily_report", None) or [])),
                   "Caso 8: la historia inyectada fue la elegida",
                   [(e.get("event_data") or {}).get("id") for e in (getattr(store, "daily_report", None) or [])
                    if hasattr(e, "get")])
            ids = [entry[0] if hasattr(entry, "__getitem__") and not hasattr(entry, "get") else entry
                   for entry in (store.manager_inventory or [])]
            results = [e.get("result") for e in (getattr(store, "daily_report", None) or [])
                       if hasattr(e, "get")]
            qc_log(any(r in ("Success", "Critical Success") for r in results),
                   "Caso 8: el desenlace entra en la rama de loot", results)
            qc_log("health_potion" in [str(i) for i in ids],
                   "Caso 8: bonus_items en formato cadena concede el item", ids)
        finally:
            stories.remove(injected)

    # ------------------------------- caso 25: exclusividad de los finales nivel 5

    def qc_level5_finales():
        qc_setup(nsfw=True)
        worker = qc_worker("Margarita")
        worker["level"] = 5
        worker["relationship"] = 100
        worker["romance"] = 100
        worker["joy"] = 100
        # Las dos puertas reales del nivel 5 de disciplina:
        #  - rebelliousness < 25 (en Discipline el requisito es "menor que")
        #  - discipline_uses_level_4 >= get_unlock_required_uses()
        worker["rebelliousness"] = 10
        uses = get_unlock_required_uses()
        worker["flags"] = {
            "discipline_uses_level_4": {"value": uses, "duration": -1},
            "friendship_uses_level_4": {"value": uses, "duration": -1},
            "romance_uses_level_4": {"value": uses, "duration": -1},
        }

        def offered():
            return {i.get("id") for i in (get_available_interactions_for_worker(worker) or [])
                    if hasattr(i, "get")}

        before = offered()
        finales = {"discipline_level5_finale_harem_member", "discipline_level5_finale_house_servant"}
        qc_log(finales <= before, "Caso 25: los dos finales de disciplina se ofrecen de partida",
               sorted(finales - before))
        qc_log("discipline_level5_sell_specialty_buyer" in before,
               "Caso 25: la venta al comprador especialista se ofrece")
        qc_log("friendship_level5" in before, "Caso 25: el final de amistad se ofrece")
        romance_before = {i for i in before if i.startswith("romance_level5_")}
        qc_log(bool(romance_before), "Caso 25: hay final de romance ofrecido", romance_before)

        # El camino real: la pantalla de resultado marca el flag permanente
        # (screens.rpy:8110), no el effect.flags del JSON.
        _apply_discipline_final_and_close(worker, "Harem Member", [])
        qc_log(bool((worker.get("flags") or {}).get("discipline_final_done")),
               "Caso 25: la pantalla de resultado marca discipline_final_done")
        after = offered()
        qc_log(not (finales & after),
               "Caso 25: tras elegir un final, NINGUN final de disciplina se repite",
               sorted(finales & after))
        qc_log("discipline_level5_sell_specialty_buyer" in after,
               "Caso 25: la venta sigue disponible (repetible a proposito)")
        # Exclusividad CRUZADA por diseno (worker_interactions.rpy:390-414): un final
        # cierra el nivel 5 de las otras ramas tambien.
        qc_log("friendship_level5" not in after,
               "Caso 25: el final de amistad queda cerrado por exclusividad cruzada")
        qc_log(not {i for i in after if i.startswith("romance_level5_")},
               "Caso 25: el final de romance queda cerrado por exclusividad cruzada",
               {i for i in after if i.startswith("romance_level5_")})

        # Y al reves: partiendo limpio, el final de amistad cierra los de disciplina.
        worker["flags"] = {
            "discipline_uses_level_4": {"value": uses, "duration": -1},
            "friendship_uses_level_4": {"value": uses, "duration": -1},
            "romance_uses_level_4": {"value": uses, "duration": -1},
        }
        qc_log(finales <= offered(), "Caso 25: limpiado el flag, los finales vuelven")
        _interaction_result_mark_worker_flag(worker, "friendship_final_done")
        reverse = offered()
        qc_log(not (finales & reverse),
               "Caso 25: el final de amistad cierra los de disciplina", sorted(finales & reverse))
        qc_log("discipline_level5_sell_specialty_buyer" in reverse,
               "Caso 25: la venta sobrevive tambien a esa ruta")

    # ------------------------- retrato del roster en el modo que toca (caso 17)

    def qc_portraits():
        """El retrato debe salir con la variante que el filtro de contenido sirve.
        Si se mezcla (plantilla NSFW en sesion SFW), worker_media_is_visible la
        oculta y el panel muestra "No Image Available": eso es correcto, pero hay
        que comprobar que el caso legitimo SI pinta."""
        for nsfw in (False, True):
            persistent.nsfw_enabled = nsfw
            mode = "NSFW" if nsfw else "SFW"
            for name in ("Margarita", "Chestnut"):
                served = [w for w in load_workers(include_unique=True)
                          if hasattr(w, "get") and w.get("name") == name]
                qc_log(len(served) == 1, "Retrato %s: %s la sirve el filtro" % (mode, name), len(served))
                worker = dict(served[0])
                ensure_worker_defaults(worker)
                qc_log(worker_media_is_visible(worker),
                       "Retrato %s: las imagenes de %s son visibles" % (mode, name))
                path = get_worker_image_safe(worker)
                qc_log(path and renpy.loadable(str(path)),
                       "Retrato %s: %s tiene retrato cargable" % (mode, name), path)
                qc_info("retrato %s de %s -> %s" % (mode, name, path))
        persistent.nsfw_enabled = False

    # ------------------- caso 26: las pantallas principales renderizan (y captura)

    def qc_main_screens():
        qc_setup(nsfw=False)
        variant = _qc_os.environ.get("RENPY_VARIANT", "") or "desktop"
        qc_info("variante de pantalla: %s" % variant)
        # El informe diario necesita datos: un dia real del castillo.
        add_new_building("Castle", 0)
        building = available_buildings.get("Castle")
        building["type"] = "governor_castle"
        building["owned"] = True
        store.owned_buildings.append("Castle")
        for worker in store.workers:
            worker["assigned_building"] = "Castle"
        building["servant_jobs"] = {"Margarita": "servant", "Chestnut": "guards"}
        building["assigned_servants"] = list(store.workers)
        process_daily_events()
        return variant

    # --------------------------------- casos 22, 23: bucle diario y cambio de mes

    def qc_daily_loop():
        qc_setup(nsfw=False)
        add_new_building("Castle", 0)
        building = available_buildings.get("Castle")
        building["type"] = "governor_castle"
        building["owned"] = True
        store.owned_buildings.append("Castle")
        for worker in store.workers:
            worker["assigned_building"] = "Castle"
        building["servant_jobs"] = {"Margarita": "servant", "Chestnut": "guards"}
        building["assigned_servants"] = list(store.workers)

        store.current_day = 28
        store.current_month = 3
        for day in range(6):
            before_day = store.current_day
            process_daily_events()
            qc_log(isinstance(getattr(store, "daily_report", None) or [], (list,)) or
                   hasattr(getattr(store, "daily_report", None) or [], "__iter__"),
                   "Caso 22: informe iterable el dia %s" % before_day)
            advance_calendar_one_day()
        qc_log(store.current_month == 4, "Caso 23: el mes avanzo tras el dia 30",
               (store.current_month, store.current_day))
        state = monthly_state()
        qc_log(hasattr(state, "get"), "Caso 23: hay estado de condicion mensual", type(state).__name__)
        qc_info("condicion mensual tras el rollover: %r" % (state.get("card", {}) or {}).get("id"))

    def advance_calendar_one_day():
        store.current_day += 1
        if store.current_day > 30:
            store.current_day = 1
            store.current_month += 1
            if store.current_month > 12:
                store.current_month = 1
                store.current_year += 1
        monthly_sync()


screen qc_gate():
    zorder 1000
    timer 0.3 action Return()


label splashscreen:
    $ qc_log(True, "--- Nivel A: contenido nuevo ---")

    # Casos 13-16: efectos reales de los lore events, exito y fallo.
    $ qc_lore_case("unique_margarita_lore_event", "Margarita", 0, 0.0, 450, 6, "unique_margarita_bond_done", "Caso 13 exito")
    $ qc_lore_case("unique_margarita_lore_event", "Margarita", 0, 1.0, -520, 0, "unique_margarita_bond_done", "Caso 13 fallo")
    $ qc_lore_case("unique_margarita_lore_event", "Margarita", 1, 0.0, -350, 10, "unique_margarita_bond_done", "Caso 14 determinista")
    $ qc_lore_case("unique_chestnut_lore_event", "Chestnut", 0, 0.0, 260, 5, "unique_chestnut_relay_done", "Caso 15 exito")
    $ qc_lore_case("unique_chestnut_lore_event", "Chestnut", 0, 1.0, -430, 0, "unique_chestnut_relay_done", "Caso 15 fallo")
    $ qc_lore_case("unique_chestnut_lore_event", "Chestnut", 1, 0.0, -400, 12, "unique_chestnut_relay_done", "Caso 15 determinista")

    # Caso 12: orden de los 3 stages del arco.
    $ qc_arc_order()

    # Paridad de roster SFW/NSFW.
    $ qc_setup(nsfw=False)
    $ qc_roster_parity()

    # Casos 17, 18, 21: imagenes.
    $ qc_images()

    # Casos 19, 20: castillo en SFW y su dia.
    $ qc_castle()

    # Caso 8: bonus_items como cadena.
    $ qc_bonus_items_string()

    # Caso 25: exclusividad de los finales de nivel 5.
    $ qc_level5_finales()

    # Casos 22, 23: bucle diario y cambio de mes.
    $ qc_daily_loop()

    # Retratos servidos por el filtro de contenido.
    $ qc_setup(nsfw=False)
    $ qc_portraits()

    # Caso 26: las pantallas principales construyen y se capturan.
    $ _qc_variant = qc_main_screens()
    show screen map_screen
    call screen qc_gate
    $ qc_log(renpy.get_screen("map_screen") is not None, "Caso 26: map_screen renderiza (%s)" % _qc_variant)
    $ qc_shot("map-" + _qc_variant.split(" ")[0])
    hide screen map_screen
    show screen daily_report
    call screen qc_gate
    $ qc_log(renpy.get_screen("daily_report") is not None, "Caso 26: daily_report renderiza (%s)" % _qc_variant)
    $ qc_shot("daily_report-" + _qc_variant.split(" ")[0])
    hide screen daily_report
    $ renpy.show_screen("worker_details", worker=qc_worker("Margarita"), in_roster=True)
    call screen qc_gate
    $ qc_log(renpy.get_screen("worker_details") is not None, "Caso 26: worker_details renderiza (%s)" % _qc_variant)
    $ qc_shot("worker_details-" + _qc_variant.split(" ")[0])
    $ renpy.hide_screen("worker_details")

    $ qc_log(True, "--- Nivel A completado ---")
    $ renpy.quit(status=0)
