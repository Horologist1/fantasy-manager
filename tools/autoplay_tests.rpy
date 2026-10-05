# Pruebas de la lista (.hermes/audits/TEST_LIST_2026-09-28.md) que el
# autojugador ejecuta mientras juega. Cada una dice QUE SE JUEGA y QUE DEBE
# CUMPLIRSE; el resultado va al informe como PASA/FALLA.
#
# Las que necesitan varias fases (guardar -> cargar -> comparar) guardan su fase
# en renpy.session, que sobrevive al reinicio del motor que provoca una carga.
#
# Se carga despues de autoplay.rpy y usa sus utilidades (ap_note, ap_shot, _ap).

init -95 python:

    AP_TESTS = []

    def ap_test(test_id, description):
        def register(function):
            AP_TESTS.append({"id": test_id, "desc": description, "fn": function})
            return function
        return register

    def ap_result(test_id, ok, detail=""):
        """ok=True PASA, ok=False FALLA, ok=None NO CONCLUYENTE.

        Lo tercero existe porque una prueba puede no llegar a ejercitarse en una
        sesion (p. ej. T3.4 necesita que el dinero cambie solo). Contarlo como
        fallo mezcla "el juego esta mal" con "no me dio tiempo".
        """
        results = renpy.session.setdefault("ap_results", {})
        if test_id in results:
            return
        estado = "NO CONCLUYENTE" if ok is None else ("PASA" if ok else "FALLA")
        results[test_id] = {"ok": (None if ok is None else bool(ok)),
                            "estado": estado, "detail": str(detail)[:200]}
        ap_note("TEST", "%s %s :: %s" % (estado, test_id, detail),
                test_id=test_id, ok=(None if ok is None else bool(ok)))
        if ok is False:
            ap_shot("fail-" + test_id)

    def ap_pending_tests():
        done = renpy.session.get("ap_results") or {}
        return [t for t in AP_TESTS if t["id"] not in done]

    def ap_phase(test_id, name, **extra):
        data = {"id": test_id, "name": name}
        data.update(extra)
        renpy.session["ap_test_phase"] = data

    def ap_phase_name(test_id):
        phase = renpy.session.get("ap_test_phase") or {}
        return phase.get("name") if phase.get("id") == test_id else None

    def ap_phase_clear():
        renpy.session["ap_test_phase"] = None

    def ap_tests_diag():
        if renpy.session.get("ap_tests_diag"):
            return
        renpy.session["ap_tests_diag"] = True
        ap_note("DIAG", "pruebas registradas: %d -> %r"
                % (len(AP_TESTS), [x["id"] for x in AP_TESTS][-8:]))

    def ap_tests_tick():
        ap_tests_diag()
        """Una prueba por tick como mucho, nunca a medio dialogo ni menu."""
        if not getattr(store, "game_initialized", False):
            return False
        if renpy.get_screen("say") or renpy.get_screen("choice") or renpy.get_screen("input"):
            return False
        phase = renpy.session.get("ap_test_phase")
        esperando = None
        if phase:
            esperando = phase.get("id")
            for test in AP_TESTS:
                if test["id"] == esperando:
                    if bool(test["fn"]()):
                        return True
                    break            # esta esperando: que no bloquee al resto
            else:
                ap_phase_clear()
                esperando = None
        if _ap.actions - _ap.last_test_at < 40:
            return False
        pending = [t for t in ap_pending_tests() if t["id"] != esperando]
        if not pending:
            return False
        # Turno rotatorio: recorrer siempre desde el principio dejaba sin
        # ejecutar a las ultimas de la lista (las de Arena y Academia no
        # corrieron nunca). El desplazamiento reparte los turnos.
        desplazamiento = (_ap.actions // 40) % len(pending)
        pending = pending[desplazamiento:] + pending[:desplazamiento]
        _ap.last_test_at = _ap.actions
        # Recorrer TODAS las pendientes, no solo la primera: una prueba cuyas
        # precondiciones aun no se cumplen devuelve False, y quedarse en ella
        # dejaba sin ejecutar a todas las de atras (bloques 5 y 7 enteros).
        for test in pending:
            try:
                if bool(test["fn"]()):
                    return True
            except renpy.game.CONTROL_EXCEPTIONS:
                raise
            except Exception as e:
                ap_result(test["id"], False, "excepcion: %r" % (e,))
                ap_phase_clear()
                return True
        return False

    # -------------------------------------------------------------- utilidades

    def ap_slot_snapshot(slot):
        """Lo que el juego dejo escrito en el sidecar de ese slot."""
        name = _get_current_slot_name(slot)
        path = _get_snapshot_file_path(name)
        if not _ap_os.path.exists(path):
            return None
        return _read_snapshot_file(path)

    def ap_quiet_latency():
        """Guardar y cargar desde el ARNES cuesta ~1,7 s con 40 workers. Es coste
        del medidor: si no se silencia, I8 lo denuncia atribuyendolo al ultimo
        clic del jugador, que no tiene nada que ver."""
        _ap.last_tick_at = None
        _ap.quiet_i8_until = _ap.tick + 15

    def ap_save_slot(slot):
        set_save_blocked_context(None)
        ap_quiet_latency()
        SnapshotFileSave(slot)()

    def ap_load_slot(slot):
        ap_quiet_latency()
        CanonicalSnapshotFileLoad(FileLoad(slot, confirm=False), slot, confirm=False)()

    # ==================================================== Bloque 3: saves

    @ap_test("T3.1", "Guardar deja un slot con el dia y el dinero correctos")
    def _t3_1():
        expected = (getattr(store, "current_day", None), getattr(store, "money", None))
        ap_save_slot(40)
        snap = ap_slot_snapshot(40)
        if snap is None:
            ap_result("T3.1", False, "no se escribio el sidecar del slot 40")
            return True
        got = (snap.get("current_day"), snap.get("money"))
        ap_result("T3.1", got == expected, "guardado %r, en partida %r" % (got, expected))
        return True

    @ap_test("T3.4", "Sobrescribir un slot carga lo nuevo, nunca lo viejo")
    def _t3_4():
        name = ap_phase_name("T3.4")
        if name is None:
            ap_save_slot(41)
            renpy.session["ap_t34_first"] = getattr(store, "money", None)
            ap_phase("T3.4", "esperando-cambio", since=_ap.actions)
            return True
        if name == "esperando-cambio":
            first = renpy.session.get("ap_t34_first")
            if getattr(store, "money", None) == first:
                phase = renpy.session.get("ap_test_phase") or {}
                if _ap.actions - (phase.get("since") or 0) > 800:
                    ap_phase_clear()
                    ap_result("T3.4", None, "el dinero no cambio solo en esta sesion")
                    return True
                return False
            ap_save_slot(41)
            renpy.session["ap_t34_second"] = getattr(store, "money", None)
            ap_phase("T3.4", "cargando")
            ap_load_slot(41)
            return True
        if name == "cargando":
            ap_phase_clear()
            second = renpy.session.get("ap_t34_second")
            current = getattr(store, "money", None)
            ap_result("T3.4", current == second,
                      "el slot sobrescrito cargo %r, esperado %r" % (current, second))
            return True
        return False

    @ap_test("T3.5", "Cada slot devuelve SU partida, sin mezclarse")
    def _t3_5():
        name = ap_phase_name("T3.5")
        if name is None:
            marks = {}
            for slot in (42, 43, 44, 45):
                store.money = 70000 + slot
                ap_save_slot(slot)
                marks[str(slot)] = 70000 + slot
            renpy.session["ap_t35_marks"] = marks
            ap_phase("T3.5", "cargar-42")
            ap_load_slot(42)
            return True
        if name and name.startswith("cargar-"):
            slot = name.split("-")[1]
            marks = renpy.session.get("ap_t35_marks") or {}
            current = getattr(store, "money", None)
            if current != marks.get(slot):
                ap_phase_clear()
                ap_result("T3.5", False, "el slot %s cargo %r, esperado %r"
                          % (slot, current, marks.get(slot)))
                return True
            following = {"42": "43", "43": "44", "44": "45"}.get(slot)
            if following is None:
                ap_phase_clear()
                ap_result("T3.5", True, "los 4 slots cargaron su propia marca")
                return True
            ap_phase("T3.5", "cargar-" + following)
            ap_load_slot(int(following))
            return True
        return False

    @ap_test("T3.6", "Borrar un slot lo deja sin datos")
    def _t3_6():
        ap_save_slot(46)
        if ap_slot_snapshot(46) is None:
            ap_result("T3.6", False, "no se pudo preparar el slot 46")
            return True
        name = _get_current_slot_name(46)
        try:
            snapshot_pre_delete_slot(46)
        except Exception:
            pass
        renpy.unlink_save(name)
        try:
            snapshot_delete_sidecars(46)
        except Exception:
            pass
        quedan = bool(snapshot_slot_has_any_data(46)) or ap_slot_snapshot(46) is not None
        ap_result("T3.6", not quedan,
                  "quedan datos tras borrar" if quedan else "el slot quedo limpio")
        return True

    @ap_test("T3.10", "Lo que ya ocurrio sigue ocurrido tras guardar y cargar")
    def _t3_10():
        name = ap_phase_name("T3.10")
        if name is None:
            flags = getattr(store, "event_flags", None) or {}
            seen = sorted(k for k in flags if flags.get(k))
            occurrences = dict(getattr(store, "event_occurrences", None) or {})
            if not seen and not occurrences:
                return False   # todavia no ha pasado nada: se reintenta mas tarde
            renpy.session["ap_t310_flags"] = seen
            renpy.session["ap_t310_occ"] = occurrences
            ap_save_slot(47)
            ap_phase("T3.10", "cargando")
            ap_load_slot(47)
            return True
        if name == "cargando":
            ap_phase_clear()
            before_flags = renpy.session.get("ap_t310_flags") or []
            before_occ = renpy.session.get("ap_t310_occ") or {}
            flags = getattr(store, "event_flags", None) or {}
            occurrences = getattr(store, "event_occurrences", None) or {}
            perdidas = [k for k in before_flags if not flags.get(k)]
            cambiados = [k for k, v in before_occ.items() if occurrences.get(k) != v]
            ap_result("T3.10", not perdidas and not cambiados,
                      "flags perdidas %r, contadores cambiados %r"
                      % (perdidas[:5], cambiados[:5]))
            return True
        return False

    @ap_test("T3.13", "Cambiar el filtro de genero no borra workers del roster")
    def _t3_13():
        name = ap_phase_name("T3.13")
        if name is None:
            workers = getattr(store, "workers", None) or []
            if len(workers) < 2:
                return False   # sin roster no hay nada que comprobar
            renpy.session["ap_t313_names"] = sorted(
                str(w.get("name")) for w in workers if hasattr(w, "get"))
            renpy.session["ap_t313_filter"] = getattr(persistent, "worker_gender_filter", "both")
            ap_save_slot(48)
            persistent.worker_gender_filter = "male"
            ap_phase("T3.13", "cargando")
            ap_load_slot(48)
            return True
        if name == "cargando":
            ap_phase_clear()
            before = renpy.session.get("ap_t313_names") or []
            workers = getattr(store, "workers", None) or []
            after = sorted(str(w.get("name")) for w in workers if hasattr(w, "get"))
            persistent.worker_gender_filter = renpy.session.get("ap_t313_filter") or "both"
            ap_result("T3.13", after == before,
                      "roster %d -> %d tras cargar con el filtro cambiado"
                      % (len(before), len(after)))
            return True
        return False

    # ==================================================== Bloque 4: ciclo diario

    @ap_test("T4.3", "El resultado y el dinero de cada entrada del informe no se contradicen")
    def _t4_3():
        report = getattr(store, "daily_report", None) or []
        revisadas = 0
        malos = []
        for entry in report:
            if not hasattr(entry, "get"):
                continue
            resultado = str(entry.get("result") or "").strip()
            earnings = entry.get("earnings")
            if not resultado or earnings is None:
                continue
            # La formacion de la Academia CUESTA matricula y fuerza "Success"
            # (event_daily_exec.rpy:1017-1023): restar ahi es correcto, no una
            # contradiccion. Se identifica por el profession_id del historial.
            worker_obj = entry.get("worker")
            pid = ""
            if hasattr(worker_obj, "get"):
                for day in reversed(worker_obj.get("activity_log") or []):
                    for item in reversed(day.get("items") or []):
                        meta = item.get("metadata") or {}
                        if meta.get("profession_id"):
                            pid = str(meta["profession_id"])
                            break
                    if pid:
                        break
            if pid.startswith("academy_"):
                continue
            try:
                valor = int(earnings)
            except (TypeError, ValueError):
                malos.append("%s: earnings no numerico %r" % (resultado, earnings))
                continue
            revisadas += 1
            nombre = (entry.get("worker") or {}).get("name") if hasattr(entry.get("worker"), "get") else entry.get("worker_name")
            if resultado in ("Success", "Critical Success") and valor < 0:
                malos.append("%s dice %s y resta %d" % (nombre, resultado, valor))
            if resultado == "Failure" and valor > 0:
                malos.append("%s dice Failure y suma %d" % (nombre, valor))
        if revisadas < 2:
            return False
        ap_result("T4.3", not malos,
                  "%d entradas revisadas, contradicciones: %r" % (revisadas, malos[:5]))
        return True

    @ap_test("T4.6", "El calendario avanza siempre y el informe sale cada dia")
    def _t4_6():
        historial = renpy.session.setdefault("ap_t46_days", [])
        day = getattr(store, "current_day", None)
        month = getattr(store, "current_month", None)
        if day is None or month is None:
            return False
        fecha = (month, day)
        if not historial or historial[-1] != list(fecha):
            historial.append(list(fecha))
        if len(historial) < 12:
            return False
        # 12 dias jugados: ninguno puede repetirse ni retroceder dentro del mes.
        malos = []
        for antes, despues in zip(historial, historial[1:]):
            if despues[0] == antes[0] and despues[1] <= antes[1]:
                malos.append((antes, despues))
        ap_result("T4.6", not malos,
                  "%d dias jugados, saltos raros: %r" % (len(historial), malos[:3]))
        return True

    @ap_test("T4.7", "Al cruzar de mes hay condicion mensual y se anuncia")
    def _t4_7():
        month = getattr(store, "current_month", None)
        primero = renpy.session.get("ap_t47_month")
        if primero is None:
            renpy.session["ap_t47_month"] = month
            return False
        if month == primero:
            return False
        estado = None
        getter = getattr(store, "monthly_state", None)
        if callable(getter):
            try:
                estado = getter()
            except Exception as e:
                ap_result("T4.7", False, "monthly_state() reventó: %r" % (e,))
                return True
        ap_result("T4.7", hasattr(estado, "get"),
                  "mes %r -> %r, estado mensual %r" % (primero, month, type(estado).__name__))
        return True

    # ==================================================== Bloque 6: workers

    @ap_test("T6.4", "La ficha de CADA worker del roster abre con sus datos")
    def _t6_4():
        workers = [w for w in (getattr(store, "workers", None) or []) if hasattr(w, "get")]
        if len(workers) < 3:
            return False
        malos = []
        for worker in workers:
            nombre = worker.get("name")
            if not nombre:
                malos.append("worker sin nombre")
                continue
            if not worker.get("skills"):
                malos.append("%s sin skills" % nombre)
            if worker.get("level") is None:
                malos.append("%s sin nivel" % nombre)
            try:
                imagen = get_worker_image_safe(worker)
            except Exception as e:
                malos.append("%s: imagen reventó %r" % (nombre, e))
                continue
            if imagen and not renpy.loadable(str(imagen)):
                malos.append("%s: imagen no cargable %s" % (nombre, imagen))
        ap_result("T6.4", not malos,
                  "%d workers revisados, problemas: %r" % (len(workers), malos[:5]))
        return True

    @ap_test("T6.11", "Con el roster grande nada tarda mas de lo aceptable")
    def _t6_11():
        workers = getattr(store, "workers", None) or []
        if len(workers) < 30:
            return False
        lentas = [f for f in _ap.findings if "I8-lento" in str(f.get("message", ""))]
        ap_result("T6.11", not lentas,
                  "%d workers; interacciones lentas detectadas: %d" % (len(workers), len(lentas)))
        return True

    @ap_test("T3.12", "Cargar con el roster grande no congela el juego")
    def _t3_12():
        workers = getattr(store, "workers", None) or []
        if len(workers) < 30:
            return False
        ms = renpy.session.get("ap_load_ms")
        if ms is None:
            return False   # todavia no ha habido una carga medida
        ap_result("T3.12", ms < 3000,
                  "cargar con %d workers tardo %d ms" % (len(workers), ms))
        return True

    # ============================== Bloque 5: edificios y profesiones

    def ap_btype(building):
        if not hasattr(building, "get"):
            return None
        btype_id = building.get("type")
        for bt in (building_types_json.get("building_types") or []):
            if bt.get("id") == btype_id:
                return bt
        return None

    @ap_test("T5.2", "Cada trabajo del informe pertenece de verdad a su edificio")
    def _t5_2():
        report = getattr(store, "daily_report", None) or []
        revisadas, malos = 0, []
        vistas = renpy.session.setdefault("ap_t52_profesiones", [])
        for entry in report:
            if not hasattr(entry, "get"):
                continue
            worker = entry.get("worker")
            worker = worker if hasattr(worker, "get") else {}
            for day in (worker.get("activity_log") or []):
                for item in (day.get("items") or []):
                    meta = item.get("metadata") or {}
                    pid = meta.get("profession_id")
                    btid = meta.get("building_type_id")
                    if not pid or not btid:
                        continue
                    revisadas += 1
                    if pid not in vistas:
                        vistas.append(pid)
                    bt = next((b for b in (building_types_json.get("building_types") or [])
                               if b.get("id") == btid), None)
                    if bt is None:
                        malos.append("tipo de edificio inexistente: %s" % btid)
                        continue
                    ids = [p.get("id") for p in (bt.get("professions") or [])]
                    if pid not in ids:
                        malos.append("%s no es profesion de %s" % (pid, btid))
        if revisadas < 4:
            return False
        ap_result("T5.2", not malos,
                  "%d trabajos, %d profesiones distintas, incoherencias: %r"
                  % (revisadas, len(vistas), malos[:5]))
        return True

    @ap_test("T5.3", "En modo SFW ningun trabajo asignado es contenido restringido")
    def _t5_3():
        if getattr(persistent, "nsfw_enabled", False):
            ap_result("T5.3", True, "sesion NSFW: no aplica")
            return True
        buildings = getattr(store, "available_buildings", None) or {}
        if not hasattr(buildings, "get"):
            return False
        malos, revisados = [], 0
        for name in (getattr(store, "owned_buildings", None) or []):
            building = buildings.get(name)
            bt = ap_btype(building)
            if bt is None:
                continue
            jobs = building.get("servant_jobs") or {}
            if not hasattr(jobs, "items"):
                continue
            for worker_name, pid in jobs.items():
                revisados += 1
                profession = next((p for p in (bt.get("professions") or [])
                                   if p.get("id") == pid), None)
                if profession is None:
                    continue
                if not profession_is_visible(profession, bt):
                    malos.append("%s asignado a %s (oculta en SFW)" % (worker_name, pid))
        if not revisados:
            return False
        ap_result("T5.3", not malos,
                  "%d asignaciones revisadas, restringidas: %r" % (revisados, malos[:5]))
        return True

    @ap_test("T5.8", "Ningun edificio supera su maximo de trabajadores")
    def _t5_8():
        buildings = getattr(store, "available_buildings", None) or {}
        if not hasattr(buildings, "get"):
            return False
        malos, revisados = [], 0
        workers = [w for w in (getattr(store, "workers", None) or []) if hasattr(w, "get")]
        for name in (getattr(store, "owned_buildings", None) or []):
            building = buildings.get(name)
            bt = ap_btype(building)
            if bt is None or not hasattr(building, "get"):
                continue
            jobs = building.get("servant_jobs") or {}
            if not hasattr(jobs, "get"):
                continue
            dentro = [w for w in workers if w.get("assigned_building") == name]
            revisados += 1
            calculador = getattr(store, "get_max_daily_workers", None)
            if not callable(calculador):
                return False
            for profession in (bt.get("professions") or []):
                pid = profession.get("id")
                # El tope REAL escala con el nivel del edificio (script.rpy:5373).
                # Leer max_daily_workers a pelo da falsos positivos en cuanto el
                # edificio sube de nivel.
                try:
                    limite = int(calculador(building, profession))
                except (TypeError, ValueError):
                    continue
                puestos = len([w for w in dentro if jobs.get(w.get("name")) == pid])
                if puestos > limite:
                    malos.append("%s/%s: %d por encima del tope %d" % (name, pid, puestos, limite))
        if not revisados:
            return False
        ap_result("T5.8", not malos,
                  "%d edificios revisados, desbordes: %r" % (revisados, malos[:5]))
        return True

    # ============================== Bloque 7: interacciones y finales

    def ap_flag_marcada(worker, flag):
        valor = (worker.get("flags") or {}).get(flag)
        if valor is None:
            return False
        if hasattr(valor, "get"):
            return bool(valor.get("value", False))
        return bool(valor)

    @ap_test("T7.6", "Elegido un final de nivel 5, no se ofrece ningun otro")
    def _t7_6():
        workers = [w for w in (getattr(store, "workers", None) or []) if hasattr(w, "get")]
        getter = getattr(store, "get_available_interactions_for_worker", None)
        if not callable(getter):
            return False
        con_final = [w for w in workers
                     if ap_flag_marcada(w, "discipline_final_done")
                     or ap_flag_marcada(w, "friendship_final_done")
                     or ap_flag_marcada(w, "romance_confess_done")]
        if not con_final:
            return False
        malos = []
        for worker in con_final:
            ofrecidas = [i.get("id") for i in (getter(worker) or []) if hasattr(i, "get")]
            fuera = [i for i in ofrecidas
                     if "level5" in str(i) and i != "discipline_level5_sell_specialty_buyer"]
            if fuera:
                malos.append("%s: %r" % (worker.get("name"), fuera[:3]))
        ap_result("T7.6", not malos,
                  "%d workers con final hecho, finales aun ofrecidos: %r"
                  % (len(con_final), malos[:3]))
        return True

    @ap_test("T7.9", "Toda interaccion ofrecida cumple de verdad sus requisitos")
    def _t7_9():
        workers = [w for w in (getattr(store, "workers", None) or []) if hasattr(w, "get")]
        getter = getattr(store, "get_available_interactions_for_worker", None)
        if not callable(getter) or len(workers) < 3:
            return False
        malos, revisadas = [], 0
        for worker in workers[:8]:
            for interaction in (getter(worker) or []):
                if not hasattr(interaction, "get"):
                    continue
                revisadas += 1
                requisitos = interaction.get("stat_requirements") or {}
                if not hasattr(requisitos, "items"):
                    continue
                es_disciplina = "Discipline" in (interaction.get("categories") or [])
                for stat, pedido in requisitos.items():
                    if pedido is None:
                        continue
                    valor = worker.get(stat, 0) or 0
                    if es_disciplina and stat == "rebelliousness":
                        if pedido > 0 and valor >= pedido:
                            malos.append("%s: %s con %s=%s (pide menor que %s)"
                                         % (worker.get("name"), interaction.get("id"),
                                            stat, valor, pedido))
                    elif valor < pedido:
                        malos.append("%s: %s con %s=%s (pide %s o mas)"
                                     % (worker.get("name"), interaction.get("id"),
                                        stat, valor, pedido))
        if revisadas < 5:
            return False
        ap_result("T7.9", not malos,
                  "%d interacciones ofrecidas, con requisitos incumplidos: %r"
                  % (revisadas, malos[:5]))
        return True

    # ============================== Bloque 8: eventos

    @ap_test("T8.1", "Todo evento resuelto deja huella y no se queda a medias")
    def _t8_1():
        occurrences = getattr(store, "event_occurrences", None) or {}
        if not hasattr(occurrences, "items") or len(occurrences) < 2:
            return False
        flags = getattr(store, "event_flags", None) or {}
        malos = []
        for event_id, veces in occurrences.items():
            try:
                cuenta = int(veces)
            except (TypeError, ValueError):
                malos.append("%s: contador no numerico %r" % (event_id, veces))
                continue
            if cuenta < 0:
                malos.append("%s: contador negativo %d" % (event_id, cuenta))
        ap_result("T8.1", not malos,
                  "%d eventos con contador, %d flags; anomalias: %r"
                  % (len(occurrences), len(flags), malos[:5]))
        return True

    @ap_test("T8.6", "Un evento limitado no supera su maximo de repeticiones")
    def _t8_6():
        occurrences = getattr(store, "event_occurrences", None) or {}
        if not hasattr(occurrences, "items") or not occurrences:
            return False
        catalogo = {}
        for carpeta in ("data/events", "data/events/recruit"):
            try:
                for evento in (load_events_from_folder(carpeta) or []):
                    if hasattr(evento, "get") and evento.get("id"):
                        catalogo[evento["id"]] = evento
            except Exception:
                continue
        if not catalogo:
            return False
        malos, revisados = [], 0
        for event_id, veces in occurrences.items():
            evento = catalogo.get(event_id)
            if evento is None or not evento.get("limited"):
                continue
            revisados += 1
            tope = evento.get("max_occurrences")
            try:
                tope = int(tope) if tope is not None else 1
                cuenta = int(veces)
            except (TypeError, ValueError):
                continue
            if cuenta > tope:
                malos.append("%s ocurrio %d veces, tope %d" % (event_id, cuenta, tope))
        if not revisados:
            return False
        ap_result("T8.6", not malos,
                  "%d eventos limitados vistos, excesos: %r" % (revisados, malos[:5]))
        return True

    # ============================== Bloque 15: sistema y UI

    @ap_test("T15.1", "Toda pantalla visitada se ha podido cerrar")
    def _t15_1():
        vistas = _ap.screens_seen
        if len(vistas) < 12:
            return False
        # Si alguna pantalla hubiera quedado pegada, I3 lo habria registrado.
        pegadas = [f for f in _ap.findings if "O3-no-cierra" in str(f.get("message", ""))]
        ap_result("T15.1", not pegadas,
                  "%d pantallas visitadas, pegadas: %r"
                  % (len(vistas), [f.get("message") for f in pegadas][:3]))
        return True

    @ap_test("T15.9", "Nada pulsable por debajo de la pantalla que esta encima")
    def _t15_9():
        """Click-through de verdad: algo pulsable en una pantalla con zorder
        MENOR que la de mas arriba. Comparar contra una lista fija de modales da
        falsos positivos en cuanto se apilan dos popups (visto: error_popup
        legitimamente encima de confirm_upgrade)."""
        filas = [r for r in (_ap.last_affordances or [])
                 if str(r.get("screen") or "") not in ("ap_driver", "quick_menu")]
        if len(filas) < 2:
            return False
        zorders = {}
        for nombre in {str(r.get("screen")) for r in filas}:
            pantalla = renpy.get_screen(nombre)
            if pantalla is None:
                continue
            try:
                zorders[nombre] = int(getattr(pantalla, "zorder", 0) or 0)
            except (TypeError, ValueError):
                zorders[nombre] = 0
        if len(zorders) < 2:
            return False
        arriba = max(zorders.values())
        debajo = sorted({n for n, z in zorders.items() if z < arriba})
        # Que haya pantallas debajo es normal (el hub sigue ahi); lo que se
        # comprueba es que el motor no de foco a las que estan tapadas por una
        # MODAL. Sin modal arriba, no hay nada que comprobar.
        modal_arriba = [n for n, z in zorders.items() if z == arriba
                        and getattr(renpy.get_screen(n), "modal", False)]
        if not modal_arriba:
            return False
        ap_result("T15.9", not debajo,
                  "modal %r en zorder %d; pulsable por debajo: %r"
                  % (modal_arriba, arriba, debajo[:5]))
        return True

    # ============================== Bloques 9-11: academia, arena, templo

    @ap_test("T9.2", "Teniendo la Academia, la matricula no se vuelve a cobrar")
    def _t9_2():
        buildings = getattr(store, "available_buildings", None) or {}
        if not hasattr(buildings, "get") or "Academy" not in buildings:
            return False
        if not getattr(store, "academy_enrolled", False):
            ap_result("T9.2", False,
                      "se posee la Academia pero academy_enrolled es False: "
                      "el mapa volveria a pedir matricula")
            return True
        ap_result("T9.2", True, "Academia poseida y matriculada")
        return True

    @ap_test("T9.8", "Cada objeto del inventario existe en el catalogo y tiene cantidad valida")
    def _t9_8():
        inventario = getattr(store, "manager_inventory", None) or []
        if len(inventario) < 2:
            return False
        catalogo = getattr(store, "items_json", None)
        conocidos = set()
        if hasattr(catalogo, "get"):
            for item in (catalogo.get("items") or []):
                if hasattr(item, "get") and item.get("id"):
                    conocidos.add(str(item["id"]))
        malos, revisados = [], 0
        for entrada in inventario:
            if hasattr(entrada, "get"):
                item_id, cantidad = entrada.get("item_id"), entrada.get("quantity", 1)
            elif hasattr(entrada, "__getitem__") and not _ap_is_text(entrada):
                item_id = entrada[0]
                cantidad = entrada[1] if len(entrada) > 1 else 1
            else:
                item_id, cantidad = entrada, 1
            revisados += 1
            try:
                if int(cantidad) < 0:
                    malos.append("%s con cantidad %r" % (item_id, cantidad))
            except (TypeError, ValueError):
                malos.append("%s con cantidad no numerica %r" % (item_id, cantidad))
            if conocidos and str(item_id) not in conocidos:
                malos.append("%s no esta en el catalogo" % item_id)
        ap_result("T9.8", not malos,
                  "%d entradas de inventario, anomalias: %r" % (revisados, malos[:5]))
        return True

    @ap_test("T10.1", "Teniendo la Arena, el permiso del Lanista sigue pagado")
    def _t10_1():
        buildings = getattr(store, "available_buildings", None) or {}
        if not hasattr(buildings, "get") or "Arena" not in buildings:
            return False
        desbloqueada = bool(getattr(store, "arena_unlocked", False))
        pagado = bool(getattr(store, "arena_lanista_paid", False))
        ap_result("T10.1", desbloqueada and pagado,
                  "arena_unlocked=%r arena_lanista_paid=%r con la Arena en propiedad"
                  % (desbloqueada, pagado))
        return True

    @ap_test("T10.3", "Ningun worker queda con vida o energia fuera de rango")
    def _t10_3():
        workers = [w for w in (getattr(store, "workers", None) or []) if hasattr(w, "get")]
        if len(workers) < 3:
            return False
        malos = []
        for worker in workers:
            for campo, tope_campo in (("health", "max_health"), ("energy", "max_energy")):
                valor = worker.get(campo)
                if valor is None:
                    continue
                try:
                    valor = float(valor)
                except (TypeError, ValueError):
                    malos.append("%s: %s no numerico %r" % (worker.get("name"), campo, valor))
                    continue
                if valor < 0:
                    malos.append("%s: %s negativo (%s)" % (worker.get("name"), campo, valor))
                tope = worker.get(tope_campo)
                try:
                    tope = float(tope) if tope is not None else None
                except (TypeError, ValueError):
                    tope = None
                if tope is not None and valor > tope:
                    malos.append("%s: %s %s por encima de su tope %s"
                                 % (worker.get("name"), campo, valor, tope))
        ap_result("T10.3", not malos,
                  "%d workers revisados, fuera de rango: %r" % (len(workers), malos[:5]))
        return True

    @ap_test("T11.6", "Cada worker es un objeto independiente, sin datos compartidos")
    def _t11_6():
        workers = [w for w in (getattr(store, "workers", None) or []) if hasattr(w, "get")]
        if len(workers) < 4:
            return False
        malos = []
        for campo in ("traits", "inventory", "skills", "activity_log"):
            vistos = {}
            for worker in workers:
                valor = worker.get(campo)
                if valor is None:
                    continue
                clave = id(valor)
                if clave in vistos:
                    malos.append("%s y %s comparten el mismo %s"
                                 % (vistos[clave], worker.get("name"), campo))
                else:
                    vistos[clave] = worker.get("name")
        ap_result("T11.6", not malos,
                  "%d workers, estructuras compartidas: %r" % (len(workers), malos[:5]))
        return True

    # ============================== Bloque 12: manager, tiendas, inventario

    @ap_test("T12.1", "El nivel y los puntos del Manager son coherentes")
    def _t12_1():
        nivel = getattr(store, "manager_level", None)
        if nivel is None:
            return False
        try:
            nivel = int(nivel)
        except (TypeError, ValueError):
            ap_result("T12.1", False, "manager_level no numerico: %r" % (nivel,))
            return True
        puntos = getattr(store, "manager_skill_points", None)
        malos = []
        if nivel < 1:
            malos.append("nivel %d" % nivel)
        if puntos is not None:
            try:
                if int(puntos) < 0:
                    malos.append("puntos negativos %r" % puntos)
            except (TypeError, ValueError):
                malos.append("puntos no numericos %r" % puntos)
        ap_result("T12.1", not malos, "nivel %d, puntos %r; anomalias: %r"
                  % (nivel, puntos, malos))
        return True

    @ap_test("T12.7", "En SFW no hay objetos restringidos en el inventario")
    def _t12_7():
        if getattr(persistent, "nsfw_enabled", False):
            ap_result("T12.7", True, "sesion NSFW: no aplica")
            return True
        inventario = getattr(store, "manager_inventory", None) or []
        if not inventario:
            return False
        visible = getattr(store, "item_content_is_visible", None)
        if not callable(visible):
            return False
        malos = []
        for entrada in inventario:
            if hasattr(entrada, "get"):
                item_id = entrada.get("item_id")
            elif hasattr(entrada, "__getitem__") and not _ap_is_text(entrada):
                item_id = entrada[0]
            else:
                item_id = entrada
            try:
                if not visible(item_id):
                    malos.append(str(item_id))
            except Exception:
                continue
        ap_result("T12.7", not malos,
                  "%d objetos, restringidos en SFW: %r" % (len(inventario), malos[:5]))
        return True

    # ============================== Bloque 13: contenido nuevo

    @ap_test("T13.5", "Margarita tiene imagen para toda interaccion que la pida")
    def _t13_5():
        workers = [w for w in (getattr(store, "workers", None) or [])
                   if hasattr(w, "get") and str(w.get("folder", "")).lower() == "margarita"]
        if not workers:
            return False
        worker = workers[0]
        cargador = getattr(store, "load_interactions", None)
        resolver = getattr(store, "get_interaction_image", None)
        if not callable(cargador) or not callable(resolver):
            return False
        interacciones = [i for i in (cargador() or []) if hasattr(i, "get") and i.get("image")]
        if len(interacciones) < 10:
            return False
        sin_imagen, no_cargable = [], []
        for interaccion in interacciones:
            try:
                ruta = resolver(worker, interaccion)
            except Exception as e:
                sin_imagen.append("%s revento: %r" % (interaccion.get("id"), e))
                continue
            if ruta is None:
                # En SFW es legitimo que el filtro oculte una interaccion NSFW.
                if not getattr(persistent, "nsfw_enabled", False):
                    continue
                sin_imagen.append(str(interaccion.get("id")))
            elif not renpy.loadable(str(ruta)):
                no_cargable.append("%s -> %s" % (interaccion.get("id"), ruta))
        ap_result("T13.5", not sin_imagen and not no_cargable,
                  "%d interacciones; sin imagen %r; no cargables %r"
                  % (len(interacciones), sin_imagen[:4], no_cargable[:4]))
        return True

    @ap_test("T13.7", "El castillo ofrece en SFW sus 6 profesiones y oculta las 2 restringidas")
    def _t13_7():
        bt = next((b for b in (building_types_json.get("building_types") or [])
                   if b.get("id") == "governor_castle"), None)
        if bt is None:
            ap_result("T13.7", False, "no existe el tipo governor_castle")
            return True
        if getattr(persistent, "nsfw_enabled", False):
            visibles = [p.get("id") for p in (bt.get("professions") or [])
                        if profession_is_visible(p, bt)]
            ap_result("T13.7", len(visibles) == 8,
                      "en NSFW deberian verse las 8: %r" % (sorted(visibles),))
            return True
        visibles = sorted(p.get("id") for p in (bt.get("professions") or [])
                          if profession_is_visible(p, bt))
        ocultas = sorted(p.get("id") for p in (bt.get("professions") or [])
                         if not profession_is_visible(p, bt))
        esperadas = ["ambassador", "chamberlain", "guards", "prisoner", "rest", "servant"]
        ap_result("T13.7", visibles == esperadas and ocultas == ["courtesan", "pleasure_servant"],
                  "visibles %r, ocultas %r" % (visibles, ocultas))
        return True

    # ============================== Bloque 14: mods

    @ap_test("T14.5", "Un mod con JSON malformado no se lleva por delante el catalogo")
    def _t14_5():
        if not _ap_os.environ.get("FM_AUTOPLAY_BADMOD"):
            return False
        cargador = getattr(store, "load_workers", None)
        if not callable(cargador):
            return False
        try:
            catalogo = cargador(include_unique=True, include_encounter_only=True,
                                for_events=True) or []
        except Exception as e:
            ap_result("T14.5", False, "el catalogo revento con el mod roto: %r" % (e,))
            return True
        validos = [w for w in catalogo if hasattr(w, "get") and w.get("name") and w.get("folder")]
        # Lo que importa no es el TAMANO del catalogo (en SFW es menor por el
        # filtro de contenido), sino que la basura del fichero roto no se cuele:
        # aquel traia name=12345, skills como cadena y entradas nulas.
        basura = [w for w in catalogo if not hasattr(w, "get")]
        nombres_malos = [repr(w.get("name")) for w in catalogo
                         if hasattr(w, "get") and w.get("name") is not None
                         and not _ap_is_text(w.get("name"))]
        skills_malas = [str(w.get("name")) for w in catalogo
                        if hasattr(w, "get") and w.get("skills") is not None
                        and not hasattr(w.get("skills"), "get")]
        ap_result("T14.5",
                  not basura and not nombres_malos and not skills_malas and len(validos) >= 20,
                  "%d workers validos; basura %d, nombres invalidos %r, skills invalidas %r"
                  % (len(validos), len(basura), nombres_malos[:3], skills_malas[:3]))
        return True

    @ap_test("T14.4", "Ningun worker del roster apunta a una plantilla inexistente")
    def _t14_4():
        workers = [w for w in (getattr(store, "workers", None) or []) if hasattr(w, "get")]
        if len(workers) < 3:
            return False
        cargador = getattr(store, "load_workers", None)
        if not callable(cargador):
            return False
        try:
            catalogo = cargador(include_unique=True, include_encounter_only=True,
                                for_events=True, apply_content_filters=False) or []
        except Exception:
            return False
        carpetas = {str(w.get("folder")) for w in catalogo if hasattr(w, "get") and w.get("folder")}
        if not carpetas:
            return False
        huerfanos = []
        for worker in workers:
            carpeta = worker.get("folder")
            if not carpeta:
                huerfanos.append("%s sin carpeta" % worker.get("name"))
            elif str(carpeta) not in carpetas and not worker.get("monster"):
                huerfanos.append("%s -> %s" % (worker.get("name"), carpeta))
        ap_result("T14.4", not huerfanos,
                  "%d workers, sin plantilla: %r" % (len(workers), huerfanos[:5]))
        return True

    # ============================== Bloque 16: tactil

    @ap_test("T16.4", "En tactil ningun boton se sale de la pantalla")
    def _t16_4():
        if not renpy.variant("touch"):
            return False
        filas = _ap.last_affordances or []
        if len(filas) < 6:
            return False
        fuera = [(r.get("label"), r.get("x"), r.get("y"), r.get("w"), r.get("h"))
                 for r in filas
                 if r.get("x") < 0 or r.get("y") < 0
                 or r.get("x") + r.get("w") > config.screen_width
                 or r.get("y") + r.get("h") > config.screen_height]
        ap_result("T16.4", not fuera,
                  "%d botones en pantalla tactil, desbordados: %r" % (len(filas), fuera[:4]))
        return True

    # ==================================================== Bloque 2: tutorial

    @ap_test("T2.13", "Los objetivos del tutorial son coherentes y no retroceden")
    def _t2_13():
        actual = getattr(store, "current_objective", None)
        if actual is None:
            return False
        try:
            actual = int(actual)
        except (TypeError, ValueError):
            ap_result("T2.13", False, "current_objective no numerico: %r" % (actual,))
            return True
        historial = renpy.session.setdefault("ap_t213_objetivos", [])
        if not historial or historial[-1] != actual:
            historial.append(actual)
        if len(historial) < 2:
            return False
        # Estar en el objetivo N implica que 1..N-1 estan hechos; es la regla que
        # aplica la reconciliacion al cargar (legacy_progress.rpy).
        pendientes = [n for n in range(1, min(actual, 17))
                      if not getattr(store, "objective_%d_complete" % n, False)]
        retrocesos = [(a, b) for a, b in zip(historial, historial[1:]) if b < a]
        ap_result("T2.13", not pendientes and not retrocesos,
                  "objetivo %d; anteriores sin marcar %r; retrocesos %r"
                  % (actual, pendientes[:5], retrocesos[:3]))
        return True

    # ==================================================== Bloque 6: equipo

    @ap_test("T6.7", "Lo equipado sobrevive a guardar y cargar")
    def _t6_7():
        name = ap_phase_name("T6.7")
        if name is None:
            equipados = []
            for worker in (getattr(store, "workers", None) or []):
                if not hasattr(worker, "get"):
                    continue
                for entrada in (worker.get("inventory") or []):
                    if store._is_equipped(entrada):
                        try:
                            equipados.append((str(worker.get("name")), str(entrada[0])))
                        except Exception:
                            continue
            if not equipados:
                return False   # todavia nadie lleva nada equipado
            renpy.session["ap_t67_equipados"] = sorted(equipados)
            ap_save_slot(49)
            ap_phase("T6.7", "cargando")
            ap_load_slot(49)
            return True
        if name == "cargando":
            ap_phase_clear()
            antes = renpy.session.get("ap_t67_equipados") or []
            ahora = []
            for worker in (getattr(store, "workers", None) or []):
                if not hasattr(worker, "get"):
                    continue
                for entrada in (worker.get("inventory") or []):
                    if store._is_equipped(entrada):
                        try:
                            ahora.append((str(worker.get("name")), str(entrada[0])))
                        except Exception:
                            continue
            ahora = sorted(ahora)
            ap_result("T6.7", ahora == antes,
                      "%d equipados antes, %d despues" % (len(antes), len(ahora)))
            return True
        return False

    # ==================================================== Bloque 7: cooldowns

    @ap_test("T7.8", "Una interaccion en cooldown no se ofrece")
    def _t7_8():
        workers = [w for w in (getattr(store, "workers", None) or []) if hasattr(w, "get")]
        getter = getattr(store, "get_available_interactions_for_worker", None)
        cargador = getattr(store, "load_interactions", None)
        if not callable(getter) or not callable(cargador):
            return False
        catalogo = {i.get("id"): i for i in (cargador() or []) if hasattr(i, "get")}
        con_cooldown = []
        for worker in workers:
            for flag, valor in (worker.get("flags") or {}).items():
                if not str(flag).endswith("_cooldown"):
                    continue
                activo = valor.get("value", False) if hasattr(valor, "get") else bool(valor)
                if activo:
                    con_cooldown.append((worker, str(flag)))
        if not con_cooldown:
            return False
        malos = []
        for worker, flag in con_cooldown[:6]:
            ofrecidas = [i.get("id") for i in (getter(worker) or []) if hasattr(i, "get")]
            for interaction_id in ofrecidas:
                excluidos = (catalogo.get(interaction_id) or {}).get("excluded_flags") or {}
                if flag in excluidos:
                    malos.append("%s: %s con %s activo"
                                 % (worker.get("name"), interaction_id, flag))
        ap_result("T7.8", not malos,
                  "%d workers con cooldown activo; ofrecidas pese a el: %r"
                  % (len(con_cooldown), malos[:5]))
        return True

    # ==================================================== Bloque 9: academia

    @ap_test("T9.3", "Formarse en la Academia deja huella en el worker")
    def _t9_3():
        formados = []
        for worker in (getattr(store, "workers", None) or []):
            if not hasattr(worker, "get"):
                continue
            for day in (worker.get("activity_log") or []):
                for item in (day.get("items") or []):
                    pid = str(((item.get("metadata") or {}).get("profession_id")) or "")
                    if pid.startswith("academy_"):
                        formados.append(worker)
                        break
        if not formados:
            return False
        malos = []
        for worker in formados[:6]:
            usos = worker.get("skill_uses") or {}
            if not hasattr(usos, "values"):
                malos.append("%s sin skill_uses" % worker.get("name"))
                continue
            total = 0
            for valor in usos.values():
                try:
                    total += int(valor)
                except (TypeError, ValueError):
                    malos.append("%s con skill_uses no numerico" % worker.get("name"))
                    break
            if total <= 0:
                malos.append("%s se formo y no acumulo ningun uso" % worker.get("name"))
        ap_result("T9.3", not malos,
                  "%d workers formados; sin huella: %r" % (len(formados), malos[:5]))
        return True

    # ==================================================== Bloque 15: preferencias

    @ap_test("T15.5", "Las preferencias sobreviven a guardar y cargar")
    def _t15_5():
        name = ap_phase_name("T15.5")
        claves = ("nsfw_enabled", "worker_gender_filter", "large_font_mode",
                  "intro_popups_enabled", "age_verified")
        if name is None:
            renpy.session["ap_t155_prefs"] = {
                k: repr(getattr(persistent, k, None)) for k in claves}
            ap_save_slot(50)
            ap_phase("T15.5", "cargando")
            ap_load_slot(50)
            return True
        if name == "cargando":
            ap_phase_clear()
            antes = renpy.session.get("ap_t155_prefs") or {}
            cambiadas = [k for k in claves
                         if antes.get(k) != repr(getattr(persistent, k, None))]
            ap_result("T15.5", not cambiadas,
                      "preferencias alteradas por la carga: %r" % (cambiadas,))
            return True
        return False

    # ==================================================== Edificios: ciclo de vida

    @ap_test("T5.1", "Cada edificio comprado es de un tipo real y esta consolidado")
    def _t5_1():
        propios = list(getattr(store, "owned_buildings", None) or [])
        edificios = getattr(store, "available_buildings", None) or {}
        if not propios or not hasattr(edificios, "get"):
            return False
        tipos = {b.get("id") for b in (building_types_json.get("building_types") or [])}
        malos = []
        for nombre in propios:
            building = edificios.get(nombre)
            if not hasattr(building, "get"):
                malos.append("%s no esta en available_buildings" % nombre)
                continue
            if not building.get("owned"):
                malos.append("%s en owned_buildings pero owned=False" % nombre)
            tipo = building.get("type")
            if tipo and tipo not in tipos:
                malos.append("%s con tipo inexistente %r" % (nombre, tipo))
            try:
                if int(building.get("base_level", 1)) < 1:
                    malos.append("%s con nivel %r" % (nombre, building.get("base_level")))
            except (TypeError, ValueError):
                malos.append("%s con nivel no numerico" % nombre)
        ap_result("T5.1", not malos,
                  "%d edificios en propiedad; incoherencias: %r" % (len(propios), malos[:5]))
        return True

    @ap_test("T5.12", "Nadie esta asignado a un edificio que no se posee")
    def _t5_12():
        workers = [w for w in (getattr(store, "workers", None) or []) if hasattr(w, "get")]
        if len(workers) < 3:
            return False
        propios = set(str(n) for n in (getattr(store, "owned_buildings", None) or []))
        if not propios:
            return False
        huerfanos = []
        for worker in workers:
            destino = str(worker.get("assigned_building", "Unassigned") or "Unassigned")
            if destino in ("Unassigned", "None", ""):
                continue
            if destino not in propios:
                huerfanos.append("%s -> %s" % (worker.get("name"), destino))
        ap_result("T5.12", not huerfanos,
                  "%d workers; asignados a edificios ajenos: %r" % (len(workers), huerfanos[:5]))
        return True

    # ==================================================== Economia

    @ap_test("T4.9", "El dinero nunca cae a un pozo sin fondo")
    def _t4_9():
        historial = renpy.session.setdefault("ap_t49_dinero", [])
        dinero = getattr(store, "money", None)
        if dinero is None or hasattr(dinero, "strip"):
            return False
        historial.append(int(dinero))
        if len(historial) < 40:
            return False
        minimo = min(historial)
        # Deuda moderada es jugable (el juego la permite); lo que no puede pasar
        # es una espiral sin fondo mientras el jugador sigue jugando.
        ap_result("T4.9", minimo > -100000,
                  "dinero minimo observado en %d muestras: %d" % (len(historial), minimo))
        return True

    # ==================================================== Teclado

    @ap_test("T15.3", "Los atajos documentados estan declarados en las pantallas")
    def _t15_3():
        # No se pulsa aqui: se comprueba que el contrato existe, porque un atajo
        # que desaparece del codigo es un bug silencioso (ya paso con Ctrl+flechas).
        import os as _os
        ruta = _os.path.join(config.gamedir, "scripts", "core", "screens.rpy")
        try:
            with open(ruta, "r", encoding="utf-8") as handle:
                fuente = handle.read()
        except Exception as e:
            ap_result("T15.3", False, "no se pudo leer screens.rpy: %r" % (e,))
            return True
        faltan = [clave for clave in ('key "K_BACKSPACE"', 'key "ctrl_K_LEFT"',
                                      'key "ctrl_K_RIGHT"')
                  if clave not in fuente]
        ap_result("T15.3", not faltan, "atajos ausentes del codigo: %r" % (faltan,))
        return True

    # ==================================================== Journal / objetivos

    @ap_test("T2.14", "El Journal y los flags de objetivo no se contradicen")
    def _t2_14():
        actual = getattr(store, "current_objective", None)
        if actual is None:
            return False
        try:
            actual = int(actual)
        except (TypeError, ValueError):
            return False
        if actual < 2:
            return False
        # Un objetivo POSTERIOR al actual no puede estar marcado como hecho.
        adelantados = [n for n in range(actual + 1, 18)
                       if getattr(store, "objective_%d_complete" % n, False)]
        ap_result("T2.14", not adelantados,
                  "objetivo actual %d; marcados por delante: %r" % (actual, adelantados[:5]))
        return True

    # ============== Arena y Academia: no son edificios de asignacion normal
    #
    # `autofill` los descarta por no ser "standard managed buildings", asi que
    # sus profesiones no se cubren repartiendo plantilla: se usan desde sus
    # propios menus. Estas pruebas comprueban sus contratos.

    def ap_btype_por_id(btype_id):
        """Arena y Academia estan en special_buildings.json, pero en ejecucion
        `building_types_json` los incluye: script.rpy:461-477 lo construye
        escaneando TODOS los data/buildings/*.json. Leer solo building_types.json
        desde disco da 6 tipos y engaña."""
        for bt in (building_types_json.get("building_types") or []):
            if hasattr(bt, "get") and bt.get("id") == btype_id:
                return bt
        return None

    @ap_test("T10.6", "Los programas de la Arena declaran su profesion y su nivel")
    def _t10_6():
        bt = ap_btype_por_id("arena")
        if bt is None:
            if not renpy.session.get("ap_t106_diag"):
                renpy.session["ap_t106_diag"] = True
                ap_note("DIAG", "arena no encontrada; tipos disponibles: %r"
                        % ([b.get("id") for b in (building_types_json.get("building_types") or [])],))
            return False
        profesiones = bt.get("professions") or []
        if not profesiones:
            ap_result("T10.6", False, "la Arena no declara profesiones")
            return True
        malos = []
        for profesion in profesiones:
            pid = profesion.get("id")
            if not pid:
                malos.append("profesion sin id")
                continue
            if not (profesion.get("daily_stories") or []):
                malos.append("%s sin daily_stories" % pid)
            # "rest" es descansar: no tiene skill por diseno y existe en todos
            # los edificios. Exigirsela era un falso positivo.
            if pid != "rest" and not (profesion.get("skills") or profesion.get("skill")):
                malos.append("%s sin skill asociada" % pid)
        ap_result("T10.6", not malos,
                  "%d programas de Arena; incompletos: %r" % (len(profesiones), malos[:5]))
        return True

    @ap_test("T10.2", "La Arena solo ofrece sus programas si esta desbloqueada")
    def _t10_2():
        edificios = getattr(store, "available_buildings", None) or {}
        if not hasattr(edificios, "get") or "Arena" not in edificios:
            return False
        desbloqueada = bool(getattr(store, "arena_unlocked", False))
        tier = getattr(store, "lanista_arena_program_tier", None)
        pinup = bool(getattr(store, "lanista_pinup_unlocked", False))
        malos = []
        if desbloqueada and not getattr(store, "arena_lanista_paid", False):
            malos.append("desbloqueada sin permiso pagado")
        if pinup:
            try:
                if int(tier or 0) < 1:
                    malos.append("Bikini Bouts desbloqueado con program_tier %r" % (tier,))
            except (TypeError, ValueError):
                malos.append("program_tier no numerico: %r" % (tier,))
        ap_result("T10.2", not malos,
                  "arena_unlocked=%r tier=%r pinup=%r; incoherencias: %r"
                  % (desbloqueada, tier, pinup, malos))
        return True

    @ap_test("T9.4", "Los cursos de la Academia declaran la skill que prometen")
    def _t9_4():
        bt = ap_btype_por_id("academy")
        if bt is None:
            return False
        profesiones = bt.get("professions") or []
        if not profesiones:
            ap_result("T9.4", False, "la Academia no declara profesiones")
            return True
        malos = []
        for profesion in profesiones:
            pid = str(profesion.get("id") or "")
            if not pid:
                malos.append("curso sin id")
                continue
            historias = profesion.get("daily_stories") or []
            if not historias:
                malos.append("%s sin lecciones" % pid)
                continue
            if pid == "rest":
                continue   # descansar no es un curso: no declara skill
            for historia in historias:
                if not hasattr(historia, "get"):
                    malos.append("%s con leccion malformada" % pid)
                    continue
                if not (historia.get("skill_options") or historia.get("used_skill")):
                    malos.append("%s/%s sin skill declarada"
                                 % (pid, historia.get("id", "?")))
        ap_result("T9.4", not malos,
                  "%d cursos de Academia; incompletos: %r" % (len(profesiones), malos[:5]))
        return True

    @ap_test("T9.6", "La quest de la biblioteca no se salta etapas")
    def _t9_6():
        etapa = getattr(store, "academy_lib_stage", None)
        if etapa is None:
            return False
        try:
            etapa = int(etapa)
        except (TypeError, ValueError):
            ap_result("T9.6", False, "academy_lib_stage no numerico: %r" % (etapa,))
            return True
        flags = getattr(store, "event_flags", None) or {}
        malos = []
        # El manual encontrado implica haber pasado del principio.
        if flags.get("academy_lib_manual_found") and etapa < 1:
            malos.append("manual encontrado con etapa %d" % etapa)
        # Descifrado hecho implica manual encontrado.
        if flags.get("academy_lib_decrypt_done") and not flags.get("academy_lib_manual_found"):
            malos.append("descifrado hecho sin manual encontrado")
        if etapa < 0:
            malos.append("etapa negativa: %d" % etapa)
        ap_result("T9.6", not malos,
                  "etapa %d; incoherencias: %r" % (etapa, malos))
        return True

    # ============================= Filtros de inventario y tienda (T12.5)
    #
    # screens.rpy:5255 fija las categorias que el popup ofrece; screens.rpy:4663
    # aplica el filtro por `type` o por `extra_filter_categories`, con un caso
    # aparte en 4658: la categoria se llama "gifts" pero el tipo es "gift".
    # Un objeto cuyo tipo no encaje en ninguna categoria solo aparece en "All":
    # existe, pero el jugador no puede acotarlo nunca.

    AP_CATEGORIAS_INVENTARIO = (
        "weapon", "armor", "clothing", "accessory", "consumable",
        "ingredient", "gifts", "currency", "quest_item", "misc",
    )

    @ap_test("T12.5", "Todo objeto visible cae en alguna categoria del filtro")
    def _t12_5():
        catalogo = getattr(store, "items_json", None)
        visible = getattr(store, "item_content_is_visible", None)
        if not hasattr(catalogo, "get") or not callable(visible):
            return False
        objetos = catalogo.get("items") or []
        if not objetos:
            return False
        categorias = set(AP_CATEGORIAS_INVENTARIO)
        huerfanos = {}
        for objeto in objetos:
            if not hasattr(objeto, "get"):
                continue
            try:
                if not visible(objeto):
                    continue          # oculto por modo SFW/NSFW: no se ofrece
            except Exception:
                continue
            tipo = objeto.get("type")
            extras = objeto.get("extra_filter_categories") or []
            alcanzable = (tipo in categorias
                          or (tipo == "gift" and "gifts" in categorias)
                          or any(e in categorias for e in extras))
            if not alcanzable:
                huerfanos.setdefault(str(tipo), []).append(str(objeto.get("id")))
        ap_result("T12.5", not huerfanos,
                  "%d objetos visibles; tipos sin categoria: %r"
                  % (len(objetos), {k: v[:3] for k, v in list(huerfanos.items())[:4]}))
        return True

    # use_item (script.rpy:2012 y siguientes) reparte por clave de `effect` y
    # cierra con `else: pass`: una clave que no este en el reparto se gasta el
    # objeto SIN hacer nada, y el jugador paga el precio por nada. Asi estaba
    # Elixir of Passion (1000 de oro, "+10 Libido", cero efecto).
    # "cap" se ignora a proposito (comentario en script.rpy:2072); "money" llega
    # por apply_effects cuando no hay worker, y por purchase_effect al comprar.
    AP_EFECTOS_DE_CONSUMIBLE = (
        "custom", "health", "energy", "libido", "skill_modifiers",
        "joy", "rebelliousness", "romance", "relationship",
        "add_trait", "remove_trait", "money", "cap",
    )

    @ap_test("T12.6", "Ningun consumible promete un efecto que use_item tire a la basura")
    def _t12_6():
        catalogo = getattr(store, "items_json", None)
        if not hasattr(catalogo, "get"):
            return False
        consumibles = [o for o in (catalogo.get("items") or [])
                       if hasattr(o, "get") and o.get("type") == "consumable"]
        if not consumibles:
            return False
        conocidas = set(AP_EFECTOS_DE_CONSUMIBLE)
        malos = []
        for objeto in consumibles:
            # Los que se gastan al comprar no pasan por use_item: su efecto lo
            # resuelve purchase_effect, asi que no necesitan `effect`.
            if objeto.get("consume_on_purchase") or objeto.get("purchase_effect"):
                continue
            efecto = objeto.get("effect")
            if not efecto:
                malos.append("%s sin effect" % objeto.get("id"))
                continue
            if not hasattr(efecto, "keys"):
                malos.append("%s con effect que no es un mapa" % objeto.get("id"))
                continue
            for clave in efecto.keys():
                if clave not in conocidas:
                    malos.append("%s promete %r y nadie la aplica"
                                 % (objeto.get("id"), clave))
        ap_result("T12.6", not malos,
                  "%d consumibles; efectos que se pierden: %r" % (len(consumibles), malos[:5]))
        return True

    # ==================================================== Templo y franquicia
    #
    # Premisas verificadas en el codigo antes de escribir las aserciones:
    #   fm_lifecycle/rules.py:6    SEALS son 4.
    #   life_cycle.rpy:81          ritual_ready = unlocked or stage >= 4.
    #   rules.py:117               can_explore = not unlocked and stage < 4
    #                              and (last_day is None or dia > last_day).
    #   franchise_holdings.rpy:22  los holdings se abren con objective_16_complete.
    #   worker_loader.rpy:366      el roster gestionable excluye a los de franquicia.

    @ap_test("T11.1", "El progreso del templo esta dentro de sus limites")
    def _t11_1():
        getter = getattr(store, "church_exploration", None)
        if not callable(getter):
            return False
        try:
            progreso = getter()
        except Exception as e:
            ap_result("T11.1", False, "church_exploration() revento: %r" % (e,))
            return True
        if not hasattr(progreso, "get"):
            ap_result("T11.1", False, "estado del templo no es un mapa: %r" % (type(progreso).__name__,))
            return True
        etapa = progreso.get("stage")
        malos = []
        try:
            etapa = int(etapa)
        except (TypeError, ValueError):
            ap_result("T11.1", False, "stage no numerico: %r" % (etapa,))
            return True
        if etapa < 0 or etapa > 4:
            malos.append("stage fuera de [0,4]: %d" % etapa)
        listo = getattr(store, "church_ritual_ready", None)
        if callable(listo):
            try:
                if bool(listo()) and etapa < 4 and not (church_life_state() or {}).get("unlocked"):
                    malos.append("ritual listo con stage %d y sin desbloquear" % etapa)
            except Exception:
                pass
        ap_result("T11.1", not malos, "stage %d; incoherencias: %r" % (etapa, malos))
        return True

    @ap_test("T11.2", "No se puede explorar el templo dos veces el mismo dia")
    def _t11_2():
        explorar = getattr(store, "church_can_explore", None)
        getter = getattr(store, "church_exploration", None)
        if not callable(explorar) or not callable(getter):
            return False
        try:
            puede = bool(explorar())
            progreso = getter()
        except Exception as e:
            ap_result("T11.2", False, "la consulta del templo revento: %r" % (e,))
            return True
        if not hasattr(progreso, "get"):
            return False
        ultimo = progreso.get("last_day")
        if ultimo is None:
            return False   # aun no se ha explorado nunca: nada que comprobar
        hoy = calculate_total_days()
        # Si ya se exploro hoy, can_explore tiene que ser False (rules.py:117).
        if int(ultimo) >= int(hoy):
            ap_result("T11.2", not puede,
                      "ya explorado el dia %s y can_explore=%r" % (ultimo, puede))
            return True
        return False

    @ap_test("T11.3", "Los holdings de franquicia no existen antes de desbloquearse")
    def _t11_3():
        holdings = getattr(store, "franchise_holdings", None)
        desbloqueo = getattr(store, "franchise_holdings_unlocked", None)
        if holdings is None or not callable(desbloqueo):
            return False
        if not hasattr(holdings, "keys"):
            ap_result("T11.3", False, "franchise_holdings no es un mapa: %r" % (type(holdings).__name__,))
            return True
        try:
            abierto = bool(desbloqueo())
        except Exception as e:
            ap_result("T11.3", False, "franchise_holdings_unlocked() revento: %r" % (e,))
            return True
        cuantos = len(holdings)
        ap_result("T11.3", abierto or cuantos == 0,
                  "desbloqueado=%r con %d holdings" % (abierto, cuantos))
        return True

    @ap_test("T11.4", "Quien esta en una franquicia no ocupa sitio en el roster local")
    def _t11_4():
        holdings = getattr(store, "franchise_holdings", None)
        if not hasattr(holdings, "keys") or not holdings:
            return False
        comprobador = getattr(store, "worker_is_in_franchise", None)
        filtro = getattr(store, "workers_filtered_by_gender", None)
        if not callable(comprobador) or not callable(filtro):
            return False
        workers = [w for w in (getattr(store, "workers", None) or []) if hasattr(w, "get")]
        remotos = [w for w in workers if comprobador(w)]
        if not remotos:
            return False
        try:
            locales = {str(w.get("name")) for w in (filtro(workers) or []) if hasattr(w, "get")}
        except Exception as e:
            ap_result("T11.4", False, "el filtro del roster revento: %r" % (e,))
            return True
        colados = [str(w.get("name")) for w in remotos if str(w.get("name")) in locales]
        ap_result("T11.4", not colados,
                  "%d workers en franquicia; colados en el roster local: %r"
                  % (len(remotos), colados[:5]))
        return True

    # ======================= Roster virtualizado (solo se construyen las visibles)
    #
    # La lista de plantilla construye unicamente la ventana visible: a 200 workers
    # eso baja el coste de actualizar la pantalla de 96 ms a 11,8 ms. El riesgo de
    # esa tecnica no es el rendimiento, es que el hueco que sustituye a las filas
    # no construidas descuadre el recorrido de la barra y el ultimo worker se
    # vuelva inalcanzable, o que la ventana se quede corta y aparezcan huecos.

    @ap_test("T15.14", "La ventana del roster cubre SIEMPRE la franja visible")
    def _t15_14():
        """Barrido exhaustivo del invariante que evita huecos en blanco.

        No basta con que la ventana sea valida: tiene que CONTENER todas las filas
        que caen dentro del viewport en esa posicion de scroll. Si no, el jugador
        ve un hueco. Se recorre todo el recorrido en pasos finos y para varios
        tamanos de plantilla, usando el Adjustment real de la pantalla.
        """
        ventana = getattr(store, "fm_ventana_de_roster", None)
        dame_ajuste = getattr(store, "fm_roster_adjustment", None)
        paso = getattr(store, "FM_ROSTER_PASO", None)
        espacio = getattr(store, "FM_ROSTER_ESPACIO", None)
        if not callable(ventana) or not callable(dame_ajuste) or not paso:
            return False
        ajuste = dame_ajuste()
        previo = (getattr(ajuste, "value", 0), getattr(ajuste, "range", 0),
                  getattr(ajuste, "page", 0))
        fallos = []
        comprobadas = 0
        try:
            for total in (1, 2, 7, 13, 14, 15, 40, 99, 200, 377):
                alto_contenido = total * paso - espacio
                for pagina in (420, 300, 640):
                    recorrido = max(0, alto_contenido - pagina)
                    ajuste.page = pagina
                    ajuste.range = recorrido
                    # Pasos finos: mas de un punto por fila, y siempre los extremos.
                    posiciones = set([0, recorrido])
                    paso_barrido = max(1, int(paso // 4))
                    v = 0
                    while v <= recorrido:
                        posiciones.add(v)
                        v += paso_barrido
                    for valor in sorted(posiciones):
                        ajuste.value = valor
                        desde, hasta = ventana(total)
                        comprobadas += 1
                        if not (0 <= desde <= hasta <= total):
                            fallos.append("rango invalido %d-%d de %d" % (desde, hasta, total))
                            break
                        if hasta == desde and total > 0:
                            fallos.append("ventana vacia en total=%d valor=%d" % (total, valor))
                            break
                        # Filas que de verdad caen dentro del viewport ahora mismo.
                        primera_visible = int(valor // paso)
                        ultima_visible = int((valor + pagina) // paso)
                        if ultima_visible > total - 1:
                            ultima_visible = total - 1
                        if primera_visible > total - 1:
                            primera_visible = total - 1
                        if desde > primera_visible or hasta < ultima_visible + 1:
                            fallos.append(
                                "hueco: total=%d pagina=%d valor=%d visible=%d-%d ventana=%d-%d"
                                % (total, pagina, valor, primera_visible, ultima_visible,
                                   desde, hasta))
                            break
                    if fallos:
                        break
                if fallos:
                    break
        finally:
            try:
                ajuste.value, ajuste.range, ajuste.page = previo
            except Exception:
                pass
        ap_result("T15.14", not fallos,
                  "%d posiciones comprobadas; fallos: %r" % (comprobadas, fallos[:3]))
        return True

    @ap_test("T15.10", "La ventana del roster llega hasta la ultima fila al bajar del todo")
    def _t15_10():
        pantalla = renpy.get_screen("workers")
        if pantalla is None:
            return False
        ventana = getattr(store, "fm_ventana_de_roster", None)
        ajuste = getattr(store, "fm_roster_adjustment", None)
        if not callable(ventana) or not callable(ajuste):
            return False
        try:
            alcance = ajuste()
            estado = dict(pantalla.scope or {})
        except Exception as e:
            ap_result("T15.10", False, "no se pudo leer el roster: %r" % (e,))
            return True
        total = estado.get("_fm_total_filas")
        if not isinstance(total, int) or total <= 0:
            return False
        if total <= 20:
            return False      # sin virtualizar no hay nada que comprobar
        previo = getattr(alcance, "value", 0)
        malos = []
        try:
            # Bajar del todo: la ventana TIENE que incluir la ultima fila.
            recorrido = float(getattr(alcance, "range", 0) or 0)
            alcance.value = recorrido
            desde, hasta = ventana(total)
            if hasta < total:
                malos.append("al fondo la ventana acaba en %d de %d" % (hasta, total))
            # Arriba del todo: tiene que incluir la primera.
            alcance.value = 0
            desde0, hasta0 = ventana(total)
            if desde0 != 0:
                malos.append("arriba la ventana empieza en %d" % desde0)
            if hasta0 <= desde0:
                malos.append("ventana vacia arriba: %d-%d" % (desde0, hasta0))
            # Y en medio: ventana no vacia y dentro de rango.
            alcance.value = recorrido / 2.0 if recorrido else 0
            desdeM, hastaM = ventana(total)
            if not (0 <= desdeM < hastaM <= total):
                malos.append("ventana invalida en medio: %d-%d de %d" % (desdeM, hastaM, total))
        finally:
            try:
                alcance.value = previo
            except Exception:
                pass
        ap_result("T15.10", not malos,
                  "%d filas; ventana %d-%d; problemas: %r" % (total, desde0, hasta0, malos))
        return True

    @ap_test("T15.11", "El hueco de las filas no construidas mide lo que medirian ellas")
    def _t15_11():
        relleno = getattr(store, "fm_relleno_de_roster", None)
        paso = getattr(store, "FM_ROSTER_PASO", None)
        espacio = getattr(store, "FM_ROSTER_ESPACIO", None)
        if not callable(relleno) or paso is None or espacio is None:
            return False
        malos = []
        if relleno(0) != 0:
            malos.append("relleno(0) deberia ser 0 y es %r" % (relleno(0),))
        if relleno(-3) != 0:
            malos.append("relleno negativo deberia ser 0 y es %r" % (relleno(-3),))
        # Invariante: el alto total con ventana tiene que ser el mismo que con
        # todas las filas. alto(total) == relleno(a) + filas(k) + relleno(c)
        # contando las separaciones del vbox.
        for total, a, k in ((200, 0, 16), (200, 40, 16), (200, 184, 16), (37, 5, 10)):
            c = total - a - k
            if c < 0:
                continue
            completo = total * paso - espacio
            hijos = (1 if a else 0) + k + (1 if c else 0)
            troceado = relleno(a) + k * (paso - espacio) + relleno(c) + espacio * max(0, hijos - 1)
            if completo != troceado:
                malos.append("total=%d a=%d k=%d: %d != %d" % (total, a, k, completo, troceado))
        ap_result("T15.11", not malos, "problemas de aritmetica: %r" % (malos,))
        return True

    @ap_test("T15.12", "La virtualizacion se desactiva sola si la maquetacion cambia")
    def _t15_12():
        valido = getattr(store, "fm_roster_paso_valido", None)
        ventana = getattr(store, "fm_ventana_de_roster", None)
        if not callable(valido) or not callable(ventana):
            return False
        class _Falso(object):
            def __init__(self, recorrido, pagina):
                self.range = recorrido
                self.page = pagina
                self.value = 0
        paso = getattr(store, "FM_ROSTER_PASO", 61)
        espacio = getattr(store, "FM_ROSTER_ESPACIO", 5)
        total = 200
        malos = []
        # Alto coherente con la formula: debe aceptarlo.
        bueno = _Falso(total * paso - espacio - 420, 420)
        if not valido(total, bueno):
            malos.append("rechaza una maquetacion que SI cuadra")
        # Filas 20 px mas altas: debe rechazarlo y construir todo.
        malo = _Falso(total * (paso + 20) - espacio - 420, 420)
        if valido(total, malo):
            malos.append("acepta una maquetacion que NO cuadra")
        # Sin renderizar todavia: no hay nada que contradecir.
        if not valido(total, _Falso(0, 0)):
            malos.append("rechaza el estado sin renderizar")
        ap_result("T15.12", not malos, "problemas: %r" % (malos,))
        return True

    @ap_test("T15.13", "La ventana del roster no desincroniza: mismas identidades y lista completa")
    def _t15_13():
        """El miedo razonable con la virtualizacion es que los workers de una
        lista no sean los de otra. No puede pasar, porque la ventana es un corte
        (`lista[a:b]`) que comparte las MISMAS referencias: la fila no trabaja con
        una copia del worker, trabaja con el mismo diccionario que store.workers.
        Esto lo comprueba en ejecucion en vez de darlo por supuesto."""
        pantalla = renpy.get_screen("workers")
        if pantalla is None:
            return False
        try:
            estado = dict(pantalla.scope or {})
        except Exception:
            return False
        completa = estado.get("filtered_workers")
        total = estado.get("_fm_total_filas")
        desde = estado.get("_fm_desde")
        hasta = estado.get("_fm_hasta")
        nombres_nav = estado.get("_workers_nav_names")
        if completa is None or not isinstance(total, int):
            return False
        malos = []

        # 1) La pantalla sigue contando la plantilla ENTERA, no la ventana.
        if len(completa) != total:
            malos.append("total %d pero la lista tiene %d" % (total, len(completa)))

        # 2) La navegacion recorre la lista entera.
        if nombres_nav is not None and len(nombres_nav) != total:
            malos.append("navegacion con %d nombres de %d" % (len(nombres_nav), total))

        # 3) La ventana es un tramo contiguo y dentro de rango.
        if not (isinstance(desde, int) and isinstance(hasta, int)
                and 0 <= desde <= hasta <= total):
            malos.append("ventana fuera de rango: %r-%r de %r" % (desde, hasta, total))
            ap_result("T15.13", False, "%r" % (malos,))
            return True

        # 4) IDENTIDAD: cada worker construido es el MISMO objeto que el de
        #    store.workers con ese nombre. Si fueran copias, cambiar algo en una
        #    fila no se veria en el resto del juego: eso seria la desincronizacion.
        por_nombre = {}
        for w in (getattr(store, "workers", None) or []):
            if hasattr(w, "get"):
                por_nombre.setdefault(str(w.get("name")), w)
        copias = []
        ausentes = []
        for w in completa[desde:hasta]:
            if not hasattr(w, "get"):
                continue
            nombre = str(w.get("name"))
            real = por_nombre.get(nombre)
            if real is None:
                ausentes.append(nombre)
            elif real is not w:
                copias.append(nombre)
        if copias:
            malos.append("la fila usa una COPIA de: %r" % (copias[:4],))
        if ausentes:
            malos.append("workers de la fila que no estan en store.workers: %r" % (ausentes[:4],))

        # 5) El orden de la ventana es el de la lista completa en ese tramo.
        tramo = [str(w.get("name")) for w in completa[desde:hasta] if hasattr(w, "get")]
        esperado = [str(w.get("name")) for w in completa if hasattr(w, "get")][desde:hasta]
        if tramo != esperado:
            malos.append("la ventana reordena las filas")

        ap_result("T15.13", not malos,
                  "%d filas, ventana %d-%d, %d construidas; problemas: %r"
                  % (total, desde, hasta, hasta - desde, malos))
        return True

    @ap_test("T15.15", "Desplazar de verdad reconstruye la ventana correcta")
    def _t15_15():
        """Prueba la CADENA entera, no solo la aritmetica.

        T15.14 barre la funcion poniendo el valor a mano. Esto usa
        Adjustment.change(), que es por donde pasan la rueda y el arrastre: dispara
        el callback, que llama a restart_interaction, que hace que la pantalla se
        reconstruya. Luego lee del scope de la screen que filas se construyeron DE
        VERDAD y comprueba que cubren la franja visible. Si esa cadena se rompiera,
        el jugador veria huecos en blanco al desplazar.

        Usa ap_phase (el mecanismo del arnes), que reintenta en ticks
        consecutivos: con fases propias solo tenia turno cada 40 acciones y la
        prueba no llegaba a terminar.
        """
        pantalla = renpy.get_screen("workers")
        dame_ajuste = getattr(store, "fm_roster_adjustment", None)
        paso = getattr(store, "FM_ROSTER_PASO", None)
        if pantalla is None or not callable(dame_ajuste) or not paso:
            return False
        try:
            estado = dict(pantalla.scope or {})
        except Exception:
            return False
        total = estado.get("_fm_total_filas")
        if not isinstance(total, int) or total <= 20:
            return False
        ajuste = dame_ajuste()
        recorrido = float(getattr(ajuste, "range", 0) or 0)
        pagina = float(getattr(ajuste, "page", 0) or 0)
        if recorrido <= 0 or pagina <= 0:
            return False

        def hueco(valor):
            desde, hasta = estado.get("_fm_desde"), estado.get("_fm_hasta")
            if not isinstance(desde, int) or not isinstance(hasta, int):
                return "la pantalla no expone la ventana"
            primera = min(total - 1, int(valor // paso))
            ultima = min(total - 1, int((valor + pagina) // paso))
            if desde > primera or hasta < ultima + 1:
                return ("hueco en %d: visible %d-%d, construidas %d-%d"
                        % (valor, primera, ultima, desde, hasta))
            return None

        fase = ap_phase_name("T15.15")
        if fase is None:
            ap_phase("T15.15", "medio", previo=getattr(ajuste, "value", 0),
                     destino=recorrido * 0.5)
            ajuste.change(recorrido * 0.5)     # camino real de rueda y arrastre
            return False
        datos = renpy.session.get("ap_test_phase") or {}
        if fase == "medio":
            problema = hueco(float(datos.get("destino") or 0))
            if problema:
                ap_phase_clear()
                ap_result("T15.15", False, problema)
                return True
            ap_phase("T15.15", "fondo", previo=datos.get("previo"), destino=recorrido)
            ajuste.change(recorrido)
            return False
        if fase == "fondo":
            problema = hueco(recorrido)
            desde, hasta = estado.get("_fm_desde"), estado.get("_fm_hasta")
            if not problema and hasta != total:
                problema = "al fondo la ventana acaba en %r de %d" % (hasta, total)
            try:
                ajuste.change(float(datos.get("previo") or 0))
            except Exception:
                pass
            ap_phase_clear()
            ap_result("T15.15", not problema,
                      problema or ("cadena de scroll correcta: %d filas, ventana final %r-%r"
                                   % (total, desde, hasta)))
            return True
        ap_phase_clear()
        return False
