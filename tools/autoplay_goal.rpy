# Jugador con objetivo: intenta PASARSE el juego, no recorrer pantallas.
#
# Se monta encima de tools/autoplay.rpy y reutiliza su percepcion (focus_list),
# su actuacion (clics SDL reales) y sus invariantes. Lo unico que cambia es el
# cerebro: en vez de explorar en anchura, lee el objetivo del Journal y persigue
# el siguiente paso que lo acerca, como haria un jugador.
#
# Contrato (el mismo que el explorador): MIRA el estado como lo veria alguien
# delante de la pantalla (dinero, plantilla, objetivo) y ACTUA solo con clics y
# teclas reales. Nunca escribe en el store ni llama a la logica del juego.
#
# Solo se copia a la copia desechable con `tools/autoplay.py --goal`.
#
# Capas:
#   OBJETIVO    ap_goal_plan()      -> que tareas tocan ahora, por objetivo
#   TAREAS      _g_task_*()         -> el siguiente clic de cada tarea
#   NAVEGACION  _g_go_hub()/_g_*    -> reconocer pantallas y botones, volver
#   ORACULOS    ap_goal_oracles()   -> lo que solo ve quien intenta ganar

init 5 python:
    import json as _g_json
    import os as _g_os
    import re as _g_re

    # Objetivo al que se considera "pasado" el tramo. 9 = completar del 1 al 8.
    AP_GOAL_TARGET = int(_g_os.environ.get("FM_GOAL_TARGET") or 9)

    # Tipo del primer edificio. Tavern: sus tres profesiones tiran de Charm y
    # Service, que es lo que traen casi todos los workers iniciales.
    AP_GOAL_BUILDING = (_g_os.environ.get("FM_GOAL_BUILDING") or "Tavern").strip()

    # Dias que un jugador razonable tardaria como mucho en cada objetivo. Pasarse
    # no es un crash: es "esto no se puede conseguir jugando bien", que es
    # justo lo que un explorador nunca ve.
    AP_GOAL_DAY_BUDGET = {1: 3, 2: 3, 3: 3, 4: 30, 5: 6, 6: 20, 7: 6, 8: 90,
                          9: 200, 10: 80, 11: 40, 12: 90, 13: 90, 14: 200, 15: 60, 16: 200}

    # Clics que una tarea puede gastar en un dia antes de darla por atascada.
    AP_GOAL_TASK_CLICKS = 40

    # Colchon de dinero: el jugador no gasta por debajo de esto salvo para el
    # objetivo que lo pide. La bancarrota es a -5000, pero quedarse a cero con
    # costes diarios es la espiral que un jugador evita.
    AP_GOAL_RESERVE = 800

    # Huecos del mapa por precio (gui/map/<ID>a.png). El mas barato primero.
    AP_GOAL_MAP_SLOTS = [
        ("S2Tavern", 15000), ("N5Tavern", 15000), ("S4Tavern", 15000),
        ("S3Bluehouse", 20000), ("N1Bluehouse", 20000), ("N3Bluehouse", 20000),
        ("S1Redhouse", 25000), ("S4Redhouse", 25000), ("N4Redhouse", 25000),
        ("S1Greenhouse", 30000), ("N2Greenhouse", 30000), ("N5Greenhouse", 30000),
    ]

    # Botones de habilidad de edificio, por tipo.
    AP_GOAL_SKILL_BUTTON = ("Equipment", "Ingredients", "Hag Potions",
                            "Accommodations", "Security")

    class _APGoal(object):
        """Fuera del store, igual que _ap: no entra en rollback ni en saves."""
        def __init__(self):
            self.day_key = None
            self.days_played = 0
            self.obj = None
            self.obj_since_day = 0
            self.timeline = []
            self.task = None
            self.task_clicks = {}
            self.task_failed = {}
            self.task_fail_days = {}
            self.recruit_day = None
            self.autofill_done = set()
            self.journal_day = None
            self.journal_opens_on_obj = 0
            self.lunch_tried = set()
            self.skill_plus_clicked = False
            self.confirm_yes = False
            self.popups_off = False
            self.game_seen = False
            self.finished = False
            self.manager_for = None
            self.money_by_day = []
            self.stalled = set()
            self.potion_search = 0
            self.journal_scrolls = 0
            self.journal_arrow = False
            self.money_pre_advance = None
            self.net_by_day = []
            self.buildings_seen = None
            self.buildings_sold = set()
            self.type_changes_allowed = set()
            self.experiments = []
            self.exp_running = None
            self.exp_current = None
            self.exp_rotation = 0
            self.exp_done = set()
            self.ledger = []
            self.last_experiment_day = None
            self.endgame_start = None
            self.franchise_open = False
            self.arena_started = False
            self.special_day = None
            self.types_failed = set()
            self.lab_day = None
            self.academy_logged = False
            self.alchemy_before = None
            self.church_day = None
            self.church_visits = 0
            self.church_pref_day = None
            self.ritual_idx = 0
            self.last_choice_label = ""
            self.last_choice_gain_rep = False
            self.shop_open = None
            self.shop_scrolls = 0
            self.shop_stale = 0
            self.universal_clicks = {}
            self.staff_failed = set()
            self.staff_scrolls = 0
            self.staff_day = None
            self.list_seen = {}
            self.list_stale = {}
            self.list_turns = {}
            self.shops_done = set()
            self.equip_tried = set()
            self.equip_day = None
            self.equip_target = None
            self.equip_scrolls = 0

    _apg = _APGoal()

    # ------------------------------------------------------------ PERCEPCION

    def _g_dname(d, depth=0):
        """Nombre de fichero de un displayable de imagen, atravesando envoltorios."""
        if d is None or depth > 5:
            return ""
        for attr in ("filename", "name"):
            value = getattr(d, attr, None)
            if _ap_is_text(value) and value:
                return value
            if value is not None and not _ap_is_text(value) and hasattr(value, "__iter__"):
                try:
                    joined = " ".join(str(x) for x in value)
                except Exception:
                    joined = ""
                if joined:
                    return joined
        for attr in ("target", "child", "image"):
            inner = getattr(d, attr, None)
            if inner is not None and inner is not d:
                found = _g_dname(inner, depth + 1)
                if found:
                    return found
        return ""

    def _g_img(row):
        """Imagen de un imagebutton. Los botones de cerrar y los edificios del
        mapa NO tienen texto ni alt: sin esto el jugador no sabe cerrar nada."""
        if "img" in row:
            return row["img"]
        name = ""
        widget = row.get("widget")
        states = getattr(widget, "state_children", None)
        if states and hasattr(states, "get"):
            d = states.get("idle_") or states.get("insensitive_")
            if d is None:
                for value in states.values():
                    d = value
                    break
            name = _g_dname(d)
        if not name:
            name = _g_dname(widget)
        row["img"] = str(name).replace("\\", "/")
        return row["img"]

    def _g_label(row):
        # El TTS anade " selected" al boton que tiene el foco o esta marcado
        # ("Back selected"): es estado, no parte del nombre.
        label = (row.get("label") or "").strip()
        if label == "selected":
            return ""  # imagebutton con foco: solo queda el estado
        if label.endswith(" selected"):
            label = label[:-len(" selected")].rstrip()
        return label

    def _g_find(rows, text=None, exact=False, screen=None, img=None, prefix=False):
        for row in rows:
            if screen is not None and row.get("screen") != screen:
                continue
            if img is not None and img not in _g_img(row):
                continue
            if text is not None:
                label = _g_label(row).lower()
                want = text.lower()
                if exact and label != want:
                    continue
                if prefix and not label.startswith(want):
                    continue
                if not exact and not prefix and want not in label:
                    continue
            return row
        return None

    def _g_same_row(rows, anchor, text, side=None):
        """El boton `text` que esta en la misma fila que `anchor`. En inventario
        y tienda todos los botones se llaman igual ('Buy', 'Right', 'Use'): lo
        unico que los distingue es en que fila estan."""
        ay = anchor["y"] + anchor["h"] // 2
        best, best_d = None, None
        for row in rows:
            if _g_label(row).lower() != text.lower():
                continue
            if side == "left" and row["x"] > config.screen_width // 2:
                continue
            if side == "right" and row["x"] < config.screen_width // 2:
                continue
            d = abs(row["y"] + row["h"] // 2 - ay)
            if d > max(anchor["h"], row["h"]):
                continue
            if best_d is None or d < best_d:
                best, best_d = row, d
        return best

    def _g_is_close(row):
        label = _g_label(row).lower()
        if label in ("close", "back", "return", "cerrar", "volver", "ok", "continue"):
            return True
        img = _g_img(row).lower()
        # Las flechas del historial de dialogo NO avanzan: navegan hacia atras.
        if "arrow" in img:
            return False
        return (not label) and ("return" in img or "close" in img)

    def _g_screens(rows):
        return set(r.get("screen") for r in rows)

    def _g_at_hub(rows):
        screens = _g_screens(rows) - {"quick_menu", "ap_driver", None}
        return screens == {"tavern"}

    def _g_today():
        return (getattr(store, "current_year", 0), getattr(store, "current_month", 0),
                getattr(store, "current_day", 0))

    def _g_money():
        try:
            return int(getattr(store, "money", 0) or 0)
        except Exception:
            return 0

    def _g_workers():
        return [w for w in (getattr(store, "workers", None) or []) if hasattr(w, "get")]

    def _g_unassigned():
        return [w for w in _g_workers()
                if (w.get("assigned_building") or "Unassigned") == "Unassigned"]

    def _g_assigned_count():
        return len(_g_workers()) - len(_g_unassigned())

    def _g_owned():
        return [str(b) for b in (getattr(store, "owned_buildings", None) or [])]

    def _g_building_names():
        """Edificios propios que cuentan para el objetivo 8 (no Arena/Academia)."""
        return [b for b in _g_owned() if b not in ("Arena", "Academy")]

    # ------------------------------------------------------------ NAVEGACION

    def _g_go_hub(rows):
        """Volver al hub cerrando lo que haya encima, como haria una persona."""
        if _g_at_hub(rows):
            return None
        for row in rows:
            if row.get("screen") == "tavern":
                continue
            if _g_is_close(row):
                return row
        no = _g_find(rows, "No", exact=True)
        if no is not None:
            return no
        return None

    def _g_open_from_hub(rows, button):
        """Paso de navegacion desde el hub: si no estamos en el, volver."""
        if _g_at_hub(rows):
            return _g_find(rows, button, exact=True, screen="tavern")
        return _g_go_hub(rows)

    def _g_open_manager(rows, building):
        """Abrir la pantalla Manager de un edificio concreto."""
        shown = _g_screens(rows)
        if "Manager" in shown and _apg.manager_for == building:
            return "HERE"
        if "Building_select_global" in shown:
            for row in rows:
                if row.get("screen") != "Building_select_global":
                    continue
                label = _g_label(row)
                if label.endswith(": " + building) or label == building:
                    _apg.manager_for = building
                    return row
            return _g_go_hub(rows)
        if "Manager" in shown:
            back = _g_find(rows, "Back", exact=True, screen="Manager")
            return back or _g_go_hub(rows)
        return _g_open_from_hub(rows, "Buildings")

    # -------------------------------------------------- PANTALLAS UNIVERSALES
    #
    # Lo que aparece solo (eventos, informes, avisos) y hay que despachar sea
    # cual sea la tarea. Devuelve la fila a pulsar o None si no aplica.

    def _g_option_cost(label):
        """Monedas que pide una opcion, si las dice ("Invest 10,000 coins")."""
        best = 0
        for m in _g_re.finditer(r"\$?(\d{1,3}(?:,\d{3})+|\d+)\s*(?:coins|gold)?", label):
            text = m.group(0).lower()
            if "$" in text or "coin" in text or "gold" in text:
                best = max(best, int(m.group(1).replace(",", "")))
        return best

    # Desbloqueos que el jugador sabe que necesita (tiendas 2 y 3: anillo,
    # espada y el equipo de los objetivos 12-16).
    AP_GOAL_UNLOCK_WORDS = ("adventurer's market", "emporium", "merchant's favor",
                            "pay the debt yourself")

    def _g_option_score(label):
        """Lo que valora quien persigue el objetivo: no tocar el dinero que
        esta ahorrando, preferir lo que da algo y lo que no arriesga."""
        low = label.lower()
        score = 0.0
        if any(w in low for w in AP_GOAL_UNLOCK_WORDS):
            cost = _g_option_cost(label) or 800
            if _g_money() - cost >= 3000 and getattr(store, "current_objective", 1) != 10:
                return 10.0
        if "gain:" in low:
            score += 1
        if "risk" in low:
            score -= 1
        cost = _g_option_cost(label)
        money = max(_g_money(), 1)
        if "cost: money" in low or cost:
            # Gastar una fraccion pequena es aceptable; una grande, no.
            share = (cost / float(money)) if cost else 0.25
            score -= 4 * share + (0 if money > 3000 else 1)
        return score

    def _g_event_option(rows, screen):
        options = [r for r in rows if r.get("screen") == screen and _g_label(r)
                   and "(locked)" not in _g_label(r).lower()]
        if not options:
            return None
        scored = [(_g_option_score(_g_label(r)), _ap_random.random(), r) for r in options]
        scored.sort(key=lambda t: (t[0], t[1]), reverse=True)
        pick = scored[0][2]
        _apg.last_choice_label = _g_label(pick)
        _apg.last_choice_gain_rep = "gain: reputation" in _g_label(pick).lower()
        ap_note("DECIDE", "%s: %r (puntos %.2f de %d opciones)"
                % (screen, _g_label(pick)[:70], scored[0][0], len(options)))
        return pick

    def _g_guard_universal(rows, row):
        """Las pantallas que se despachan solas no pasan por el tope de clics
        de las tareas. Sin este tope, un Yes que el juego rechaza ("no tienes
        dinero") y vuelve a ofrecer se repitio 1.500 veces."""
        key = (_g_today(), row.get("screen"), _g_label(row))
        veces = _apg.universal_clicks.get(key, 0) + 1
        _apg.universal_clicks[key] = veces
        if veces <= 15:
            return row
        if veces == 16:
            ap_note("LOOP", "%r en %s pulsado 15 veces hoy: se cancela"
                    % (_g_label(row)[:40], row.get("screen")))
        for alt in rows:
            if alt.get("screen") == row.get("screen") and alt is not row:
                if _g_label(alt) in ("No", "Cancel") or _g_is_close(alt):
                    return alt
        return _g_go_hub(rows) or row

    def _g_universal(rows):
        shown = _g_screens(rows)

        if "screen_intro_popup" in shown:
            if not _apg.popups_off:
                stop = _g_find(rows, "Stop showing these messages", screen="screen_intro_popup")
                if stop is not None:
                    _apg.confirm_yes = True
                    return stop
            for row in rows:
                if row.get("screen") == "screen_intro_popup" and _g_is_close(row):
                    return row

        if "confirm" in shown:
            if _apg.confirm_yes:
                _apg.confirm_yes = False
                if not _apg.popups_off:
                    _apg.popups_off = True
                return _g_find(rows, "Yes", exact=True, screen="confirm")
            return _g_find(rows, "No", exact=True, screen="confirm")

        if "manager_levelup_benefit" in shown:
            found = _g_find(rows, "Continue", screen="manager_levelup_benefit")
            if found is not None:
                return found
        if "skip_tutorial_confirm" in shown:
            return _g_find(rows, "No, Continue", screen="skip_tutorial_confirm")
        for screen in ("confirm_buy_worker", "confirm_upgrade", "confirm_buy_potion"):
            if screen in shown:
                return _g_find(rows, "Yes", exact=True, screen=screen)
        for screen in ("confirm_refresh_workers", "confirm_change_type", "confirm_sell_worker"):
            if screen in shown:
                return _g_find(rows, "No", exact=True, screen=screen)

        if "recruitment_choice_screen" in shown:
            options = [r for r in rows if r.get("screen") == "recruitment_choice_screen"
                       and _g_label(r) and "examine" not in _g_label(r).lower()]
            if options:
                # La primera opcion contrata en todos los reclutamientos
                # publicados; la ultima rechaza.
                options.sort(key=lambda r: r["y"])
                return options[0] if _g_want_more_workers() else options[-1]
        if "recruitment_event_screen" in shown:
            want = "Recruit them" if _g_want_more_workers() else "Refuse them"
            return _g_find(rows, want, screen="recruitment_event_screen")
        for screen in ("recruitment_outcome", "interaction_result", "auto_advance_summary",
                       "error_popup", "monthly_card", "daily_report", "report_details",
                       "gender_filter_after_load_warning"):
            if screen in shown:
                if screen == "auto_advance_summary":
                    found = _g_find(rows, "Continue", screen=screen)
                    if found is not None:
                        return found
                if screen == "gender_filter_after_load_warning":
                    found = _g_find(rows, "Keep Filter", screen=screen)
                    if found is not None:
                        return found
                for row in rows:
                    if row.get("screen") == screen and _g_is_close(row):
                        return row
                mine = [r for r in rows if r.get("screen") == screen]
                if mine and screen in ("recruitment_outcome", "interaction_result", "error_popup"):
                    return mine[0]

        if "choose_event_worker_screen" in shown:
            # "Kar - Combat 83 (+10 event) vs 70 -> 93%": el de mas probabilidad.
            best, best_p = None, -1
            for row in rows:
                if row.get("screen") != "choose_event_worker_screen" or not _g_label(row):
                    continue
                m = _g_re.search(r"(\d+)%", _g_label(row))
                p = int(m.group(1)) if m else 0
                if p > best_p:
                    best, best_p = row, p
            if best is not None:
                return best
        if "random_event_choice" in shown:
            pick = _g_event_option(rows, "random_event_choice")
            if pick is not None:
                return pick
        if "choice" in shown:
            pick = _g_round_answer(rows, "choice") or _g_choice_pref(rows, "choice")
            if pick is not None:
                return pick
            pick = _g_event_option(rows, "choice")
            if pick is not None:
                return pick
        if "training_branch_menu" in shown:
            pick = _g_event_option(rows, "training_branch_menu")
            if pick is not None:
                return pick
        if "training_branch_narration" in shown:
            mine = [r for r in rows if r.get("screen") == "training_branch_narration"]
            if mine:
                return mine[0]
        return None

    # ---------------------------------------------------------------- TAREAS
    #
    # Cada tarea devuelve una fila a pulsar, "DONE" si ya no hace falta, o
    # "WAIT" si no se puede hacer hoy (falta dinero, ya se hizo hoy...).

    def _g_want_more_workers():
        obj = getattr(store, "current_objective", 1) or 1
        target = 10 if obj <= 8 else 16
        return len(_g_workers()) < target

    def _g_task_skill(rows):
        if getattr(store, "manager_start_skill_chosen", False):
            return "DONE"
        shown = _g_screens(rows)
        if "manager_character_sheet" in shown:
            confirm = _g_find(rows, "Confirm", exact=True, screen="manager_character_sheet")
            if confirm is not None:
                return confirm
            pluses = sorted([r for r in rows if r.get("screen") == "manager_character_sheet"
                             and _g_label(r) == "+"], key=lambda r: r["y"])
            if pluses:
                return pluses[0]
            return None
        name = ("%s %s" % (getattr(store, "player_title", ""),
                           getattr(store, "player_name", ""))).strip()
        return _g_open_from_hub(rows, name)

    def _g_task_recruit(rows):
        if _apg.recruit_day == _g_today():
            return "DONE"
        if not _g_want_more_workers():
            return "DONE"
        shown = _g_screens(rows)
        if "map_screen" in shown:
            found = _g_find(rows, "Recruit Workers", screen="map_screen")
            if found is not None:
                _apg.recruit_day = _g_today()
                return found
            return "WAIT"
        return _g_open_from_hub(rows, "Explore")

    def _g_task_buy_servants(rows, target):
        if len(_g_workers()) >= target:
            return "DONE"
        if _g_money() < 1600 + AP_GOAL_RESERVE:
            return "WAIT"
        shown = _g_screens(rows)
        if "buy_servants_table" in shown:
            buys = [r for r in rows if r.get("screen") == "buy_servants_table"
                    and _g_label(r) == "Buy" and r.get("sensitive", True)]
            if buys:
                return _ap_random.choice(buys)
            return "WAIT"
        if "map_screen" in shown:
            return _g_find(rows, "Buy Servants", screen="map_screen") or "WAIT"
        return _g_open_from_hub(rows, "Explore")

    def _g_task_set_type(rows):
        if getattr(store, "building_1_type_set", False):
            return "DONE"
        shown = _g_screens(rows)
        if "building_type_selection" in shown:
            for name in (AP_GOAL_BUILDING, "Tavern", "Restaurant"):
                found = _g_find(rows, name, exact=True, screen="building_type_selection")
                if found is not None:
                    return found
            return None
        if "Manager" in shown:
            return _g_find(rows, "Building Type", exact=True, screen="Manager")
        if "Building_select_global" in shown:
            found = _g_find(rows, "Unassigned:", prefix=True, screen="Building_select_global")
            if found is not None:
                _apg.manager_for = _g_label(found).split(": ", 1)[-1]
                return found
        return _g_open_from_hub(rows, "Buildings")

    def _g_task_autofill(rows, building):
        key = (_g_today(), building)
        if key in _apg.autofill_done or not _g_unassigned():
            return "DONE"
        step = _g_open_manager(rows, building)
        if step != "HERE":
            return step
        found = _g_find(rows, "Auto-fill empty slots", screen="Manager")
        _apg.autofill_done.add(key)
        return found or "WAIT"

    def _g_task_journal(rows, mark=False):
        """Abrir el Journal: reevalua objetivos y deja leer el actual."""
        shown = _g_screens(rows)
        if "journal_panel" in shown:
            if mark:
                found = _g_journal_action(rows)
                if found is not None:
                    if _apg.journal_scrolls and _apg.journal_arrow:
                        # Bajo el pliegue, pero la flecha lo avisa: es el diseno.
                        ap_note("G6-ok", "%r bajo el pliegue con flecha visible"
                                % _g_label(found).split(chr(10))[0][:40])
                    elif _apg.journal_scrolls:
                        # Solo se ve girando la rueda y NADA avisa de que hay
                        # mas debajo (ni barra ni flecha).
                        ap_bug("G6-oculto", "%r (objetivo %s) solo aparece tras %d giros de rueda "
                               "en el Journal, que no muestra barra de scroll"
                               % (_g_label(found).split(chr(10))[0][:40],
                                  getattr(store, "current_objective", "?"), _apg.journal_scrolls))
                    _apg.journal_scrolls = 0
                    return found
                _g_diag_journal(rows)
                # Lo que haria una persona que espera un boton: girar la rueda.
                if _apg.journal_scrolls < 8:
                    if _apg.journal_scrolls == 0:
                        _apg.journal_arrow = _g_arrow_visible()
                    _apg.journal_scrolls += 1
                    _g_wheel_down(config.screen_width // 2, config.screen_height // 2)
                    return "ACTED"
            _apg.journal_day = (_g_today(), getattr(store, "current_objective", None))
            for row in rows:
                if row.get("screen") == "journal_panel" and _g_is_close(row):
                    return row
            return None
        if _apg.journal_day == (_g_today(), getattr(store, "current_objective", None)):
            return "DONE"
        _apg.journal_scrolls = 0
        _apg.journal_opens_on_obj += 1 if _g_at_hub(rows) else 0
        return _g_open_from_hub(rows, "Journal")

    # Botones del Journal que hacen avanzar, por orden de prioridad. Los de
    # eleccion (gambito del 9, camino del 16) son insensibles hasta cumplir el
    # requisito, y la percepcion ya descarta los insensibles.
    AP_GOAL_JOURNAL_ACTIONS = (
        "Send word through your contacts",
        "Plan the Governor's Death",
        "Heist and Blackmail",
        "Path of the Blade",
        "Path of the Shadow",
        "MARK COMPLETE - BEGIN THE FINAL STRIKE",
        "MARK AS COMPLETE",
        "MARK COMPLETE",
    )

    def _g_journal_action(rows):
        for text in AP_GOAL_JOURNAL_ACTIONS:
            if text.startswith("Path of the") and getattr(store, "vengeance_path_chosen", False):
                continue  # re-pulsarlo solo cambia de camino: bucle
            for row in rows:
                if row.get("screen") != "journal_panel":
                    continue
                label = _g_label(row)
                if label == text or label.startswith(text):
                    if text.startswith("MARK COMPLETE") and label.startswith("MARK AS"):
                        continue
                    return row
        return None

    def _g_arrow_visible():
        """La flecha de 'hay mas' del Journal (un Text de una DynamicDisplayable)."""
        try:
            raiz = renpy.get_screen("journal_panel")
            for node in _ap_walk(raiz) if raiz is not None else []:
                if type(node).__name__ == "DynamicDisplayable":
                    hijo = getattr(node, "child", None)
                    texto = getattr(hijo, "text", None)
                    if texto and u"▼" in "".join(t for t in texto if _ap_is_text(t)).lower():
                        return True
        except Exception:
            pass
        return False

    def _g_wheel_down(x, y):
        """Rueda REAL hacia abajo: el boton 5 es lo que el keymap del motor llama
        viewport_wheeldown."""
        mouse = renpy.test.testmouse
        mouse.move_mouse(x, y)
        mouse.press_mouse(5)
        mouse.release_mouse(5)
        _ap.actions += 1
        _ap.last_action = {"label": "(rueda)", "screen": "wheel"}
        ap_note("SCROLL", "rueda abajo en (%d, %d)" % (x, y))

    def _g_diag_journal(rows):
        """Una vez: el boton esperado no esta entre lo pulsable. Volcar el foco
        crudo (con lo que la percepcion descarta por salirse de pantalla) y el
        texto pintado, para distinguir 'no se pinta' de 'se pinta y no se ve'."""
        if renpy.session.get("ap_goal_journal_diag"):
            return
        renpy.session["ap_goal_journal_diag"] = True
        crudos = []
        try:
            for focus in renpy.display.focus.focus_list:
                if focus.x is None or focus.widget is None:
                    continue
                crudos.append((_ap_label_of(focus.widget)[:30], int(focus.x), int(focus.y),
                               int(focus.w), int(focus.h)))
        except Exception as e:
            crudos.append(repr(e))
        ap_shot("journal-sin-mark")
        ap_note("DIAG", "Journal sin MARK AS COMPLETE visible",
                focus_crudo=crudos, textos=[t[:80] for _s, t in ap_visible_text()][:40],
                puede=getattr(store, "can_complete_objective_8", lambda: None)())

    def _g_task_potion(rows):
        if getattr(store, "potion_used_on_worker", False):
            return "DONE"
        shown = _g_screens(rows)
        bought = getattr(store, "potion_purchased", False)
        moved = getattr(store, "potion_transferred", False)
        if not bought:
            if _g_money() < 60:
                return "WAIT"
            if "manager_inventory" in shown:
                anchor = None
                for row in rows:
                    if (row.get("screen") == "manager_inventory"
                            and _g_label(row).startswith("Energy Potion")
                            and row["x"] > config.screen_width // 2):
                        anchor = row
                        break
                if anchor is not None:
                    buy = _g_same_row(rows, anchor, "Buy")
                    if buy is not None:
                        return buy
                # No se ve en la lista: buscarla, como haria un jugador.
                if _apg.potion_search < 3:
                    search = _g_find(rows, "Search", exact=True, screen="manager_inventory")
                    if search is not None:
                        _apg.potion_search += 1
                        renpy.session["ap_next_input"] = "Energy"
                        return search
                return None
            if "shop_selection" in shown:
                return _g_find(rows, "Basic Shop", screen="shop_selection")
            if "map_screen" in shown:
                return _g_find(rows, "Visit Shops", screen="map_screen")
            return _g_open_from_hub(rows, "Explore")
        if "manager_inventory" in shown:
            side_left = [r for r in rows if r.get("screen") == "manager_inventory"
                         and r["x"] < config.screen_width // 2]
            side_right = [r for r in rows if r.get("screen") == "manager_inventory"
                          and r["x"] >= config.screen_width // 2]
            if not moved:
                anchor = _g_find(side_left, "Energy Potion", prefix=True)
                if anchor is not None:
                    move = _g_same_row(rows, anchor, "Right")
                    if move is not None:
                        return move
                # Esta abierta la tienda, no el almacen: salir y entrar por Storage.
                return _g_find(rows, "Close", exact=True, screen="manager_inventory")
            anchor = _g_find(side_right, "Energy Potion", prefix=True)
            if anchor is not None:
                use = _g_same_row(rows, anchor, "Use")
                if use is not None:
                    return use
            return _g_find(rows, "Close", exact=True, screen="manager_inventory")
        return _g_open_from_hub(rows, "Storage")

    def _g_task_upgrade(rows, building):
        if getattr(store, "building_upgraded_tutorial", False):
            return "DONE"
        if _g_money() < 1000 + AP_GOAL_RESERVE:
            return "WAIT"
        step = _g_open_manager(rows, building)
        if step != "HERE":
            return step
        return _g_find(rows, "Upgrade Building", exact=True, screen="Manager") or "WAIT"

    def _g_task_skill_bonus(rows, building):
        if getattr(store, "building_skill_bonus_increased_tutorial", False):
            if "adjust_skill_bonus" in _g_screens(rows):
                for row in rows:
                    if row.get("screen") == "adjust_skill_bonus" and _g_is_close(row):
                        return row
            return "DONE"
        if _g_money() < 300 + AP_GOAL_RESERVE:
            return "WAIT"
        shown = _g_screens(rows)
        if "adjust_skill_bonus" in shown:
            if not _apg.skill_plus_clicked:
                plus = _g_find(rows, "+", exact=True, screen="adjust_skill_bonus")
                if plus is not None:
                    _apg.skill_plus_clicked = True
                    return plus
            for row in rows:
                if row.get("screen") == "adjust_skill_bonus" and _g_is_close(row):
                    return row
            return None
        step = _g_open_manager(rows, building)
        if step != "HERE":
            return step
        for name in AP_GOAL_SKILL_BUTTON:
            found = _g_find(rows, name, exact=True, screen="Manager")
            if found is not None:
                return found
        return "WAIT"

    def _g_task_lunch(rows):
        if getattr(store, "tutorial_friendly_chat_done", False):
            return "DONE"
        if _g_money() < 150 + AP_GOAL_RESERVE // 2:
            return "WAIT"
        shown = _g_screens(rows)
        if "interaction_category" in shown:
            found = _g_find(rows, "Friendly Lunch", exact=True, screen="interaction_category")
            if found is not None and found.get("sensitive", True):
                return found
            return (_g_find(rows, "Back", exact=True, screen="interaction_category")
                    or _g_go_hub(rows))
        if "interaction_menu" in shown:
            found = _g_find(rows, "Friendship", exact=True, screen="interaction_menu")
            if found is not None:
                return found
            return _g_find(rows, "Close", exact=True, screen="interaction_menu") or _g_go_hub(rows)
        if "worker_details" in shown:
            return _g_find(rows, "Interact", exact=True, screen="worker_details") or _g_go_hub(rows)
        if "workers" in shown:
            names = [str(w.get("name") or "") for w in _g_workers()]
            for name in names:
                if not name or name in _apg.lunch_tried:
                    continue
                for row in rows:
                    if row.get("screen") != "workers":
                        continue
                    label = _g_label(row)
                    if label.startswith(name[:12]) and _g_re.search(r"\(\d+\)$", label):
                        _apg.lunch_tried.add(name)
                        return row
            return "WAIT"
        return _g_open_from_hub(rows, "Workers")

    def _g_task_buy_building(rows, target=2, kind=None):
        """Comprar un hueco del mapa. Para el 8 vale el mas barato; para el 13
        se busca un Casino (sus Guards entrenan Combat para el 14 y el 16)."""
        if len(_g_building_names()) >= target:
            return "DONE"
        shown = _g_screens(rows)
        if "buy_map_building" in shown:
            options = [r for r in rows if r.get("screen") == "buy_map_building"
                       and " - $" in _g_label(r) and r.get("sensitive", True)]
            for name in ((kind,) if kind else ()) + (AP_GOAL_BUILDING, "Tavern", "Restaurant", "Casino"):
                for row in options:
                    if _g_label(row).startswith(name + " - $"):
                        return row
            return options[0] if options else _g_go_hub(rows)
        money = _g_money()
        if "map_screen" in shown:
            colchon = 10000 if target == 2 else 0
            huecos = AP_GOAL_MAP_SLOTS
            if kind == "Casino":
                huecos = [h for h in AP_GOAL_MAP_SLOTS if "Redhouse" in h[0] or "Greenhouse" in h[0]]
            for slot, price in huecos:
                if money < price + colchon + AP_GOAL_RESERVE:
                    continue
                for row in rows:
                    if row.get("screen") == "map_screen" and (slot + "a") in _g_img(row):
                        return row
            return "WAIT"
        minimo = 25000 if kind == "Casino" else AP_GOAL_MAP_SLOTS[0][1]
        if money < minimo + (10000 if target == 2 else 0) + AP_GOAL_RESERVE:
            return "WAIT"
        return _g_open_from_hub(rows, "Explore")

    # ------------------------------------------------- TAREAS DE MEDIO JUEGO

    def _g_items_by_name():
        cache = renpy.session.get("ap_goal_items")
        if cache is None:
            cache = {}
            for item in (getattr(store, "items_json", None) or {}).get("items", []) or []:
                if hasattr(item, "get") and item.get("name"):
                    cache[item.get("name")] = item
            renpy.session["ap_goal_items"] = cache
        return cache

    def _g_owned_count(name):
        """Unidades de un objeto entre almacen y workers (lo que el jugador ve
        en sus inventarios)."""
        item = _g_items_by_name().get(name)
        if item is None:
            return 0
        iid = item.get("id")
        total = 0
        bolsas = [getattr(store, "manager_inventory", None) or []]
        bolsas += [w.get("inventory") or [] for w in _g_workers()]
        for bolsa in bolsas:
            for entry in bolsa:
                if hasattr(entry, "__getitem__") and not _ap_is_text(entry) and len(entry) >= 2:
                    if entry[0] == iid:
                        try:
                            total += int(entry[1] or 0)
                        except Exception:
                            total += 1
        return total

    def _g_shop_of(price):
        if price <= 200:
            return "Basic Shop"
        if price <= 500:
            return "Adventurer's Market"
        return "Elite Emporium"

    # Equipo que persigue cada objetivo: (nombre, copias). Por preferencia: el
    # jugador compra el primero que vea en la estanteria y pueda pagar. El
    # auto-equipo del juego reparte desde el almacen segun la profesion.
    AP_GOAL_GEAR = {
        "charm": [("Crown of Dominion", 3), ("Refined Service Dress", 3), ("The Stars' Tears", 3),
                  ("Charming Earrings", 3), ("Service Uniform", 3), ("Pearl Necklace", 3)],
        "clever": [("Tactician Monocle", 2), ("Magic Robe", 2), ("Strategist Notebook", 2)],
        "combat": [("Blade of the Fallen King", 5), ("Mithril Sword", 5), ("Silver Sword", 5),
                   ("Cloak of Shadows", 5), ("Steel Plate Armor", 5), ("Chainmail Shirt", 5),
                   ("Amulet of the Wanderer", 5), ("Warrior Gauntlets", 5), ("Amulet of Power", 5)],
        "artifacts": [("Enchanted Ring", 1), ("Obsidian Blade", 1)],
    }

    def _g_spend_floor():
        """Dinero por debajo del cual no se compra equipo: depende de para que
        se esta ahorrando ahora mismo."""
        obj = getattr(store, "current_objective", 1) or 1
        if obj >= 14:
            # El mejor arma de Combat cuesta 12.000: con un suelo bajo se compra
            # siempre la barata y nunca se llega a ahorrar para la buena.
            return 1500
        if obj == 10:
            return 30000 + AP_GOAL_RESERVE
        if obj == 13 and len(_g_building_names()) < 3:
            return 25000 + AP_GOAL_RESERVE
        return 2500

    def _g_item_bonus(item, skill):
        mods = item.get("skill_modifiers") or (item.get("effect") or {}).get("skill_modifiers") or {}
        try:
            return int(mods.get(skill, 0) or 0) if hasattr(mods, "get") else 0
        except Exception:
            return 0

    def _g_gear_ranking(skill):
        """(hueco, [(bonus, nombre, precio)] de mejor a peor) para una habilidad.
        Lo que un jugador sabria leyendo las descripciones de la tienda."""
        clave = "ap_goal_rank_" + skill
        cache = renpy.session.get(clave)
        if cache is not None:
            return cache
        por_hueco = {}
        for item in _g_items_by_name().values():
            iid = str(item.get("id") or "").lower()
            if "test" in iid or "debug" in iid or not item.get("shop_available", True):
                continue
            hueco = item.get("type")
            if hueco not in ("weapon", "armor", "accessory", "clothing"):
                continue
            bonus = _g_item_bonus(item, skill)
            if bonus < 3:
                continue
            por_hueco.setdefault(hueco, []).append(
                (bonus, item.get("name"), int(item.get("price", 0) or 0)))
        for hueco in por_hueco:
            por_hueco[hueco].sort(key=lambda t: (-t[0], t[2]))
        renpy.session[clave] = por_hueco
        return por_hueco

    def _g_gear_wants(skill, copies):
        """Para cada hueco: los objetos que mejorarian lo que ya hay. Se quiere
        uno mientras haya menos de `copies` unidades de ese nivel o mejores."""
        wants = []
        for hueco, ranking in _g_gear_ranking(skill).items():
            for bonus, name, price in ranking:
                tengo = sum(_g_owned_count(n) for b, n, _p in ranking if b >= bonus)
                if tengo < copies:
                    wants.append((bonus, name, price))
        wants.sort(key=lambda t: -t[0])
        return wants

    def _g_count_at(skill, threshold):
        calc = getattr(store, "calculate_skill_with_traits", None)
        if not callable(calc):
            return 0
        n = 0
        for w in _g_workers():
            try:
                if int(calc(w, skill)) >= threshold:
                    n += 1
            except Exception:
                pass
        return n

    def _g_skill_needs(obj):
        """Que habilidad pide el objetivo actual y aun no se cumple, con los
        valores efectivos que mira el juego. Gastar en lo ya cumplido dejo el
        objetivo 14 sin dinero para Combat durante 49 dias."""
        needs = []
        if obj == 9 and _g_count_at("Charm", 70) < 3 and _g_count_at("Combat", 70) < 3:
            needs.append(("Charm", 3))
        if obj == 14:
            if _g_count_at("Combat", 80) < 3:
                needs.append(("Combat", 5))
            if max(_g_count_at("Charm", 80), _g_count_at("Clever", 80)) < 2:
                needs.append(("Charm", 3))
        if obj == 16 and _g_count_at("Combat", 70) < 5 and _g_count_at("Clever", 70) < 5:
            needs.append(("Combat", 5))
        return needs

    def _g_wishlist():
        obj = getattr(store, "current_objective", 1) or 1
        floor = _g_spend_floor()
        money = _g_money()
        salida = []
        if obj >= 11:
            for name, _c in AP_GOAL_GEAR["artifacts"]:
                item = _g_items_by_name().get(name)
                if item is not None and _g_owned_count(name) < 1:
                    price = int(item.get("price", 0) or 0)
                    if money - price >= 1000:
                        salida.append((name, _g_shop_of(price)))
        objetivos = _g_skill_needs(obj)
        for skill, copies in objetivos:
            for _bonus, name, price in _g_gear_wants(skill, copies):
                if money - price < floor:
                    continue
                salida.append((name, _g_shop_of(price)))
        return salida

    def _g_shelf_match(label, name):
        """La tienda recorta los nombres largos con '...' ("Dragon Scale Gaun...:
        $4600"): comparar contra el prefijo visible, no el nombre entero."""
        shown = label.split(": $", 1)[0].strip()
        if shown == name:
            return True
        for cut in (chr(0x2026), "..."):
            if shown.endswith(cut):
                prefix = shown[:-len(cut)].rstrip()
                return len(prefix) >= 6 and name.startswith(prefix)
        return False

    def _g_task_gear(rows):
        """Comprar lo de la lista: entrar en la tienda, girar la rueda hasta
        verlo y pulsar el Buy de su fila. Una visita por tienda y dia."""
        wanted = _g_wishlist()
        shown = _g_screens(rows)
        if "manager_inventory" in shown and _apg.shop_open:
            nombres = [n for n, shop in wanted if shop == _apg.shop_open]
            for row in rows:
                if row.get("screen") != "manager_inventory" or row["x"] < config.screen_width // 2:
                    continue
                label = _g_label(row)
                for name in nombres:
                    if _g_shelf_match(label, name):
                        buy = _g_same_row(rows, row, "Buy")
                        if buy is not None:
                            ap_note("DECIDE", "comprar %s en %s ($%d)" % (name, _apg.shop_open, _g_money()))
                            _apg.shop_scrolls = 0
                            return buy
            vistos = renpy.session.setdefault("ap_goal_shop_diag", {})
            etiquetas = [_g_label(r)[:40] for r in rows if r.get("screen") == "manager_inventory"
                         and r["x"] >= config.screen_width // 2 and ":" in _g_label(r)]
            ya = vistos.setdefault(_apg.shop_open, [])
            nuevas = [e for e in etiquetas if e not in ya]
            if nuevas and len(ya) < 200:
                ya.extend(nuevas)
                ap_note("SHELF", "%s: %s" % (_apg.shop_open, nuevas), buscando=nombres)
            # Fin de la lista: tres giros seguidos sin ninguna fila nueva.
            if nuevas:
                _apg.shop_stale = 0
            else:
                _apg.shop_stale += 1
            if nombres and _apg.shop_scrolls < 150 and _apg.shop_stale < 3:
                _apg.shop_scrolls += 1
                # Girar ENCIMA de la lista, no en un punto fijo: la rueda solo
                # mueve el viewport que esta bajo el puntero.
                filas = [r for r in rows if r.get("screen") == "manager_inventory"
                         and r["x"] >= config.screen_width // 2 and ": $" in _g_label(r)]
                if filas:
                    x = filas[0]["x"] + filas[0]["w"] // 2
                    y = (min(r["y"] for r in filas) + max(r["y"] + r["h"] for r in filas)) // 2
                else:
                    x, y = int(config.screen_width * 0.72), int(config.screen_height * 0.6)
                _g_wheel_down(x, y)
                return "ACTED"
            _apg.shops_done.add((_g_today(), _apg.shop_open))
            _apg.shop_open = None
            return _g_find(rows, "Close", exact=True, screen="manager_inventory") or _g_go_hub(rows)
        pendientes = [shop for _n, shop in wanted if (_g_today(), shop) not in _apg.shops_done]
        if not pendientes:
            return "DONE"
        shop = pendientes[0]
        if "shop_selection" in shown:
            found = _g_find(rows, shop, exact=True, screen="shop_selection")
            if found is None:
                # Tienda cerrada todavia: no insistir hoy.
                _apg.shops_done.add((_g_today(), shop))
                return _g_go_hub(rows)
            _apg.shop_open = shop
            _apg.shop_scrolls = 0
            _apg.shop_stale = 0
            renpy.session.setdefault("ap_goal_shop_diag", {})[shop] = []
            return found
        if "map_screen" in shown:
            return _g_find(rows, "Visit Shops", screen="map_screen") or "WAIT"
        return _g_open_from_hub(rows, "Explore")

    def _g_points_left():
        keys = ["business_acumen", "combat_instruction", "servant_training", "gang_leader"]
        if getattr(persistent, "nsfw_enabled", False):
            keys.append("whore_mastery")
        skills = getattr(store, "management_skills", None) or {}
        spent = sum(int(skills.get(k, 0) or 0) for k in keys)
        return int(getattr(store, "manager_level", 1) or 1) - spent

    def _g_task_points(rows):
        """Puntos de manager sin gastar -> Combat Instruction (+5 Combat a TODOS)."""
        if not getattr(store, "manager_start_skill_chosen", False) or _g_points_left() <= 0:
            if "manager_character_sheet" in _g_screens(rows):
                return _g_go_hub(rows)
            return "DONE"
        shown = _g_screens(rows)
        if "manager_character_sheet" in shown:
            confirm = _g_find(rows, "Confirm", exact=True, screen="manager_character_sheet")
            if confirm is not None:
                return confirm
            pluses = sorted([r for r in rows if r.get("screen") == "manager_character_sheet"
                             and _g_label(r) == "+"], key=lambda r: r["y"])
            orden = ["business_acumen"]
            if getattr(persistent, "nsfw_enabled", False):
                orden.append("whore_mastery")
            orden += ["combat_instruction", "servant_training", "gang_leader"]
            i = orden.index("combat_instruction")
            if len(pluses) == len(orden):
                return pluses[i]
            return pluses[0] if pluses else None
        name = ("%s %s" % (getattr(store, "player_title", ""),
                           getattr(store, "player_name", ""))).strip()
        return _g_open_from_hub(rows, name)

    def _g_task_auto_equip(rows):
        """Encender 'Auto Equip' en cada worker: el juego reparte el equipo del
        almacen segun la profesion. Uno por pasada, desde la plantilla."""
        if _apg.equip_day != _g_today():
            _apg.equip_day = _g_today()
            _apg.equip_tried = set()
            _apg.equip_scrolls = 0
        # Solo los que trabajan: el auto-equipo reparte segun la profesion.
        pendientes = [w for w in _g_workers() if not w.get("auto_equip", False)
                      and (w.get("assigned_building") or "Unassigned") != "Unassigned"
                      and str(w.get("name") or "") not in _apg.equip_tried]
        shown = _g_screens(rows)
        # Primero la ficha ya abierta del que se busca: al abrirla se marca como
        # intentado, y si era el ULTIMO pendiente la tarea se daba por hecha
        # justo antes de pulsar el interruptor (le paso a Talon 22 dias).
        if "worker_details" in shown and _apg.equip_target:
            toggle = _g_find(rows, "Auto Equip: Off", exact=True, screen="worker_details")
            _apg.equip_target = None
            if toggle is not None:
                return toggle
            return _g_go_hub(rows)
        if not pendientes:
            return "DONE"
        if "worker_details" in shown:
            return _g_go_hub(rows)
        if "workers" in shown:
            for w in pendientes:
                name = str(w.get("name") or "")
                for row in rows:
                    if row.get("screen") != "workers":
                        continue
                    label = _g_label(row)
                    if label.startswith(name[:12]) and _g_re.search(r"\(\d+\)$", label):
                        _apg.equip_tried.add(name)
                        _apg.equip_target = name
                        return row
            # No esta en la parte visible de la lista: bajar, como una persona.
            # Clave por worker buscado: al reabrir, la lista vuelve arriba y lo
            # ya visto en otra busqueda no debe contar como "nada nuevo".
            if _g_roster_more(rows, ("equip", _g_today(), str(pendientes[0].get("name")))):
                return "ACTED"
            for w in pendientes:
                _apg.equip_tried.add(str(w.get("name") or ""))
            return _g_go_hub(rows)
        return _g_open_from_hub(rows, "Workers")

    def _g_building(name):
        edificios = getattr(store, "available_buildings", None) or {}
        b = edificios.get(name) if hasattr(edificios, "get") else None
        return b if hasattr(b, "get") else {}

    def _g_task_upgrade_to(rows, building, level):
        """Subir un edificio de nivel: mas plazas por profesion (+1 por nivel)."""
        b = _g_building(building)
        # El precio sale de base_level (get_building_upgrade_cost), no de
        # "level": leer el otro llevo a un bucle Yes -> "no tienes dinero".
        actual = int(b.get("base_level", b.get("level", 1)) or 1)
        if actual >= level:
            return "DONE"
        coste = actual * actual * 1000
        if _g_money() < coste + 3000:
            return "WAIT"
        step = _g_open_manager(rows, building)
        if step != "HERE":
            return step
        return _g_find(rows, "Upgrade Building", exact=True, screen="Manager") or "WAIT"

    def _g_roster_more(rows, key):
        """Seguir girando mientras aparezcan filas nuevas. La plantilla baja
        ~1 fila por giro: cortar en 12 giros dejo sin ver al worker 16."""
        vistos = _apg.list_seen.setdefault(key, set())
        nombres = set(_g_label(r) for r in rows if r.get("screen") == "workers"
                      and _g_re.search(r"\(\d+\)$", _g_label(r)))
        nuevos = nombres - vistos
        vistos.update(nombres)
        racha = _apg.list_stale.get(key, 0)
        racha = 0 if nuevos else racha + 1
        _apg.list_stale[key] = racha
        giros = _apg.list_turns.get(key, 0)
        if racha >= 3 or giros >= 80:
            _apg.list_seen.pop(key, None)
            _apg.list_stale.pop(key, None)
            _apg.list_turns.pop(key, None)
            return False
        _apg.list_turns[key] = giros + 1
        _g_wheel_list(rows, "workers")
        return True

    def _g_wheel_list(rows, screen):
        """Girar la rueda encima de las filas visibles de una lista."""
        filas = [r for r in rows if r.get("screen") == screen and _g_label(r)
                 and _g_re.search(r"\(\d+\)$", _g_label(r))]
        if filas:
            x = min(r["x"] for r in filas) + 40
            y = (min(r["y"] for r in filas) + max(r["y"] + r["h"] for r in filas)) // 2
        else:
            x, y = config.screen_width // 2, int(config.screen_height * 0.6)
        _g_wheel_down(x, y)

    def _g_casino():
        for b in _g_building_names():
            if str(_g_building(b).get("type") or "").lower() == "casino":
                return b
        return None

    def _g_job_cell(rows, name):
        """En la fila del roster de `name`: la celda de trabajo (la segunda
        celda de texto tras el nombre; la primera es el edificio)."""
        anchor = None
        for row in rows:
            if row.get("screen") != "workers":
                continue
            label = _g_label(row)
            if label.startswith(name[:12]) and _g_re.search(r"\(\d+\)$", label):
                if anchor is None or row["x"] < anchor["x"]:
                    anchor = row
        if anchor is None:
            return None
        ay = anchor["y"] + anchor["h"] // 2
        same = [r for r in rows if r.get("screen") == "workers" and r is not anchor
                and abs(r["y"] + r["h"] // 2 - ay) <= anchor["h"] // 2 + 4
                and r["x"] > anchor["x"] and _g_label(r)]
        same.sort(key=lambda r: r["x"])
        return same[1] if len(same) >= 2 else None

    def _g_task_staff_casino(rows):
        """Mover a los mejores en Combat al Casino como Guard. El auto-relleno
        solo usa workers SIN asignar: con toda la plantilla en las tabernas,
        el Casino se quedo vacio y el equipo de Combat sin nadie que lo usara."""
        casino = _g_casino()
        if casino is None:
            return "DONE"
        if _apg.staff_day != _g_today():
            _apg.staff_day = _g_today()
            _apg.staff_failed = set()
            _apg.staff_scrolls = 0
        b = _g_building(casino)
        jobs = b.get("servant_jobs") or {}
        plazas = min(5, 3 + int(b.get("base_level", 1) or 1) - 1)
        def combat(w):
            sk = w.get("skills") or {}
            try:
                return int(sk.get("Combat", 0) or 0) if hasattr(sk, "get") else 0
            except Exception:
                return 0
        ranking = sorted(_g_workers(), key=combat, reverse=True)[:plazas]
        pendientes = [w for w in ranking
                      if str(jobs.get(str(w.get("name")), "")).lower() != "guard"
                      and str(w.get("name")) not in _apg.staff_failed]
        shown = _g_screens(rows)
        if not pendientes:
            return "DONE"
        w = pendientes[0]
        name = str(w.get("name"))
        if "building_selection" in shown:
            for row in rows:
                if row.get("screen") == "building_selection" and _g_label(row).startswith("Casino:"):
                    return row
            return _g_go_hub(rows)
        if "job_selection" in shown:
            if (w.get("assigned_building") or "") == casino:
                found = _g_find(rows, "Guard", exact=True, screen="job_selection")
                if found is not None:
                    ap_note("DECIDE", "%s (Combat %d) pasa a Guard del Casino" % (name, combat(w)))
                    return found
                # Plazas llenas o rol no visible: no insistir con este worker.
                _apg.staff_failed.add(name)
                return _g_go_hub(rows)
            return _g_find(rows, "Change building", exact=True, screen="job_selection") or _g_go_hub(rows)
        if "workers" in shown:
            cell = _g_job_cell(rows, name)
            if cell is not None:
                _apg.staff_scrolls = 0
                return cell
            if _g_roster_more(rows, ("staff", _g_today(), name)):
                return "ACTED"
            _apg.staff_failed.add(name)
            _apg.staff_scrolls = 0
            return _g_go_hub(rows)
        return _g_open_from_hub(rows, "Workers")

    def _g_task_next_day(rows):
        if _g_at_hub(rows):
            row = _g_find(rows, "Next Day", exact=True, screen="tavern")
            if row is not None:
                # Lo que tenia ANTES de procesar el dia: el neto del dia es la
                # diferencia con el primer tick del dia siguiente, sin mezclar
                # las compras del propio jugador.
                _apg.money_pre_advance = _g_money()
            return row
        return _g_go_hub(rows)


    # =============================================================== END GAME
    #
    # Tras el golpe final el jugador no para: invierte y mide. Cada semana como
    # mucho prueba UNA inversion nueva (experimento) y compara el neto medio de
    # los 7 dias anteriores con el de los 7 siguientes. Ademas de buscar dinero,
    # esto recorre Arena, Academia, laboratorio, franquicias, iglesia y tipos de
    # edificio que el tramo de objetivos no toca.

    AP_GOAL_ENDGAME = bool(_g_os.environ.get("FM_GOAL_ENDGAME"))
    AP_GOAL_ENDGAME_DAYS = int(_g_os.environ.get("FM_GOAL_ENDGAME_DAYS") or 120)
    AP_GOAL_EXPERIMENT_GAP = 7

    def _g_endgame_active():
        return AP_GOAL_ENDGAME and bool(getattr(store, "objective_16_complete", False))

    def _g_seats_total():
        """Plazas de trabajo de todos los edificios propios (sin Rest)."""
        fn = getattr(store, "get_max_daily_workers", None)
        tipos = {}
        for bt in (getattr(store, "building_types_json", None) or {}).get("building_types", []) or []:
            tipos[bt.get("id")] = bt
        total = 0
        for name in _g_owned():
            b = _g_building(name)
            bt = tipos.get(b.get("type"))
            if not bt or not callable(fn):
                continue
            for prof in bt.get("professions") or []:
                if prof.get("id") == "rest":
                    continue
                if prof.get("nsfw") and not getattr(persistent, "nsfw_enabled", False):
                    continue
                try:
                    total += int(fn(b, prof))
                except Exception:
                    pass
        return total

    def _g_net_avg(desde, hasta):
        vals = [n for d, n in _apg.net_by_day if desde <= d < hasta]
        return (sum(vals) / float(len(vals))) if vals else None

    def _g_experiment_log(name, coste):
        dia = _apg.days_played
        _apg.experiments.append({"name": name, "day": dia, "cost": coste,
                                 "net_before": _g_net_avg(dia - 7, dia)})
        ap_note("EXPERIMENT", "empieza %s el dia %d (coste %s, neto medio previo %s)"
                % (name, dia, coste, _apg.experiments[-1]["net_before"]))

    def _g_experiment_close():
        """Rellenar el neto posterior de los experimentos con 7 dias cumplidos."""
        for e in _apg.experiments:
            if e.get("net_after") is None and _apg.days_played >= e["day"] + 8:
                e["net_after"] = _g_net_avg(e["day"] + 1, e["day"] + 8)
                antes, despues = e.get("net_before"), e.get("net_after")
                if antes is not None and despues is not None:
                    e["delta"] = round(despues - antes, 1)
                    pago = (float(e["cost"]) / e["delta"]) if e["delta"] > 0 and e["cost"] else None
                    e["payback_days"] = round(pago, 1) if pago else None
                ap_note("EXPERIMENT", "resultado %s: neto %s -> %s al dia (delta %s, se paga en %s dias)"
                        % (e["name"], antes, despues, e.get("delta"), e.get("payback_days")))

    # --- elecciones guiadas -----------------------------------------------
    # Lo que el jugador quiere contestar en los menus de las mecanicas nuevas.
    AP_GOAL_CHOICE_PREFS = (
        "Pay the tuition", "Buy the Arena permit", "Pay the alchemist pass",
        "Batch basic",
    )
    # Iglesia: UNA eleccion de exploracion por visita (cada una da un sello en
    # su dia) y luego irse. Elegirlas todas seguidas metio al jugador en un
    # bucle "Visit the cemetery." -> lista de tumbas -> volver.
    AP_GOAL_CHURCH_PREFS = ("Study the Circle ritual.", "Visit the priestess's room.",
                            "Stay for evening prayer.", "Visit the cemetery.")
    AP_GOAL_RITUAL = ("Stone.", "Water.", "Wind.", "Flame.")

    def _g_round_answer(rows, screen):
        """Rondas de combate especial y de alquimia: la pista del narrador
        indica una unica respuesta correcta. El jugador que ya ha jugado la
        conoce; aqui se lee la misma tabla que usa el juego."""
        textos = " ".join(t for _s, t in ap_visible_text()) + " " + (renpy.session.get("ap_last_say") or "")
        opciones = [r for r in rows if r.get("screen") == screen and _g_label(r)]
        etiquetas = [_g_label(r) for r in opciones]
        tablas = []
        if any(e.startswith("They're") for e in etiquetas):
            tablas.append((getattr(store, "SPECIAL_MATCH_STYLES", None),
                           {"attack": "They're attacking!", "defend": "They're defending!",
                            "feint": "They're feinting!"}))
        if any(e in ("Raise the heat.", "Keep the temperature steady.", "Lower the heat.") for e in etiquetas):
            tablas.append((getattr(store, "ALCHEMY_ROUND_STYLES", None),
                           {"heat_up": "Raise the heat.", "maintain": "Keep the temperature steady.",
                            "heat_down": "Lower the heat."}))
        for tabla, nombres in tablas:
            for estilo in (tabla or []):
                if not hasattr(estilo, "get"):
                    continue
                for n in (1, 2):
                    pista = estilo.get("hint%d" % n) or ""
                    accion = estilo.get("round%d" % n)
                    if pista and pista in textos and accion in nombres:
                        objetivo = nombres[accion]
                        for r in opciones:
                            if _g_label(r) == objetivo:
                                ap_note("DECIDE", "ronda: pista %r -> %r" % (pista[:40], objetivo))
                                return r
        return None

    def _g_choice_pref(rows, screen):
        opciones = [r for r in rows if r.get("screen") == screen and _g_label(r)]
        etiquetas = [_g_label(r) for r in opciones]
        # Ritual de los sellos: en orden.
        if all(any(e == x for e in etiquetas) for x in AP_GOAL_RITUAL):
            paso = AP_GOAL_RITUAL[_apg.ritual_idx % 4]
            _apg.ritual_idx += 1
            for r in opciones:
                if _g_label(r) == paso:
                    return r
        # Menu de la sacerdotisa (tiene "Leave."): una eleccion por dia.
        if "Leave." in etiquetas and any(e in AP_GOAL_CHURCH_PREFS for e in etiquetas):
            if _apg.church_pref_day == _g_today():
                for r in opciones:
                    if _g_label(r) == "Leave.":
                        return r
            for pref in AP_GOAL_CHURCH_PREFS:
                for r in opciones:
                    if _g_label(r) == pref:
                        _apg.church_pref_day = _g_today()
                        _apg.ritual_idx = 0
                        return r
        for pref in AP_GOAL_CHOICE_PREFS:
            for r in opciones:
                if _g_label(r).startswith(pref):
                    return r
        return None

    # --- oraculos de mecanicas (casos reales de Discord) -------------------

    def _g_oracle_alchemy():
        """G10: 'yields 15 Health Potion, 15 Energy Potion' tiene que entrar en
        el almacen (caso real: decia 15 + 15 y anadia 1)."""
        if _apg.alchemy_before is None:
            return
        # El mensaje es una linea de dialogo: cuando el oraculo corre (ticks sin
        # dialogo) ya no esta en pantalla; se usa la ultima linea leida.
        texto = " ".join(t for _s, t in ap_visible_text()) + " " + (renpy.session.get("ap_last_say") or "")
        if "The batch is lost" in texto:
            _apg.alchemy_before = None
            ap_note("G10-ok", "lote fallido: nada que comprobar")
            return
        m = _g_re.search(r"yields (.+?)\.", texto)
        if not m:
            return
        antes = _apg.alchemy_before
        _apg.alchemy_before = None
        for parte in m.group(1).split(", "):
            mm = _g_re.match(r"(\d+) (.+)", parte.strip())
            cantidad, nombre = (int(mm.group(1)), mm.group(2)) if mm else (1, parte.strip())
            ahora = _g_owned_count(nombre)
            if ahora - antes.get(nombre, 0) != cantidad:
                ap_bug("G10-alquimia", "el laboratorio dice %d %s y el inventario cambia en %d"
                       % (cantidad, nombre, ahora - antes.get(nombre, 0)))
            else:
                ap_note("G10-ok", "laboratorio: %d %s cuadra con el inventario" % (cantidad, nombre))

    def _g_oracle_reputation_text():
        """G11: una opcion que promete 'Gain: Reputation' no puede mostrar una
        perdida de reputacion (caso real: -90 al estar en el tope)."""
        if not _apg.last_choice_gain_rep:
            return
        texto = " ".join(t for _s, t in ap_visible_text())
        m = _g_re.search(r"(-\d+) Reputation", texto)
        if m:
            _apg.last_choice_gain_rep = False
            ap_bug("G11-reputacion", "la opcion %r prometia ganar reputacion y el resultado dice %s Reputation"
                   % (_apg.last_choice_label[:60], m.group(1)))

    def _g_oracle_franchise_jobs():
        """G12: un worker en la franquicia no puede tener puesto en un edificio
        (sospecha del analisis: el auto-relleno no comprueba la franquicia)."""
        fn = getattr(store, "worker_is_in_franchise", None)
        if not callable(fn):
            return
        for w in _g_workers():
            try:
                fuera = fn(w)
            except Exception:
                fuera = False
            if not fuera:
                continue
            nombre = str(w.get("name"))
            for b in _g_owned():
                jobs = _g_building(b).get("servant_jobs") or {}
                if nombre in jobs and str(jobs.get(nombre)).lower() not in ("", "unassigned"):
                    ap_bug("G12-franquicia", "%s esta en la franquicia y tiene puesto %r en %s"
                           % (nombre, jobs.get(nombre), b))

    # --- tareas del end game ------------------------------------------------

    def _g_task_fill_seats(rows):
        """Plantilla para las plazas: contratar. Un edificio vacio paga su
        mantenimiento igual (edificio 2: 700/dia sin ingresar nada durante 28
        dias), asi que esto va ANTES que cualquier experimento."""
        if len(_g_workers()) >= _g_seats_total() + 2:
            return "DONE"
        if _g_money() < 3000:
            return "WAIT"
        return _g_task_buy_servants(rows, _g_seats_total() + 2)

    def _g_task_upgrade_cheapest(rows):
        # Un experimento = UN nivel: al subir, se cierra y se mide.
        if _apg.exp_current and _apg.exp_current[0] == "upgrade":
            _t, b0, n0 = _apg.exp_current
            if int(_g_building(b0).get("base_level", 1) or 1) > n0:
                _apg.exp_current = None
                return "DONE"
        candidatos = []
        for b in _g_building_names():
            nivel = int(_g_building(b).get("base_level", 1) or 1)
            if nivel < 5:
                candidatos.append((nivel * nivel * 1000, b, nivel))
        if not candidatos:
            return "DONE"
        candidatos.sort()
        coste, b, nivel = candidatos[0]
        if _g_money() < coste + 8000:
            return "WAIT"
        if _apg.exp_current != ("upgrade", b, nivel):
            _apg.exp_current = ("upgrade", b, nivel)
            _g_experiment_log("upgrade %s a nivel %d" % (b, nivel + 1), coste)
        return _g_task_upgrade_to(rows, b, nivel + 1)

    def _g_task_franchise(rows):
        """Establecer la primera franquicia y mandar 3 workers."""
        staff = [w for w in _g_workers() if callable(getattr(store, "worker_is_in_franchise", None))
                 and store.worker_is_in_franchise(w)]
        if len(staff) >= 3:
            return "DONE"
        if _g_money() < 15000 and not _apg.franchise_open:
            return "WAIT"
        shown = _g_screens(rows)
        if "choose_worker_for_franchise" in shown:
            sends = [r for r in rows if r.get("screen") == "choose_worker_for_franchise"
                     and _g_label(r) == "Send"]
            if sends:
                _apg.confirm_yes = True
                return sends[0]
            return _g_go_hub(rows)
        if "franchise_detail" in shown:
            return _g_find(rows, "Assign worker", screen="franchise_detail") or _g_go_hub(rows)
        if "franchise_holdings" in shown:
            manage = _g_find(rows, "Manage", exact=True, screen="franchise_holdings")
            if manage is not None:
                return manage
            est = _g_find(rows, "Establish", exact=True, screen="franchise_holdings")
            if est is not None:
                if not _apg.franchise_open:
                    _apg.franchise_open = True
                    _g_experiment_log("franquicia", 10000)
                _apg.confirm_yes = True
                return est
            return _g_go_hub(rows)
        if "map_screen" in shown:
            return _g_find(rows, "Buy Buildings Abroad", screen="map_screen") or "WAIT"
        return _g_open_from_hub(rows, "Explore")

    def _g_task_arena(rows):
        """Permiso, prueba inicial y luchadores (los 3 mejores en Combat que no
        sean Guards del Casino)."""
        if not getattr(store, "arena_lanista_paid", False) and _g_money() < 14000 and not _apg.arena_started:
            return "WAIT"
        b = _g_building("Arena")
        jobs = b.get("servant_jobs") or {}
        # Los ids son arena_proving, arena_exhibition...: "fighter" es solo el
        # nombre visible (buscarlo en el id repetia la asignacion sin fin).
        luchadores = [n for n, j in jobs.items() if str(j).lower().startswith("arena_")]
        shown = _g_screens(rows)
        trial_ok = callable(getattr(store, "arena_operations_are_unlocked", None)) and store.arena_operations_are_unlocked()
        if trial_ok and len(luchadores) >= 3:
            return "DONE"
        if "choose_worker_for_arena_trial" in shown:
            mejor, valor = None, -1
            for r in rows:
                m = _g_re.search(r"\(Combat: (\d+)\)", _g_label(r))
                if r.get("screen") == "choose_worker_for_arena_trial" and m and int(m.group(1)) > valor:
                    mejor, valor = r, int(m.group(1))
            return mejor or _g_go_hub(rows)
        if "arena_menu" in shown:
            if not trial_ok:
                return _g_find(rows, "Hold the opening trial", screen="arena_menu") or _g_go_hub(rows)
            return _g_go_hub(rows)
        if trial_ok:
            # Gente nueva para la Arena antes de mover a nadie.
            if len(_g_workers()) < _g_seats_total() + 3 and _g_money() >= 3000:
                fila = _g_task_buy_servants(rows, _g_seats_total() + 3)
                if fila not in ("DONE", "WAIT"):
                    return fila
            return _g_task_staff_arena(rows)
        if "map_screen" in shown:
            if not _apg.arena_started:
                _apg.arena_started = True
                _g_experiment_log("arena", 10000)
            return _g_find(rows, "Arena", exact=True, screen="map_screen") or "WAIT"
        return _g_open_from_hub(rows, "Explore")

    def _g_task_staff_arena(rows):
        """Mover 3 luchadores a la Arena, igual que al Casino."""
        b = _g_building("Arena")
        jobs = b.get("servant_jobs") or {}
        casino = _g_casino()
        guardias = set((_g_building(casino).get("servant_jobs") or {}).keys()) if casino else set()
        def combat(w):
            sk = w.get("skills") or {}
            return int(sk.get("Combat", 0) or 0) if hasattr(sk, "get") else 0
        # Nunca sacar a nadie de un puesto ESENCIAL (si queda vacio, el edificio
        # entero cobra la mitad: asi se hundio el neto de +1.400 a -190 al dia).
        esenciales = ("bartender", "cook", "dealer", "adventurer", "prostitute", "manager")
        def puesto(w):
            b = w.get("assigned_building") or "Unassigned"
            return str((_g_building(b).get("servant_jobs") or {}).get(str(w.get("name")), "")).lower()
        candidatos = [w for w in sorted(_g_workers(), key=combat, reverse=True)
                      if str(w.get("name")) not in guardias
                      and puesto(w) not in esenciales
                      and not (callable(getattr(store, "worker_is_in_franchise", None))
                               and store.worker_is_in_franchise(w))][:3]
        pend = [w for w in candidatos if not str(jobs.get(str(w.get("name")), "")).lower().startswith("arena_")
                and str(w.get("name")) not in _apg.staff_failed]
        if not pend:
            return "DONE"
        w = pend[0]
        name = str(w.get("name"))
        shown = _g_screens(rows)
        if "building_selection" in shown:
            for row in rows:
                if row.get("screen") == "building_selection" and _g_label(row) == "Arena: Arena":
                    return row
            _apg.staff_failed.add(name)
            return _g_go_hub(rows)
        if "job_selection" in shown:
            if (w.get("assigned_building") or "") == "Arena":
                for rol in ("Championship fighter", "Proving fighter", "Exhibition fighter"):
                    found = _g_find(rows, rol, exact=True, screen="job_selection")
                    if found is not None:
                        ap_note("DECIDE", "%s (Combat %d) a la Arena como %s" % (name, combat(w), rol))
                        return found
                _apg.staff_failed.add(name)
                return _g_go_hub(rows)
            return _g_find(rows, "Change building", exact=True, screen="job_selection") or _g_go_hub(rows)
        if "workers" in shown:
            cell = _g_job_cell(rows, name)
            if cell is not None:
                return cell
            if _g_roster_more(rows, ("arena", _g_today(), name)):
                return "ACTED"
            _apg.staff_failed.add(name)
            return _g_go_hub(rows)
        return _g_open_from_hub(rows, "Workers")

    def _g_task_special_match(rows):
        """Combate especial semanal ($5.000): con la pista bien leida, el premio
        es 5.000 x victorias."""
        ops = callable(getattr(store, "arena_operations_are_unlocked", None)) and store.arena_operations_are_unlocked()
        shown = _g_screens(rows)
        # Ya pagado y con el selector abierto: terminar. Mirar aqui el dinero
        # (ya descontado) cedia el turno, otra tarea cerraba el selector, el
        # juego devolvia los 5.000 y se repetia cada dia.
        en_flujo = "choose_worker_for_arena_special_match" in shown
        if not en_flujo:
            if not ops or _g_money() < 15000:
                return "WAIT"
            if _apg.special_day is not None and _apg.days_played - _apg.special_day < 7:
                return "DONE"
        if "choose_worker_for_arena_special_match" in shown:
            mejor, valor = None, -1
            for r in rows:
                m = _g_re.search(r"\(Combat: (\d+)\)", _g_label(r))
                if r.get("screen") == "choose_worker_for_arena_special_match" and m and int(m.group(1)) > valor:
                    mejor, valor = r, int(m.group(1))
            if mejor is not None:
                _apg.special_day = _apg.days_played
                _g_experiment_log("combate especial", 5000)
            return mejor or _g_go_hub(rows)
        if "arena_menu" in shown:
            return _g_find(rows, "Buy special match", screen="arena_menu") or _g_go_hub(rows)
        if "map_screen" in shown:
            return _g_find(rows, "Arena", exact=True, screen="map_screen") or "WAIT"
        return _g_open_from_hub(rows, "Explore")

    # Tipos de edificio a probar y huecos donde se pueden poner.
    AP_GOAL_TYPE_SLOTS = (
        ("Restaurant", ("Bluehouse", "Tavern")),
        ("Adventurer's Guild", ("Greenhouse",)),
        ("Brothel", ("Redhouse", "Tavern")),
        ("Casino", ("Redhouse", "Greenhouse")),
        ("Tavern", ("Tavern", "Bluehouse")),
    )

    def _g_owned_types():
        return set(str(_g_building(b).get("type") or "").lower() for b in _g_building_names())

    def _g_task_new_type(rows):
        """Comprar un tipo de edificio que aun no tengo (en un hueco valido)."""
        tipos = _g_owned_types()
        objetivo = None
        for nombre, huecos in AP_GOAL_TYPE_SLOTS:
            clave = nombre.lower().replace("'", "").replace(" ", "_")
            if clave.startswith("adventurer"):
                clave = "adventurers_guild"
            if nombre == "Brothel" and not getattr(persistent, "nsfw_enabled", False):
                continue
            if clave not in tipos and nombre not in _apg.types_failed:
                objetivo = (nombre, huecos)
                break
        if objetivo is None:
            return "DONE"
        nombre, huecos = objetivo
        precios = [p for slot, p in AP_GOAL_MAP_SLOTS if any(h in slot for h in huecos)]
        if not precios or _g_money() < min(precios) + 10000:
            return "WAIT"
        shown = _g_screens(rows)
        if "buy_map_building" in shown:
            for r in rows:
                if r.get("screen") == "buy_map_building" and _g_label(r).startswith(nombre + " - $"):
                    _g_experiment_log("edificio %s" % nombre, min(precios))
                    return r
            _apg.types_failed.add(nombre)
            return _g_go_hub(rows)
        if "map_screen" in shown:
            for slot, precio in AP_GOAL_MAP_SLOTS:
                if not any(h in slot for h in huecos) or _g_money() < precio + 5000:
                    continue
                for r in rows:
                    if r.get("screen") == "map_screen" and (slot + "a") in _g_img(r):
                        return r
            _apg.types_failed.add(nombre)
            return _g_go_hub(rows)
        return _g_open_from_hub(rows, "Explore")

    def _g_task_academy_lab(rows):
        """Academia + laboratorio: lote basico cada 3 dias (mecanica, y el
        oraculo G10 compara lo que dice el mensaje con el almacen)."""
        if _apg.lab_day is not None and _apg.days_played - _apg.lab_day < 3:
            return "DONE"
        matriculado = bool(getattr(store, "academy_enrolled", False))
        if not matriculado and _g_money() < 25000:
            return "WAIT"
        if matriculado and _g_money() < 8000:
            return "WAIT"
        shown = _g_screens(rows)
        if "choose_worker_for_alchemy_craft" in shown:
            mejor, valor = None, -1
            for r in rows:
                m = _g_re.search(r"\(Craft: (\d+)\)", _g_label(r))
                if r.get("screen") == "choose_worker_for_alchemy_craft" and m and int(m.group(1)) > valor:
                    mejor, valor = r, int(m.group(1))
            if mejor is not None:
                _apg.lab_day = _apg.days_played
                _apg.alchemy_before = {n: _g_owned_count(n) for n in ("Health Potion", "Energy Potion",
                                                                     "Stamina Elixir", "Troll Blood Potion")}
            return mejor or _g_go_hub(rows)
        if "academy_menu" in shown:
            return _g_find(rows, "Rent the Laboratory", screen="academy_menu") or _g_go_hub(rows)
        if "map_screen" in shown:
            if not matriculado and not _apg.academy_logged:
                _apg.academy_logged = True
                _g_experiment_log("academia + laboratorio", 21000)
            return _g_find(rows, "Academy", exact=True, screen="map_screen") or "WAIT"
        return _g_open_from_hub(rows, "Explore")

    def _g_task_church(rows):
        """Iglesia: una visita al dia hasta reunir los cuatro sellos."""
        if _apg.church_day == _g_today() or _apg.church_visits >= 6:
            return "DONE"
        shown = _g_screens(rows)
        if "map_screen" in shown:
            found = _g_find(rows, "Church of the Circle", exact=True, screen="map_screen")
            if found is not None:
                _apg.church_day = _g_today()
                _apg.church_visits += 1
                return found
            return "WAIT"
        return _g_open_from_hub(rows, "Explore")

    def ap_goal_endgame_plan():
        # Cubrir plazas antes de invertir en nada nuevo.
        plan = [("fill_seats_first", _g_task_fill_seats)]
        # Una inversion nueva por semana como mucho, en este orden.
        hueco = (_apg.last_experiment_day is None
                 or _apg.days_played - _apg.last_experiment_day >= AP_GOAL_EXPERIMENT_GAP)
        # Primero lo que aun no se ha probado (es donde estan los bugs que no
        # ha visto nadie); mejorar niveles, al final: puesto delante acaparaba
        # 80 dias y la Academia y los combates especiales no llegaban nunca.
        experimentos = [("exp:franchise", _g_task_franchise),
                        ("exp:arena", _g_task_arena),
                        ("exp:academy", _g_task_academy_lab),
                        ("exp:new_type", _g_task_new_type),
                        ("exp:upgrade", _g_task_upgrade_cheapest)]
        en_curso = _apg.exp_running
        if en_curso:
            plan += [(n, f) for n, f in experimentos if n == en_curso]
        elif hueco:
            # Rotar el punto de partida: sin esto, mejorar edificios (siempre
            # el primero) acaparaba semanas y lo demas no se probaba nunca. Uno
            # sin dinero (WAIT) no bloquea al siguiente.
            plan += [e for e in experimentos if e[0] not in _apg.exp_done] +                     [e for e in experimentos if e[0] in _apg.exp_done]
        # Repetibles que no cuentan como experimento nuevo.
        plan += [("special_match", _g_task_special_match),
                 ("academy_lab", _g_task_academy_lab) if getattr(store, "academy_enrolled", False) else ("noop", lambda r: "DONE"),
                 ("church", _g_task_church),
                 ("fill_seats", _g_task_fill_seats),
                 ("recruit", _g_task_recruit)]
        for building in _g_building_names():
            plan.append(("autofill:" + building, lambda r, b=building: _g_task_autofill(r, b)))
        plan += [("staff_casino", _g_task_staff_casino),
                 ("auto_equip", _g_task_auto_equip),
                 ("next_day", _g_task_next_day)]
        return plan

    # ---------------------------------------------------------------- PLAN

    def ap_goal_plan():
        """Tareas para el objetivo actual, en orden. Lo ultimo es pasar el dia."""
        obj = getattr(store, "current_objective", 1) or 1
        first = (_g_building_names() or ["Building 1"])[0]
        plan = []
        if obj == 1:
            plan += [("skill", _g_task_skill),
                     ("recruit", _g_task_recruit),
                     ("buy_servants", lambda r: _g_task_buy_servants(r, 3))]
        elif obj == 2:
            plan += [("set_type", _g_task_set_type)]
        elif obj == 5:
            plan += [("potion", _g_task_potion)]
        elif obj == 6:
            plan += [("upgrade", lambda r: _g_task_upgrade(r, first)),
                     ("skill_bonus", lambda r: _g_task_skill_bonus(r, first))]
        elif obj == 7:
            plan += [("lunch", _g_task_lunch)]
        elif obj == 8:
            # Segundo edificio: una taberna. Si el primero no es de Charm
            # (Burdel, Restaurante...), sin ella el chantaje del 9 no tiene
            # donde subir Charm.
            plan += [("buy_building", lambda r: _g_task_buy_building(r, 2, "Tavern"))]
        elif obj == 13:
            plan += [("buy_casino", lambda r: _g_task_buy_building(r, 3, "Casino"))]
        # Del 8 en adelante todo se cierra a mano en el Journal: una visita al
        # dia, girando la rueda hasta ver el boton que toque.
        if obj >= 8:
            plan += [("journal_mark", lambda r: _g_task_journal(r, mark=True))]
        if obj >= 13 and _g_casino():
            plan += [("staff_casino", _g_task_staff_casino)]
        if obj >= 14:
            casinos = [b for b in _g_building_names()
                       if str(_g_building(b).get("type") or "").lower() == "casino"]
            for b in casinos:
                # Nivel 3 = 5 plazas de Guard: las 5 de Combat 70 del camino del 16.
                plan += [("upgrade:" + b, lambda r, b=b: _g_task_upgrade_to(r, b, 3))]
        if obj == 15 and _apg.days_played - _apg.obj_since_day > 10:
            # 3.000 en un dia: mas plazas, mas ingresos.
            for b in _g_building_names():
                plan += [("upgrade:" + b, lambda r, b=b: _g_task_upgrade_to(r, b, 3))]
        # Gestion diaria, en todos los objetivos a partir de tener edificio.
        if obj >= 2 and getattr(store, "building_1_type_set", False):
            plan += [("recruit", _g_task_recruit)]
            if obj >= 8:
                plan += [("buy_servants",
                          lambda r: _g_task_buy_servants(r, 10 if obj <= 8 else 15))]
            for building in _g_building_names():
                plan += [("autofill:" + building,
                          lambda r, b=building: _g_task_autofill(r, b))]
        # Equipar despues de contratar y asignar: es el orden de una persona, y
        # cada contratacion nueva ya no relanza el reparto a medias.
        if obj >= 9:
            plan += [("points", _g_task_points),
                     ("auto_equip", _g_task_auto_equip),
                     ("gear", _g_task_gear)]
        # El Journal reevalua: el auto-relleno no comprueba objetivos solo.
        plan += [("journal", _g_task_journal)]
        if obj >= 3:
            plan += [("next_day", _g_task_next_day)]
        return plan

    def _g_run_plan(rows):
        today = _g_today()
        plan = ap_goal_endgame_plan() if _g_endgame_active() else ap_goal_plan()
        for name, fn in plan:
            if _apg.task_failed.get(name) == today:
                continue
            result = fn(rows)
            if name.startswith("exp:"):
                if result == "DONE":
                    if name != "exp:upgrade":
                        _apg.exp_done.add(name)
                    if _apg.exp_running == name:
                        _apg.exp_running = None
                        _apg.last_experiment_day = _apg.days_played
                    continue
                if result not in ("WAIT",) and _apg.exp_running is None:
                    _apg.exp_running = name
                    _apg.exp_rotation += 1
            if result in ("DONE", "WAIT"):
                continue
            if result == "ACTED":
                # La tarea ya actuo por su cuenta (rueda, tecla): nada que pulsar.
                return result
            if result is None:
                # La tarea no sabe que pulsar aqui: contarlo como intento.
                result = _g_go_hub(rows)
                if result is None:
                    continue
            key = (name, today)
            _apg.task_clicks[key] = _apg.task_clicks.get(key, 0) + 1
            if _apg.task_clicks[key] > AP_GOAL_TASK_CLICKS:
                _g_task_gave_up(name, rows)
                continue
            if _apg.task != name:
                _apg.task = name
                ap_note("TASK", "%s (objetivo %s, dia %s, $%s)"
                        % (name, getattr(store, "current_objective", "?"),
                           _apg.days_played, _g_money()))
            return result
        return None

    def _g_task_gave_up(name, rows):
        today = _g_today()
        _apg.task_failed[name] = today
        days = _apg.task_fail_days.setdefault(name, [])
        if today not in days:
            days.append(today)
        ap_note("TASK_FAIL", "%s: %d clics hoy sin completarla" % (name, AP_GOAL_TASK_CLICKS),
                screens=sorted(_g_screens(rows)),
                labels=[(r.get("screen"), _g_label(r)[:30], _g_img(r)[-30:]) for r in rows[:14]])
        # Tres dias distintos sin poder hacerla: ya no es mala suerte.
        # Una sola vez por tarea: el mensaje lleva el recuento y ap_bug no lo
        # deduplicaria.
        if len(days) == 3:
            ap_bug("G4-tarea", "la tarea %r falla 3 dias distintos (objetivo %s)"
                   % (name, getattr(store, "current_objective", "?")))

    # ---------------------------------------------------------------- ORACULOS

    def _g_condition_met(obj):
        """Lo que el Journal pide, medido con lo que el jugador ve en pantalla."""
        if obj == 1:
            return (getattr(store, "workers_hired", 0) >= 3
                    and getattr(store, "manager_start_skill_chosen", False))
        if obj == 3:
            return _g_assigned_count() >= 3
        if obj == 4:
            return _g_money() >= 5000
        return None

    def _g_job_of(w):
        prof = None
        fn = getattr(store, "get_worker_profession", None)
        if callable(fn):
            try:
                prof = fn(w)
            except Exception:
                prof = None
        return str((prof or {}).get("id") or w.get("assigned_building") or "-")

    def _g_equipped(w):
        nombres = []
        por_id = {it.get("id"): it.get("name") for it in _g_items_by_name().values()}
        for entry in (w.get("inventory") or []):
            try:
                if len(entry) >= 3 and entry[2]:
                    nombres.append(str(por_id.get(entry[0], entry[0]))[:18])
            except Exception:
                pass
        return nombres

    def _g_ledger():
        """Libro del dia (lectura): ingresos por edificio del informe diario y
        costes del libro del juego. Sin desglose, una caida del neto no se
        puede atribuir (paso al abrir la Arena)."""
        ingresos = {}
        negativos = {}
        for e in (getattr(store, "daily_report", None) or []):
            if not hasattr(e, "get"):
                continue
            b = str(e.get("building") or e.get("building_name") or "?")
            try:
                v = int(e.get("earnings", 0) or 0)
            except Exception:
                v = 0
            ingresos[b] = ingresos.get(b, 0) + v
            if v < 0:
                negativos[b] = negativos.get(b, 0) + v
        costes = {}
        fn = getattr(store, "daily_ledger_cost_map", None)
        if callable(fn):
            try:
                costes = dict(fn())
            except Exception:
                costes = {}
        _apg.ledger.append({"day": _apg.days_played, "income": ingresos,
                            "losses": negativos, "costs": costes})
        ap_note("LEDGER", "dia %d: ingresos %s | perdidas %s | costes %s"
                % (_apg.days_played, ingresos, negativos, costes))

    def _g_status_probe():
        """Parte de plantilla: los mejores por habilidad EFECTIVA (la que mira el
        juego en los objetivos 9, 14 y 16). Lectura, no escritura."""
        calc = getattr(store, "calculate_skill_with_traits", None)
        if not callable(calc):
            return
        parte = {}
        for skill in ("Combat", "Charm", "Clever"):
            filas = []
            for w in _g_workers():
                try:
                    valor = int(calc(w, skill))
                except Exception:
                    continue
                base = (w.get("skills") or {}).get(skill) if hasattr(w.get("skills"), "get") else None
                filas.append((valor, base, str(w.get("name")), _g_job_of(w)))
            filas.sort(reverse=True)
            parte[skill] = filas[:5]
        # Los que trabajan en profesiones de Combat: a ellos debe llegar el
        # equipo de Combat comprado. Si no llega, el parte lo dice.
        combatientes = []
        for w in _g_workers():
            job = _g_job_of(w)
            if job in ("guard", "adventurer", "boss_hunting", "treasure_hunter") or "guard" in job:
                combatientes.append((str(w.get("name"))[:10], job, bool(w.get("auto_equip")),
                                     _g_equipped(w)))
        parte["combatientes"] = combatientes
        ap_note("STATUS", "dia %d, objetivo %s, $%d: %s" % (
            _apg.days_played, getattr(store, "current_objective", "?"), _g_money(),
            "; ".join("%s %s" % (k, [(v, b, n[:10], j[:12]) for v, b, n, j in vals])
                      for k, vals in parte.items() if k != "combatientes")
            + " | combate: %r" % (combatientes,)),
            parte=parte, puntos_libres=_g_points_left(), nivel_manager=getattr(store, "manager_level", None))

    def _g_building_map():
        out = {}
        for name in _g_owned():
            b = _g_building(name)
            out[name] = (str(b.get("type") or ""), str(b.get("display_name") or b.get("name") or name))
        return out

    def _g_oracle_buildings():
        """G7: comprar o mejorar NO cambia el tipo ni el nombre de los edificios
        que ya tenias (bug real de Discord: comprar una taberna convirtio el
        burdel A en taberna y le cambio el nombre)."""
        actual = _g_building_map()
        previo = _apg.buildings_seen
        if previo is not None:
            for name, (tipo, nombre) in previo.items():
                if name not in actual:
                    if name not in _apg.buildings_sold:
                        ap_bug("G7-edificio", "el edificio %r (%s) desaparecio sin venderlo" % (name, tipo))
                    continue
                # Fijar el tipo de un edificio sin tipo (objetivo 2) es legitimo.
                if actual[name][0] != tipo and tipo and name not in _apg.type_changes_allowed:
                    ap_bug("G7-edificio", "el edificio %r cambio de tipo %s -> %s sin pedirlo"
                           % (name, tipo, actual[name][0]))
                if actual[name][1] != nombre and name not in _apg.type_changes_allowed:
                    ap_bug("G7-edificio", "el edificio %r cambio de nombre %r -> %r sin renombrarlo"
                           % (name, nombre, actual[name][1]))
        _apg.buildings_seen = actual

    def _g_oracle_names():
        """G8: dos workers con el mismo nombre en la plantilla (caso Aelarin:
        el reclutamiento ofrecia el mismo doble una y otra vez)."""
        vistos = {}
        for w in _g_workers():
            n = str(w.get("name") or "")
            vistos[n] = vistos.get(n, 0) + 1
        for n, veces in vistos.items():
            if veces > 1:
                ap_bug("G8-duplicado", "hay %d workers llamados %r en la plantilla" % (veces, n))

    AP_GOAL_OPTION_SCREENS = ("random_event_choice", "choice", "recruitment_choice_screen",
                              "training_branch_menu")

    def _g_oracle_option_geometry(rows):
        """G9: las opciones de un menu de eleccion no se solapan y comparten eje
        (captura de Discord: las opciones bloqueadas se 'caian' fuera de linea)."""
        for screen in AP_GOAL_OPTION_SCREENS:
            opts = [r for r in _ap.last_affordances or [] if r.get("screen") == screen
                    and (r.get("label") or "").strip()]
            # Fuera contenedores: el foco tambien lista el marco que envuelve a
            # todas las opciones (misma etiqueta que la primera, alto enorme).
            def contiene(a, b):
                return (a is not b and a["x"] <= b["x"] and a["y"] <= b["y"]
                        and a["x"] + a["w"] >= b["x"] + b["w"] and a["y"] + a["h"] >= b["y"] + b["h"])
            opts = [a for a in opts if not any(contiene(a, b) for b in opts)]
            if len(opts) < 2:
                continue
            opts.sort(key=lambda r: r["y"])
            for a, b in zip(opts, opts[1:]):
                if b["y"] < a["y"] + a["h"] - 2:
                    ap_bug("G9-opciones", "en %s las opciones %r y %r se solapan (y %d+%d > %d)"
                           % (screen, (a.get("label") or "")[:30], (b.get("label") or "")[:30],
                              a["y"], a["h"], b["y"]))
            centros = [r["x"] + r["w"] // 2 for r in opts]
            if max(centros) - min(centros) > 40:
                ap_bug("G9-opciones", "en %s las opciones no comparten eje: centros x %r"
                       % (screen, centros))

    def ap_goal_oracles(rows):
        obj = getattr(store, "current_objective", 1) or 1
        # Cambio de dia.
        today = _g_today()
        if today != _apg.day_key:
            _apg.day_key = today
            _apg.days_played += 1
            if _apg.money_pre_advance is not None:
                _apg.net_by_day.append((_apg.days_played, _g_money() - _apg.money_pre_advance))
                _apg.money_pre_advance = None
                if _g_endgame_active():
                    _g_ledger()
            _apg.money_by_day.append((_apg.days_played, _g_money()))
            ap_goal_report("running")
            if _apg.days_played % 5 == 0 and obj >= 9:
                _g_status_probe()
            if (_apg.endgame_start is not None
                    and (_apg.days_played - _apg.endgame_start) % 15 == 0
                    and _apg.days_played > _apg.endgame_start):
                _g_checkpoint(obj, "endgame-d%d" % (_apg.days_played - _apg.endgame_start))
        # Cambio de objetivo: linea del cronograma.
        if obj != _apg.obj:
            if _apg.obj is not None:
                ap_note("OBJECTIVE", "objetivo %s -> %s en el dia %d (%d acciones, $%d)"
                        % (_apg.obj, obj, _apg.days_played, _ap.actions, _g_money()))
            _apg.timeline.append({"objective": obj, "day": _apg.days_played,
                                  "date": list(today), "actions": _ap.actions,
                                  "money": _g_money(), "workers": len(_g_workers()),
                                  "buildings": len(_g_building_names())})
            if _apg.obj is not None:
                _g_checkpoint(obj)
            _apg.obj = obj
            _apg.obj_since_day = _apg.days_played
            _apg.journal_opens_on_obj = 0
            _apg.task_failed = {}
            ap_goal_report("running")
        # G1: objetivo estancado mas dias de los que un jugador aguantaria.
        budget = AP_GOAL_DAY_BUDGET.get(obj)
        spent = _apg.days_played - _apg.obj_since_day
        if budget and spent > budget and obj not in _apg.stalled:
            _apg.stalled.add(obj)
            ap_bug("G1-estancado", "objetivo %s lleva %d dias (presupuesto %d); $%d, %d workers, "
                   "%d asignados, %d edificios" % (obj, spent, budget, _g_money(),
                                                   len(_g_workers()), _g_assigned_count(),
                                                   len(_g_building_names())),
                   dinero=_apg.money_by_day[-12:])
        # G2: condicion cumplida y el Journal no se da por enterado.
        if _g_condition_met(obj) and _apg.journal_opens_on_obj >= 2:
            ap_bug("G2-no-detectado", "objetivo %s cumplido (segun lo visible) y sin completar "
                   "tras abrir el Journal %d veces" % (obj, _apg.journal_opens_on_obj))
        _g_oracle_buildings()
        _g_oracle_names()
        _g_oracle_alchemy()
        _g_oracle_reputation_text()
        _g_oracle_franchise_jobs()
        _g_experiment_close()
        _g_oracle_option_geometry(rows)
        # G3: el Journal debe mostrar el objetivo actual.
        if "journal_panel" in _g_screens(rows) or renpy.get_screen("journal_panel") is not None:
            for _screen, text in ap_visible_text():
                m = _g_re.match(r"Objective (\d+):", text.strip())
                if m and int(m.group(1)) != obj:
                    ap_bug("G3-journal", "el Journal muestra 'Objective %s' con el objetivo %s activo"
                           % (m.group(1), obj))
        # G5: bancarrota o vuelta al menu en mitad de la partida.
        if _apg.game_seen and getattr(store, "main_menu", False):
            ap_bug("G5-derrota", "la partida termino en el objetivo %s, dia %d, $%d"
                   % (obj, _apg.days_played, _g_money()), dinero=_apg.money_by_day[-15:])
            ap_goal_finish("derrota")

    def _g_checkpoint(obj, etiqueta=None):
        """Guarda la partida al empezar cada objetivo (ranura 1, la misma que el
        fixture) y copia los ficheros a checkpoints/obj-N/. Un tramo tardio
        (9-16) cuesta 30+ minutos jugado desde cero; con esto se reanuda con
        `autoplay.py --goal --from-save <savedir>/checkpoints/obj-N`."""
        import shutil as _g_shutil
        try:
            set_save_blocked_context(None)
            SnapshotFileSave(1)()
        except renpy.game.CONTROL_EXCEPTIONS:
            raise
        except Exception as e:
            ap_note("CHECKPOINT", "no se pudo guardar el objetivo %s: %r" % (obj, e))
            return
        destino = _ap_out(_g_os.path.join("checkpoints", etiqueta or ("obj-%d" % obj)))
        try:
            if not _g_os.path.isdir(destino):
                _g_os.makedirs(destino)
            copiados = []
            for nombre in _g_os.listdir(_ap_dir()):
                if (nombre.startswith("1-1-") or nombre.startswith("snapshot_1-1")
                        or nombre == "persistent"):
                    _g_shutil.copy2(_g_os.path.join(_ap_dir(), nombre),
                                    _g_os.path.join(destino, nombre))
                    copiados.append(nombre)
            ap_note("CHECKPOINT", "objetivo %d guardado en %s (%s)" % (obj, destino, copiados))
        except Exception as e:
            ap_note("CHECKPOINT", "no se pudo copiar el objetivo %s: %r" % (obj, e))

    # ---------------------------------------------------------------- INFORME

    def ap_goal_report(status):
        data = {
            "status": status,
            "target": AP_GOAL_TARGET,
            "building": AP_GOAL_BUILDING,
            "objective": getattr(store, "current_objective", None),
            "days_played": _apg.days_played,
            "actions": _ap.actions,
            "money": _g_money(),
            "workers": len(_g_workers()),
            "assigned": _g_assigned_count(),
            "buildings": _g_building_names(),
            "timeline": _apg.timeline,
            "task_fail_days": {k: [list(d) for d in v] for k, v in _apg.task_fail_days.items()},
            "money_by_day": _apg.money_by_day,
            "net_by_day": _apg.net_by_day,
            "experiments": _apg.experiments,
            "ledger": _apg.ledger[-120:],
            "findings": [f.get("message") for f in _ap.findings],
        }
        with open(_ap_out("autoplay-goal.json"), "w", encoding="utf-8") as handle:
            _g_json.dump(data, handle, indent=2, ensure_ascii=False, default=str)

    def ap_goal_finish(status):
        if _apg.finished:
            return
        _apg.finished = True
        ap_note("GOAL_END", "%s: objetivo %s, %d dias, %d acciones"
                % (status, getattr(store, "current_objective", None),
                   _apg.days_played, _ap.actions))
        ap_goal_report(status)
        ap_report(status)
        renpy.quit()

    # ---------------------------------------------------------------- ENTRADA

    def ap_goal_choose(rows):
        """Punto de entrada desde ap_choose. Devuelve la fila a pulsar o None."""
        # Ademas de lo prohibido del arnes: nada irreversible sobre la plantilla
        # (liberar tumbas de la iglesia borra al worker muerto para siempre).
        rows = [r for r in rows if r.get("sensitive", True) and not ap_forbidden(r.get("label"))
                and "arrow" not in _g_img(r).lower()
                and not _g_label(r).startswith("Release")]
        if getattr(store, "game_initialized", False) and not getattr(store, "main_menu", False):
            _apg.game_seen = True
        # FM_GOAL_SHOTS=1: una captura la primera vez que sale cada pantalla de
        # la lista, para revisar maquetacion sin tener que jugar a mano.
        if _g_os.environ.get("FM_GOAL_SHOTS"):
            vistas = renpy.session.setdefault("ap_goal_shots", [])
            for nombre in ("map_screen", "tavern", "journal_panel", "recruitment_outcome"):
                if nombre in _g_screens(rows) and nombre not in vistas:
                    vistas.append(nombre)
                    ap_shot("vista-" + nombre)
        # Solo el menu rapido en pantalla = el juego espera un toque (una
        # "pause" tras la imagen final de un evento). En escritorio el menu
        # rapido esta vacio y el arnes avanza solo; en la variante tactil tiene
        # Skip/Auto/Menu y el jugador se quedaba mirando (O2 en events.rpy:939).
        if rows and all(r.get("screen") == "quick_menu" for r in rows):
            ap_dismiss()
            return None
        ap_goal_oracles(rows)
        obj = getattr(store, "current_objective", 1) or 1
        ganado = bool(getattr(store, "objective_16_complete", False))
        if _g_endgame_active():
            if _apg.endgame_start is None:
                _apg.endgame_start = _apg.days_played
                ap_note("ENDGAME", "empieza el end game el dia %d con $%d" % (_apg.days_played, _g_money()))
            if _apg.days_played - _apg.endgame_start >= AP_GOAL_ENDGAME_DAYS:
                ap_goal_finish("endgame")
                return None
        elif obj >= AP_GOAL_TARGET or (AP_GOAL_TARGET > 16 and ganado):
            # Tras el golpe final quedan escenas y la subida de nivel: dejar que
            # pasen antes de cerrar, para que tambien se jueguen.
            if ganado and not _g_at_hub(rows):
                row = _g_universal(rows)
                if row is not None:
                    return row
                return None
            ap_goal_finish("superado")
            return None
        row = _g_universal(rows)
        if row is not None:
            return _g_guard_universal(rows, row)
        row = _g_run_plan(rows)
        if row == "ACTED":
            return None
        if row is not None:
            return row
        # Nada en el plan: volver al hub; si ya estamos, pasar el dia.
        row = _g_go_hub(rows) or _g_task_next_day(rows)
        if row is None:
            _g_diag_lost(rows)
        return row

    def _g_diag_lost(rows):
        """Una vez por combinacion de pantallas: todo lo pulsable y lo que la
        percepcion descarto. Sin esto un 'no se que pulsar' no se puede triar."""
        key = tuple(sorted(str(s) for s in _g_screens(rows)))
        # Esperas normales, no despiste: la tarjeta de cambio de mes se cierra
        # sola en 1 s, y "Next Day" se desactiva 0,4 s al volver al hub.
        if key == ("monthly_transition",) or key == ("tavern",):
            return
        seen = renpy.session.setdefault("ap_goal_lost", [])
        if key in seen:
            return
        seen.append(key)
        crudos = []
        try:
            for focus in renpy.display.focus.focus_list:
                if focus.x is None or focus.widget is None:
                    continue
                crudos.append((_ap_label_of(focus.widget)[:24], int(focus.x), int(focus.y),
                               int(focus.w), int(focus.h)))
        except Exception as e:
            crudos.append(repr(e))
        ap_note("LOST", "sin clic posible en %r" % (key,),
                rows=[(r.get("screen"), _g_label(r)[:30], _g_img(r)[-36:], r["x"], r["y"])
                      for r in rows],
                focus_crudo=crudos[:60])
