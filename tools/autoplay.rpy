# Autojugador: JUEGA al juego. Arranca en el menu principal y solo cambia el
# estado mediante input real (SDL, via renpy.test.testmouse), sobre widgets que
# estan de verdad en pantalla. Cero siembra de estado, cero llamadas directas a
# la logica del juego.
#
# Se inyecta SOLO en una copia desechable del proyecto (tools/autoplay.py).
# Se lanza con:  renpy.exe <proyecto> test autoplay
#
# Arquitectura (ver .hermes/audits/AUTOPLAYER_PLAN_2026-09-28.md):
#   PERCEPCION  ap_affordances()  -> que se puede pulsar ahora mismo
#   ACTUACION   ap_click()        -> eventos SDL reales
#   ORACULOS    ap_oracles()      -> invariantes comprobados en cada tick
#   DIARIO      ap_note()/ap_shot -> accion + estado + captura, reproducible

init -100 python:
    import os as _ap_os
    import json as _ap_json
    import random as _ap_random
    import traceback as _ap_tb
    import time as _ap_time
    import re as _ap_re

    class _APState(object):
        """Fuera del store: no debe entrar en rollback ni en los saves."""
        def __init__(self):
            self.tick = 0
            self.actions = 0
            self.journal = []
            self.findings = []
            self.seen_labels = set()
            self.screens_seen = set()
            self.scroll_avisado = set()
            self.scroll_censo = {}
            self.coste_next_day = []
            self.next_day_ctx = []
            self.coste_roster = []
            self.coste_abrir_roster = []
            self.ultimo_notify = None
            self.dinero_previo = None
            self.unidades_previas = 0
            self.compras_vistas = 0
            self.rechazos_vistos = 0
            self.last_signature = None
            self.same_signature_ticks = 0
            self.last_action = None
            self.goal = None
            self.goal_ticks = 0
            self.day_history = []
            self.money_history = []
            self.started = False
            self.finished = False
            self.reported = set()
            self.last_date = None
            self.last_roster = None
            self.pending_close = None
            self.goal_attempts = {}
            self.last_tick_at = None
            self.save_probe_at = 0
            self.last_day_seen = None
            self.last_day_at = 0
            self.last_test_at = 0
            self.own_cost = 0.0
            self.quiet_i8_until = 0
            self.last_money = None
            self.historial = []
            self.tavern_ausente = 0
            self.motivo = ''
            self.motivo_none = ''
            self.partida_iniciada = False
            self.last_affordances = []

    _ap = _APState()

    def _ap_dir():
        return config.savedir

    def _ap_out(name):
        return _ap_os.path.join(_ap_dir(), name)

    def ap_note(kind, message, **extra):
        row = {"tick": _ap.tick, "action": _ap.actions, "kind": kind, "message": str(message)}
        row.update(extra)
        _ap.journal.append(row)
        with open(_ap_out("autoplay-journal.jsonl"), "a", encoding="utf-8") as handle:
            handle.write(_ap_json.dumps(row, ensure_ascii=False, default=str) + "\n")
        if kind in ("BUG", "ERROR"):
            _ap.findings.append(row)
            renpy.log("AUTOPLAY %s: %s" % (kind, message))

    def ap_shot(name):
        safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in str(name))[:60]
        path = _ap_out("shot-%04d-%s.png" % (_ap.actions, safe))
        try:
            renpy.screenshot(path)
        except Exception as e:
            renpy.log("AUTOPLAY: screenshot failed: %r" % (e,))
        return path

    # --------------------------------------------------------------- PERCEPCION

    def _ap_is_text(value):
        # En el store `list`/`dict` son los tipos revertable y Text.text es una
        # lista NATIVA: isinstance contra list/str falla. LA BIBLIA §1.
        return hasattr(value, "strip") and hasattr(value, "encode")

    def _ap_sensitive(node):
        """Button.sensitive es None cuando la sensibilidad se DERIVA de la accion
        (el caso normal en screens). Tratar ese None como False deja al jugador
        creyendo que no hay nada pulsable."""
        flag = getattr(node, "sensitive", None)
        if flag is not None:
            return bool(flag)
        action = getattr(node, "action", None)
        if action is None:
            return bool(getattr(node, "clicked", None))
        actions = action if (hasattr(action, "__iter__") and not _ap_is_text(action)) else [action]
        for item in actions:
            getter = getattr(item, "get_sensitive", None)
            if callable(getter):
                try:
                    if not getter():
                        return False
                except Exception:
                    pass
        return True

    def _ap_walk(node):
        yield node
        try:
            children = node.visit()
        except Exception:
            children = []
        for child in children or []:
            if child is None:
                continue
            for descendant in _ap_walk(child):
                yield descendant

    def _ap_label_of(node):
        """Nombre legible del widget: TTS/alt -> texto hijo -> imagen.

        `alt` es una propiedad de ESTILO, no un atributo del displayable, asi que
        getattr(node, "alt") no la ve. _tts_all() es justo lo que usa el motor en
        renpy/test/testfocus.py para localizar widgets, y resuelve alt y texto.
        """
        try:
            spoken = node._tts_all()
            if _ap_is_text(spoken) and spoken.strip():
                return spoken.strip()
        except Exception:
            pass
        alt = getattr(getattr(node, "style", None), "alt", None)
        if _ap_is_text(alt) and alt.strip():
            return alt.strip()
        for descendant in _ap_walk(node):
            if type(descendant).__name__ != "Text":
                continue
            text = getattr(descendant, "text", None)
            if _ap_is_text(text):
                return text.strip()
            if text is not None and hasattr(text, "__iter__"):
                parts = [p for p in text if _ap_is_text(p) and p.strip()]
                if parts:
                    return " ".join(parts).strip()
        for attribute in ("image", "idle_image", "name"):
            value = getattr(node, attribute, None)
            if _ap_is_text(value):
                return value.rsplit("/", 1)[-1].rsplit(".", 1)[0]
        return ""

    def ap_screens():
        """Screens mostradas ahora, de arriba a abajo."""
        names = []
        for layer in ("screens", "overlay", "transient", "master"):
            try:
                for displayable in reversed(renpy.display.screen.get_screen_layer_list(layer) or []):
                    tag = getattr(displayable, "screen_name", None)
                    if tag:
                        names.append(tag[0] if hasattr(tag, "__getitem__") and not _ap_is_text(tag) else tag)
            except Exception:
                continue
        return names

    def ap_affordances():
        _ap_started = _ap_time.time()
        """Lo que el jugador puede pulsar AHORA.

        Fuente: renpy.display.focus.focus_list, que es la misma lista con la que
        el motor decide que toca el raton. Respeta la modalidad sola: recorrer
        el arbol de render a mano hacia clicar botones de pantallas TAPADAS por
        otra, y esos clics no hacen nada (era el 'atasco' que veia el oraculo).
        """
        rows = []
        try:
            focuses = list(renpy.display.focus.focus_list)
        except Exception:
            focuses = []
        for focus in focuses:
            if focus.x is None or focus.widget is None:
                continue  # foco por defecto, sin rectangulo
            screen = getattr(focus, "screen", None)
            name = getattr(screen, "screen_name", None) or screen
            if name is not None and not _ap_is_text(name) and hasattr(name, "__getitem__"):
                name = name[0]
            rows.append({
                "screen": str(name) if name else "?",
                "label": _ap_label_of(focus.widget),
                "x": int(focus.x), "y": int(focus.y),
                "w": int(focus.w), "h": int(focus.h),
                "sensitive": _ap_sensitive(focus.widget),
                "widget": focus.widget,
            })
        _ap.screens_seen.update(_ap_shown_screens())
        _ap.own_cost += _ap_time.time() - _ap_started
        return [r for r in rows
                if 0 <= r["x"] and 0 <= r["y"]
                and r["x"] + r["w"] <= config.screen_width
                and r["y"] + r["h"] <= config.screen_height
                and r["w"] > 4 and r["h"] > 4]

    def _ap_shown_screens():
        """Screens realmente mostradas, de las scene lists del contexto.

        renpy.display.screen.get_screen() resuelve por tag contra
        renpy.exports.scene_lists(); para ENUMERAR hay que recorrer sus layers,
        que mapean layer -> [SceneListEntry(tag, zorder, ..., displayable, name)].
        """
        names = []
        try:
            scene_lists = renpy.exports.scene_lists()
        except Exception as e:
            # Nunca en silencio: un except mudo aqui me costo dos corridas a ciegas.
            if not renpy.session.get("ap_sl_error"):
                renpy.session["ap_sl_error"] = True
                ap_note("DIAG", "scene_lists() fallo: %r" % (e,))
            return names
        if not renpy.session.get("ap_sl_diag"):
            renpy.session["ap_sl_diag"] = True
            layers = getattr(scene_lists, "layers", None)
            ap_note("DIAG", "layers=%r" % (sorted((layers or {}).keys()),))
            for layer, entries in (layers or {}).items():
                for entry in entries or []:
                    ap_note("DIAG", "entry layer=%s tag=%r name=%r get_screen=%r" % (
                        layer, getattr(entry, "tag", None), getattr(entry, "name", None),
                        renpy.get_screen(getattr(entry, "tag", None) or "") is not None))
        for layer, entries in (getattr(scene_lists, "layers", None) or {}).items():
            for entry in entries or []:
                tag = getattr(entry, "tag", None)
                name = getattr(entry, "name", None)
                candidate = None
                if tag and _ap_is_text(tag):
                    candidate = tag
                elif name is not None and not _ap_is_text(name) and hasattr(name, "__getitem__"):
                    candidate = name[0]
                elif name is not None and _ap_is_text(name):
                    candidate = name
                if not candidate:
                    continue
                # Solo nos interesan las que son screens de verdad.
                if renpy.get_screen(candidate) is None:
                    continue
                if candidate not in names:
                    names.append(candidate)
        return names

    # ---------------------------------------------------------------- ACTUACION

    def ap_aim(row):
        """Punto donde de verdad esta el boton.

        Con `focus_mask True` el rectangulo de foco es la imagen ENTERA (los
        edificios del mapa dan rect=(0,0,1515,1080)): no dice donde esta el
        edificio, eso lo dice la mascara. Hay que buscar un punto cuyo
        focus_at_point() devuelva ESTE widget; comparar coordenadas no sirve.
        """
        _ap_started = _ap_time.time()
        cx = row["x"] + row["w"] // 2
        cy = row["y"] + row["h"] // 2
        widget = row.get("widget")
        resolver = getattr(renpy.display.render, "focus_at_point", None)
        if widget is None or not callable(resolver):
            return cx, cy

        def hits(x, y):
            try:
                focus = resolver(x, y)
            except Exception:
                return False
            return focus is not None and getattr(focus, "widget", None) is widget

        if hits(cx, cy):
            _ap.own_cost += _ap_time.time() - _ap_started
            return cx, cy
        # Rejilla proporcional al tamano: barata en botones pequenos, suficiente
        # en una imagen de mapa completa.
        steps = 8 if row["w"] * row["h"] < 200000 else 26
        for iy in range(1, steps):
            for ix in range(1, steps):
                x = row["x"] + row["w"] * ix // steps
                y = row["y"] + row["h"] * iy // steps
                if hits(x, y):
                    _ap.own_cost += _ap_time.time() - _ap_started
                    return x, y
        _ap.own_cost += _ap_time.time() - _ap_started
        return cx, cy

    def ap_click(row):
        """Clic REAL: mueve el puntero virtual y emite press/release por SDL."""
        mouse = renpy.test.testmouse
        x, y = ap_aim(row)
        mouse.move_mouse(x, y)
        mouse.press_mouse(1)
        mouse.release_mouse(1)
        _ap.actions += 1
        _ap.last_action = row
        ap_note("CLICK", row.get("label") or "(sin etiqueta)",
                screen=row.get("screen"), x=x, y=y)

    class _APKeyNode(object):
        """testkey.get_keycode(node, ...) usa node.filename/linenumber al fallar."""
        filename = "autoplay.rpy"
        linenumber = 0

    _ap_keynode = _APKeyNode()

    _AP_ENTER = chr(10)

    def ap_type(text, then_enter=True):
        """Teclea de verdad, con la misma API que el nodo Type del DSL del motor."""
        for character in text:
            renpy.test.testkey.down(_ap_keynode, character)
            renpy.test.testkey.up(_ap_keynode, character)
        if then_enter:
            # El keysym de Enter es el propio caracter de retorno: el mapa
            # del motor es unicode -> codigo, no nombres tipo K_RETURN.
            renpy.test.testkey.down(_ap_keynode, _AP_ENTER)
            renpy.test.testkey.up(_ap_keynode, _AP_ENTER)
        _ap.actions += 1
        _ap.last_action = {"label": "(type) " + text, "screen": "input"}
        ap_note("TYPE", text)

    def ap_dismiss():
        renpy.queue_event("dismiss")
        _ap.actions += 1
        _ap.last_action = {"label": "(dismiss)", "screen": "say"}
        ap_note("DISMISS", "avanzar dialogo")

    # ----------------------------------------------------------------- ORACULOS
    #
    # Capa PERMANENTE: corre en cada tick de cada prueba. Una prueba mira una
    # cosa; los invariantes miran el resto todo el rato. Sin esto, jugar solo
    # demuestra que no crashea.

    # Solo senales INEQUIVOCAS de rotura. Ojo: "Unknown" es el tramo real de
    # reputacion <50, "Restricted Business" es el nombre de un edificio oculto y
    # "No Image Available" es el placeholder legitimo del filtro de contenido.
    # Meterlos aqui genera falsos positivos, que es peor que no mirar.
    AP_BAD_TEXT = ("[prefix_", "Traceback", "object at 0x", "<built-in", "<function",
                   "KeyError", "AttributeError", "TypeError", "IndexError",
                   "object at 0x", chr(92) + "x1b")
    AP_BAD_EXACT = ("None", "nan", "[]", "{}", "-1", "0/0")

    # Pantallas donde una pulsacion PUEDE cambiar el roster legitimamente.
    AP_ROSTER_SCREENS = {
        "choice", "random_event_choice", "recruitment_choice_screen",
        "recruitment_event_screen", "recruitment_outcome", "choose_event_worker_screen",
        "buy_servants_table", "confirm_buy_worker", "confirm_sell_worker",
        "confirm_refresh_workers", "worker_details", "say",
    }

    AP_CLOSE_WORDS = ("close", "back", "return", "cerrar", "volver", "×", "x")

    def ap_visible_text():
        """Todo el texto pintado ahora mismo, no solo el de los botones."""
        chunks = []
        for name in _ap_shown_screens():
            screen = renpy.get_screen(name)
            if screen is None:
                continue
            try:
                for node in _ap_walk(screen):
                    if type(node).__name__ != "Text":
                        continue
                    value = getattr(node, "text", None)
                    if _ap_is_text(value):
                        chunks.append((name, value))
                    elif value is not None and hasattr(value, "__iter__"):
                        for part in value:
                            if _ap_is_text(part):
                                chunks.append((name, part))
            except Exception:
                continue
        return chunks

    def ap_signature():
        """Huella de lo OBSERVABLE. Incluye las affordances y el texto pintado:
        sin eso, navegar dentro de un panel contaba como 'no pasa nada' y el
        oraculo de atasco disparaba en falso (11 veces en la primera sesion)."""
        affordances = tuple(sorted(
            (r.get("screen") or "", r.get("label") or "") for r in (_ap.last_affordances or [])))
        texts = tuple(sorted({text for _, text in ap_visible_text()}))
        return (
            tuple(_ap_shown_screens()),
            affordances,
            hash(texts),
            getattr(store, "money", None),
            getattr(store, "current_day", None),
            getattr(store, "current_month", None),
            len(getattr(store, "workers", None) or []),
            getattr(store, "current_objective", None),
        )

    def ap_sysmem():
        """(MB libres en el sistema, % de carga de memoria, MB del proceso del
        juego). Un pico de lentitud aislado puede ser el PC, no el juego: sin
        este dato no se distingue (paso con un Next Day de 8 s, 2026-10-03)."""
        try:
            import ctypes
            from ctypes import wintypes

            class _MEMSTAT(ctypes.Structure):
                _fields_ = [("dwLength", wintypes.DWORD), ("dwMemoryLoad", wintypes.DWORD),
                            ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                            ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                            ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                            ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]

            class _PMC(ctypes.Structure):
                _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                            ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                            ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]

            stat = _MEMSTAT()
            stat.dwLength = ctypes.sizeof(_MEMSTAT)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
            pmc = _PMC()
            pmc.cb = ctypes.sizeof(_PMC)
            # Tipos explicitos: sin ellos el pseudo-handle -1 se trunca a 32
            # bits en Windows de 64 y la llamada devuelve 0 MB sin quejarse.
            k32 = ctypes.windll.kernel32
            k32.GetCurrentProcess.restype = wintypes.HANDLE
            info = ctypes.windll.psapi.GetProcessMemoryInfo
            info.argtypes = [wintypes.HANDLE, ctypes.POINTER(_PMC), wintypes.DWORD]
            info.restype = wintypes.BOOL
            info(k32.GetCurrentProcess(), ctypes.byref(pmc), pmc.cb)
            return (int(stat.ullAvailPhys // (1024 * 1024)), int(stat.dwMemoryLoad),
                    int(pmc.WorkingSetSize // (1024 * 1024)))
        except Exception:
            return (None, None, None)

    def ap_bug(code, message, **extra):
        """Un hallazgo por causa: no inundar el informe con el mismo sintoma."""
        key = (code, str(message)[:80])
        if key in _ap.reported:
            return
        _ap.reported.add(key)
        ap_shot(code)
        ap_note("BUG", "[%s] %s" % (code, message), **extra)

    def ap_registrar_ocupadas():
        """Profesiones con alguien asignado ahora mismo, segun servant_jobs."""
        if _ap.tick % 20 != 0:
            return
        vistas = renpy.session.setdefault("ap_ocupadas", [])
        edificios = getattr(store, "available_buildings", None) or {}
        if not hasattr(edificios, "get"):
            return
        for nombre in (getattr(store, "owned_buildings", None) or []):
            building = edificios.get(nombre)
            if not hasattr(building, "get"):
                continue
            jobs = building.get("servant_jobs") or {}
            if not hasattr(jobs, "values"):
                continue
            for pid in jobs.values():
                if pid and pid not in vistas:
                    vistas.append(pid)

    def ap_registrar_profesiones():
        ap_registrar_ocupadas()
        """Acumula las profesiones realmente trabajadas, durante toda la partida.

        Antes solo se llenaba cuando corria la prueba T5.2, que se ejecuta UNA
        vez: la rotacion creia que no se habia trabajado nada y elegia siempre lo
        mismo. Medido: 1 profesion por sesion.
        """
        if _ap.tick % 20 != 0:
            return
        vistas = renpy.session.setdefault("ap_t52_profesiones", [])
        for worker in (getattr(store, "workers", None) or []):
            if not hasattr(worker, "get"):
                continue
            for day in (worker.get("activity_log") or []):
                for item in (day.get("items") or []):
                    meta = item.get("metadata") or {}
                    pid = meta.get("profession_id")
                    if pid and pid not in vistas:
                        vistas.append(pid)

    def ap_scroll_inalcanzable():
        """T15.4: listas cuyo ultimo elemento el jugador no puede alcanzar.

        Al renderizar, Viewport deja en su yadjustment el recorrido que queda
        (viewport.py:130 y siguientes): range > 0 significa que el contenido NO
        cabe. Ese recorrido solo es navegable si hay una barra atada a ESE mismo
        Adjustment, o si el viewport acepta rueda, arrastre o teclas
        (viewport.py:59-60 y 149-150, que por defecto son False). Si no hay
        ninguna de las dos cosas, la cola de la lista es inalcanzable.
        """
        malas = []
        for nombre in _ap_shown_screens():
            try:
                raiz = renpy.get_screen(nombre)
            except Exception:
                continue
            if raiz is None:
                continue
            barras = set()
            viewports = []
            for nodo in _ap_walk(raiz):
                tipo = type(nodo).__name__
                if tipo == "Bar":
                    ajuste = getattr(nodo, "adjustment", None)
                    if ajuste is not None:
                        barras.add(id(ajuste))
                elif tipo == "Viewport":
                    viewports.append(nodo)
            for vista in viewports:
                ajuste = getattr(vista, "yadjustment", None)
                if ajuste is None:
                    continue
                try:
                    pendiente = float(getattr(ajuste, "range", 0) or 0)
                except (TypeError, ValueError):
                    continue
                if pendiente <= 1:
                    continue                      # el contenido cabe
                # Censo: para que un "no hay hallazgos" signifique algo hay que
                # poder demostrar que la sonda SI mira listas reales y las
                # absuelve por un motivo concreto.
                if id(ajuste) in barras:
                    _ap.scroll_censo["barra"] = _ap.scroll_censo.get("barra", 0) + 1
                    continue
                if (getattr(vista, "mousewheel", False)
                        or getattr(vista, "draggable", False)
                        or getattr(vista, "arrowkeys", False)
                        or getattr(vista, "pagekeys", False)):
                    _ap.scroll_censo["gesto"] = _ap.scroll_censo.get("gesto", 0) + 1
                    continue
                malas.append((nombre, int(pendiente)))
        return malas

    def ap_texto_de_notify():
        """El mensaje del aviso que el juego acaba de mostrar, o None."""
        try:
            pantalla = renpy.get_screen("notify")
        except Exception:
            return None
        if pantalla is None:
            return None
        try:
            mensaje = (dict(pantalla.scope or {})).get("message")
        except Exception:
            return None
        return mensaje if _ap_is_text(mensaje) else None

    def ap_o11_compra(dinero_antes, inventario_antes):
        """T12.3: el juego DICE lo que ha cobrado; se comprueba contra el oro real.

        buy_item_from_shop avisa con "Bought {n}x {nombre} for ${total}" y
        buy_item con "Bought {nombre} for ${precio}". Esa frase es la promesa que
        lee el jugador: si el oro no baja exactamente eso, o no aparece el objeto,
        la tienda miente. "Not enough money!" promete lo contrario: que no cobra.
        """
        mensaje = ap_texto_de_notify()
        if not mensaje:
            return
        if mensaje == _ap.ultimo_notify:
            return                    # el mismo aviso sigue en pantalla
        _ap.ultimo_notify = mensaje
        dinero_ahora = getattr(store, "money", None)
        if not isinstance(dinero_antes, int) or not isinstance(dinero_ahora, int):
            return

        if mensaje.startswith("Not enough money"):
            _ap.rechazos_vistos += 1
            if dinero_ahora != dinero_antes:
                ap_bug("O11-compra",
                       "dijo %r y aun asi el oro cambio %d -> %d"
                       % (mensaje, dinero_antes, dinero_ahora))
            return

        cobro = _ap_re.search(r"^Bought (?:(\d+)x )?(.+) for \$(\d+)$", mensaje)
        if not cobro:
            return
        cantidad = int(cobro.group(1) or 1)
        total = int(cobro.group(3))
        gastado = dinero_antes - dinero_ahora
        _ap.compras_vistas += 1
        if gastado != total:
            ap_bug("O11-compra",
                   "dijo cobrar %d por %r y el oro bajo %d (%d -> %d)"
                   % (total, cobro.group(2), gastado, dinero_antes, dinero_ahora))
            return
        # Y tiene que ENTREGAR: el inventario del manager gana esas unidades.
        unidades_ahora = ap_unidades_inventario()
        ganadas = unidades_ahora - inventario_antes
        if ganadas < cantidad:
            ap_bug("O11-compra",
                   "cobro %d por %dx %r y el inventario solo gano %d unidades"
                   % (total, cantidad, cobro.group(2), ganadas))

    def ap_unidades_inventario():
        """Unidades totales en el inventario del manager, sumando pilas."""
        total = 0
        for entrada in (getattr(store, "manager_inventory", None) or []):
            try:
                if hasattr(entrada, "get"):
                    total += int(entrada.get("quantity") or 1)
                elif hasattr(entrada, "__getitem__") and not _ap_is_text(entrada):
                    total += int(entrada[1]) if len(entrada) > 1 else 1
                else:
                    total += 1
            except Exception:
                total += 1
        return total

    # Cupo de compras por sesion: suficiente para que O11 compruebe la tienda de
    # verdad, y corto para no vaciar la bolsa ni desviar la partida.
    AP_ORO_PARA_COMPRAR = 20000
    AP_CUPO_DE_COMPRAS = 4

    def ap_oracles():
        ap_registrar_profesiones()
        """Se llama en cada tick. Registra; no devuelve nada."""
        # O11 (T12.3): comprobar la compra contra el oro y el inventario que habia
        # ANTES de la accion de este tick.
        try:
            ap_o11_compra(_ap.dinero_previo, _ap.unidades_previas)
        except Exception as e:
            ap_note("DIAG", "O11 revento: %r" % (e,))
        _ap.dinero_previo = getattr(store, "money", None)
        _ap.unidades_previas = ap_unidades_inventario()
        money = getattr(store, "money", None)
        day = getattr(store, "current_day", None)
        month = getattr(store, "current_month", None)

        # O4a: dinero imposible.
        if money is not None and not hasattr(money, "strip"):
            if money < -1000000:
                ap_bug("O4-dinero", "dinero absurdo: %s" % money)

        # O4b: el calendario no retrocede.
        if day is not None and month is not None:
            previous = _ap.last_date
            if previous is not None:
                before, after = previous, (month, day)
                if after < before and not (before[0] == 12 and after[0] == 1):
                    ap_bug("O4-calendario", "el calendario retrocedio: %r -> %r" % (before, after))
            _ap.last_date = (month, day)

        # Una CARGA cambia legitimamente todo el estado de golpe: tras ella hay
        # que reiniciar las lineas base, o el invariante acusa a la partida de
        # algo que hizo el jugador al pulsar "Load".
        # Estar en el UI de ficheros (guardar/cargar) explica por si solo que el
        # estado cambie de golpe: el jugador acaba de cargar otra partida.
        _en_ficheros = any(s in ("load", "save", "load_save_slot")
                           for s in _ap_shown_screens())
        if getattr(store, "_just_loaded", False) or _en_ficheros:
            _ap.last_roster = None
            _ap.last_date = None

        # O4c: el roster no cambia de tamano sin una accion que lo explique.
        size = len(getattr(store, "workers", None) or [])
        # Una CARGA cambia dinero, calendario y roster de golpe. El bug que este
        # invariante busca es distinto: workers que se esfuman mientras el resto
        # del estado sigue igual. Si todo cambio a la vez, fue una carga.
        _dinero_ahora = getattr(store, "money", None)
        _todo_cambio = (_ap.last_roster is not None
                        and size != _ap.last_roster
                        and _ap.last_money is not None
                        and _dinero_ahora != _ap.last_money)
        _ap.last_money = _dinero_ahora
        if _todo_cambio:
            _ap.last_roster = size
        elif _ap.last_roster is not None and size != _ap.last_roster:
            delta = size - _ap.last_roster
            last = _ap.last_action or {}
            label = (last.get("label") or "").lower()
            # Fiarse de PALABRAS es fragil: "welcome them and offer $60 per day"
            # es aceptar un reclutamiento y no contiene ningun verbo de la lista.
            # La pantalla donde se pulso es la senal fiable.
            explains = (last.get("screen") in AP_ROSTER_SCREENS) or any(
                word in label for word in
                ("buy", "hire", "recruit", "sell", "fire", "capture", "accept", "welcome",
                 "offer", "comprar", "vender", "despedir", "reclutar"))
            if abs(delta) > 0 and not explains:
                ap_bug("O4-roster", "el roster cambio %+d sin accion que lo explique (ultimo: %r)"
                       % (delta, label))
        _ap.last_roster = size

        # O5/O6: texto roto o imagen ausente, en CUALQUIER texto pintado.
        for screen_name, text in ap_visible_text():
            stripped = text.strip()
            if not stripped:
                continue
            if stripped in AP_BAD_EXACT:
                ap_bug("O6-texto", "campo con valor %r en %s" % (stripped, screen_name))
                continue
            for bad in AP_BAD_TEXT:
                if bad in stripped:
                    ap_bug("O6-texto", "texto roto %r en %s" % (stripped[:60], screen_name))
                    break

        # O10 (T15.4): lista mas larga que su hueco y sin forma de recorrerla.
        for _nombre_lista, _pendiente in ap_scroll_inalcanzable():
            if _nombre_lista in _ap.scroll_avisado:
                continue
            _ap.scroll_avisado.add(_nombre_lista)
            ap_bug("O10-scroll",
                   "en %s queda una lista con %d px sin barra ni rueda: su cola es inalcanzable"
                   % (_nombre_lista, _pendiente))

        # O12: la pantalla del "tipo de mes" sobrevive al paso de dia.
        # `day_transition` (main_flow.rpy) la muestra, espera 1 s, la oculta y
        # salta a la taberna. Reportado por el jugador: a veces se queda flotando
        # sobre la taberna. Si aparece junto a `tavern` es que el hide no surtio
        # efecto; se captura el sitio exacto y una foto para poder triarlo.
        _vistas_ahora = _ap_shown_screens()
        if "tavern" in _vistas_ahora:
            for _colgada in ("monthly_transition", "monthly_card"):
                if _colgada not in _vistas_ahora:
                    continue
                if renpy.session.get("ap_o12_" + _colgada):
                    continue
                renpy.session["ap_o12_" + _colgada] = True
                try:
                    _donde12 = renpy.get_filename_line()
                except Exception:
                    _donde12 = None
                ap_shot("O12-" + _colgada)
                ap_bug("O12-mes-pegado",
                       "%s sigue en pantalla junto a la taberna tras el paso de dia"
                       % (_colgada,),
                       screens=_vistas_ahora,
                       donde=("%s:%s" % _donde12) if _donde12 else None,
                       dia="%s/%s" % (getattr(store, "current_day", "?"),
                                      getattr(store, "current_month", "?")),
                       ultimo=(_ap.last_action or {}).get("label"))

        # O9: el juego espera en `call screen tavern` (main_flow.rpy:884) pero la
        # taberna NO esta mostrada. Eso deja pantalla negra sin nada pulsable: la
        # red de seguridad que hay justo despues de esa llamada solo corre cuando
        # la llamada RETORNA, y aqui no puede retornar porque no hay que pulsar.
        try:
            _fl = renpy.get_filename_line()
        except Exception:
            _fl = None
        if _fl and str(_fl[0]).endswith("main_flow.rpy") and int(_fl[1] or 0) == 884:
            _mostradas = _ap_shown_screens()
            # Que la taberna este oculta es NORMAL: las pantallas del hub se
            # turnan, y ademas hay otras legitimas (Manager, building_type...)
            # que no estan en la lista del juego. Probe ambos criterios y los
            # dos daban falsos positivos. Lo que de verdad caracteriza el fallo
            # es que el jugador se quede SIN NADA que pulsar mientras la llamada
            # a la taberna sigue esperando: eso es la pantalla negra.
            _hay_donde_pulsar = any(
                r.get("sensitive", True) and str(r.get("screen") or "") != "ap_driver"
                for r in (_ap.last_affordances or []))
            if not _hay_donde_pulsar:
                _ap.tavern_ausente += 1
                if _ap.tavern_ausente == 20:
                    ap_bug("O9-taverna-ausente",
                           "esperando en call screen tavern con la taberna oculta",
                           screens=_mostradas,
                           historial=[{"tick": h[0], "screens": list(h[1]), "clic": h[2]}
                                      for h in _ap.historial])
            else:
                _ap.tavern_ausente = 0
        else:
            _ap.tavern_ausente = 0

        # O3: pulsar cerrar y que la pantalla siga ahi. La ventana es corta y se
        # cancela en cuanto se pulsa otra cosa: si no, se acusa a la pantalla de
        # algo que hizo un clic posterior.
        pending = _ap.pending_close
        if pending is not None:
            screen_name, since, label = pending
            if screen_name not in _ap_shown_screens():
                _ap.pending_close = None
            elif _ap.tick - since >= 8:
                ap_bug("O3-no-cierra",
                       "%s sigue abierta 8 ticks despues de pulsar %r" % (screen_name, label))
                _ap.pending_close = None

    # ------------------------------------- I7: guardar y cargar no cambia nada

    def ap_fingerprint():
        """Estado observable que un jugador reconoceria tras cargar."""
        workers = getattr(store, "workers", None) or []
        inventory = getattr(store, "manager_inventory", None) or []
        def _entry_id(entry):
            if hasattr(entry, "get"):
                return str(entry.get("item_id") or entry.get("id") or entry)
            if hasattr(entry, "__getitem__") and not _ap_is_text(entry):
                try:
                    return str(entry[0])
                except Exception:
                    return str(entry)
            return str(entry)

        def _entrada_completa(entry):
            """id + cantidad + equipado.

            T12.8 pide "cantidades y equipados intactos": guardar solo el id
            dejaba pasar justo los dos fallos que mas ha sufrido este inventario
            (una pila que vuelve con otra cantidad, o un equipado que vuelve
            desequipado, como el bug de _is_equipped con isinstance).
            Las entradas llegan como lista nativa de JSON tras cargar y como
            tupla en memoria, asi que se leen por posicion con duck-typing.
            """
            ident = _entry_id(entry)
            cantidad, equipado = None, None
            if hasattr(entry, "get"):
                cantidad = entry.get("quantity")
                equipado = entry.get("equipped")
            elif hasattr(entry, "__getitem__") and not _ap_is_text(entry):
                try:
                    cantidad = entry[1] if len(entry) > 1 else None
                    equipado = entry[2] if len(entry) > 2 else None
                except Exception:
                    pass
            # El flag viaja como bool, como "true"/"1" y como 0/1 segun la ruta.
            if _ap_is_text(equipado):
                equipado = equipado.strip().lower() in ("true", "1", "yes", "y", "on")
            try:
                cantidad = int(cantidad) if cantidad is not None else None
            except (TypeError, ValueError):
                cantidad = None
            return "%s|%s|%s" % (ident, cantidad, bool(equipado))

        inventarios_de_workers = []
        for w in workers:
            if not hasattr(w, "get"):
                continue
            filas = sorted(_entrada_completa(e) for e in (w.get("inventory") or []))
            if filas:
                inventarios_de_workers.append("%s::%s" % (w.get("name"), ",".join(filas)))
        return {
            "money": getattr(store, "money", None),
            "day": getattr(store, "current_day", None),
            "month": getattr(store, "current_month", None),
            "year": getattr(store, "current_year", None),
            "objective": getattr(store, "current_objective", None),
            "workers": sorted(str(w.get("name")) for w in workers if hasattr(w, "get")),
            "buildings": sorted(str(b) for b in (getattr(store, "owned_buildings", None) or [])),
            "inventory": sorted(_entrada_completa(e) for e in inventory),
            "inventarios_de_workers": sorted(inventarios_de_workers),
        }

    def ap_i7_check():
        """Compara tras una carga; se llama al principio del tick."""
        before = renpy.session.get("ap_i7_before")
        if not before:
            return
        renpy.session["ap_i7_before"] = None
        # Tras cargar, el motor reconstruye estado durante varios ticks. Eso no
        # es "una interaccion lenta": se mide aparte, en T3.12.
        _ap.last_tick_at = None
        _ap.quiet_i8_until = _ap.tick + 15
        renpy.session["ap_load_ms"] = int((_ap_time.time() - (renpy.session.get("ap_load_started") or _ap_time.time())) * 1000)
        after = ap_fingerprint()
        diff = [k for k in before if before.get(k) != after.get(k)]
        if diff:
            for key in diff:
                ap_bug("I7-saveload", "guardar+cargar cambio %s: %r -> %r"
                       % (key, before.get(key), after.get(key)))
        else:
            ap_note("I7", "guardar+cargar idempotente (dia %s, %s workers)"
                    % (after.get("day"), len(after.get("workers") or [])))

    def _ap_i7_slot():
        """Nombre de la ranura 99 tal como la escribe SnapshotFileSave."""
        nombre = None
        try:
            nombre = _get_current_slot_name(99)
        except Exception:
            nombre = None
        if not nombre:
            nombre = "%s-99" % (getattr(persistent, "_file_page", 1) or 1)
        return nombre

    def ap_i7_probe():
        """Cada N acciones: guarda, carga y compara. Usa las mismas acciones que
        los botones de guardar/cargar del juego."""
        if not getattr(store, "game_initialized", False) or getattr(store, "main_menu", False):
            return False
        # FM_AP_I7_EVERY: cada cuantas acciones guardar+cargar (250 por defecto).
        # Bajarlo sirve para provocar fallos que solo salen tras una carga.
        if _ap.actions - _ap.save_probe_at < int(_ap_os.environ.get("FM_AP_I7_EVERY") or 250):
            return False
        _ap.save_probe_at = _ap.actions
        # Hay secuencias (reclutamiento...) donde el juego NO deja guardar y lo
        # avisa. Guardar ahi no hace nada, y cargar despues trae la ranura
        # ANTERIOR: eso salio como "guardar+cargar cambio day 25 -> 20" el
        # 2026-10-03 y era el arnes, no el juego.
        permitido = getattr(store, "save_is_allowed", None)
        if callable(permitido) and not permitido():
            _ap.save_probe_at = _ap.actions - 230   # reintentar en unas acciones
            return False
        try:
            set_save_blocked_context(None)
            antes_mtime = renpy.slot_mtime(_ap_i7_slot())
            renpy.session["ap_i7_before"] = ap_fingerprint()
            # El propio ciclo de guardar+cargar tarda ~1,5 s con 40 workers. Es
            # coste del MEDIDOR, no una interaccion que el jugador sufra: sin
            # anular la linea base, I8 lo denunciaba cada 250 acciones.
            _ap.last_tick_at = None
            _ap.quiet_i8_until = _ap.tick + 15
            SnapshotFileSave(99)()
            # Sin escritura nueva no hay nada que comparar: la carga traeria
            # otra partida.
            if renpy.slot_mtime(_ap_i7_slot()) == antes_mtime:
                renpy.session["ap_i7_before"] = None
                ap_note("I7", "el juego no guardo (secuencia en curso); ciclo descartado")
                return False
            renpy.session["ap_load_started"] = _ap_time.time()
            CanonicalSnapshotFileLoad(FileLoad(99, confirm=False), 99, confirm=False)()
            # Si la ejecucion LLEGA aqui, la carga no ocurrio: una carga de
            # verdad sale por FullRestartException y nunca vuelve. Dejar armada
            # la comparacion es peor que no medir, porque ap_i7_check la
            # resolveria contra la proxima carga que haga el jugador -- de OTRA
            # ranura y de otro dia -- y denunciaria un bug inexistente
            # (asi salieron "money 134718 -> 146171" y la lista de workers).
            renpy.session["ap_i7_before"] = None
            ap_note("I7", "la carga de la sonda no se ejecuto; ciclo descartado")
            return False
        except renpy.game.CONTROL_EXCEPTIONS:
            # FullRestartException NO es un fallo: es el mecanismo con el que el
            # motor ejecuta una carga. Tragarsela convierte cada carga en un bug
            # falso y, peor, impide que la carga ocurra.
            raise
        except Exception as e:
            renpy.session["ap_i7_before"] = None
            ap_bug("I7-saveload", "guardar o cargar fallo: %r" % (e,))
            return False

    def ap_watch_close(row):
        """Arma la comprobacion solo si el boton ES un cierre (texto exacto), y
        cancela cualquier vigilancia previa: un clic nuevo invalida el anterior."""
        _ap.pending_close = None
        label = (row.get("label") or "").strip().lower()
        if label in AP_CLOSE_WORDS:
            _ap.pending_close = (row.get("screen"), _ap.tick, label)

    # ------------------------------------------------------------------- BUCLE

    _ap.last_affordances = []

    def ap_tick():
        _ap.tick += 1
        # Historial corto de pantallas, LO PRIMERO del tick: las pantallas de
        # dialogo salen antes por un return temprano, y registrarlo despues
        # dejaba el historial vacio justo en los casos que hay que triar.
        _ap.historial.append((_ap.tick, tuple(_ap_shown_screens()),
                              ((_ap.last_action or {}).get("label") or "")[:40]))
        if len(_ap.historial) > 10:
            _ap.historial.pop(0)
        # I8: si una interaccion tarda demasiado, el jugador lo nota.
        now = _ap_time.time()
        if _ap.last_tick_at is not None:
            elapsed = now - _ap.last_tick_at
            # Descontar lo que cuesta el ARNES (percepcion + apuntado): acusar al
            # juego de una lentitud que pone el medidor seria un falso positivo.
            propio = _ap.own_cost
            motor = elapsed - propio
            # Las primeras acciones son arranque y carga de partida, no juego:
            # con el fixture de 40 workers eso cuesta ~1,6 s y se medía como si
            # fuera una interaccion. El coste de cargar lo mide T3.12 aparte.
            # Guardar el coste de CADA avance de dia, no solo los que pasan el
            # umbral: dos picos de 1,5 s sin distribucion no dicen si el avance
            # de dia es lento siempre o solo a veces.
            etiqueta_previa = ((_ap.last_action or {}).get("label") or "")
            if "Next Day" in etiqueta_previa and _ap.actions > 20:
                _ap.coste_next_day.append(round(motor, 3))
                # Contexto de CADA avance: dia, workers, evento y memoria del
                # sistema. Un pico solo se puede culpar al juego si se repite
                # con memoria holgada.
                libre, carga, propio_mb = ap_sysmem()
                _ap.next_day_ctx.append({
                    "s": round(motor, 3),
                    "dia": "%s/%s" % (getattr(store, "current_day", "?"),
                                      getattr(store, "current_month", "?")),
                    "workers": len(getattr(store, "workers", None) or []),
                    "evento": ((getattr(store, "current_event", None) or {}).get("id")
                               if hasattr(getattr(store, "current_event", None), "get") else None),
                    "ram_libre_mb": libre, "ram_carga_pct": carga, "juego_mb": propio_mb,
                })
            # Coste de CADA interaccion con el roster abierto. El perfilador de
            # Ren'Py abre su log con flush=False y se pierde si el proceso no sale
            # limpio, asi que para comparar variantes de la fila hace falta un
            # instrumento propio que no dependa de eso.
            # Coste de ABRIR el roster, en orden. Sirve para distinguir "la
            # primera apertura calienta caches" de "abrirlo cuesta siempre".
            if etiqueta_previa.strip() == "Workers" and _ap.actions > 20:
                _ap.coste_abrir_roster.append(round(motor, 3))
            if _ap.actions > 20 and "workers" in _ap_shown_screens():
                # Con el numero de FILAS pintadas, que es de lo que depende el
                # coste. Sin este dato dos sesiones distintas no se pueden
                # comparar: una con un filtro puesto mide 25 filas y la otra 200,
                # y la diferencia parece una mejora que no existe (me paso).
                _filas = -1
                try:
                    _scr_w = renpy.get_screen("workers")
                    if _scr_w is not None:
                        _fw = (dict(_scr_w.scope or {})).get("filtered_workers")
                        if _fw is not None:
                            _filas = len(_fw)
                except Exception:
                    _filas = -1
                _ap.coste_roster.append((_filas, round(motor, 3)))
            if motor > 1.5 and _ap.tick > _ap.quiet_i8_until and _ap.actions > 20:
                # Cuantos widgets habia realmente pintados: a 200 workers la
                # sospecha es que el coste es construir la fila, y sin este dato
                # no se distingue "estaban las 200 filas" de "habia un filtro".
                try:
                    _pintados = len(ap_affordances())
                except Exception:
                    _pintados = -1
                _libre, _carga, _juego = ap_sysmem()
                ap_bug("I8-lento",
                       "interaccion de %.2f s (arnes %.2f s) tras %r [accion %d, dia %s/%s, "
                       "%d workers, %d pulsables, pantallas %r, RAM libre %s MB (%s%% usada), "
                       "juego %s MB]"
                       % (motor, propio, (_ap.last_action or {}).get("label"),
                          _ap.actions, getattr(store, "current_day", "?"),
                          getattr(store, "current_month", "?"),
                          len(getattr(store, "workers", None) or []),
                          _pintados, _ap_shown_screens(), _libre, _carga, _juego))
        _ap.own_cost = 0.0
        _ap.last_tick_at = now

        # Cargar una partida de 40 workers cuesta ~1,6 s. Eso NO es "una
        # interaccion lenta" del jugador: es la carga, y su coste se mide aparte
        # en T3.12. Sin silenciarlo, cada arranque desde fixture generaba un
        # falso positivo (y tumbaba T6.11, que cuenta esos avisos).
        _iniciada = bool(getattr(store, "game_initialized", False))
        _en_ficheros = any(s in ("load", "save", "load_save_slot")
                           for s in _ap_shown_screens())
        if (_iniciada and not _ap.partida_iniciada) or _en_ficheros:
            _ap.quiet_i8_until = _ap.tick + 15
            _ap.last_tick_at = None
        _ap.partida_iniciada = _iniciada
        # La sesion termina por presupuesto (el proceso muere), asi que el
        # informe se reescribe sobre la marcha o no existiria nunca.
        if _ap.tick % 40 == 0:
            ap_report('running')
        if _ap.tick % 400 == 0:
            # Reintentar objetivos abandonados: el estado del juego ha cambiado.
            _ap.goal_attempts = {}


        # Entrada de texto: el juego pide el nombre del jugador.
        if renpy.get_screen("input") is not None:
            # Una tarea puede dejar encargado lo que hay que teclear (buscar un
            # objeto en la tienda); si no, es el nombre del jugador.
            ap_type(renpy.session.pop("ap_next_input", None)
                    or renpy.session.get("ap_player_name") or "Autoplayer")
            return

        # Dialogo: avanzar SOLO si no hay un menu de eleccion encima. Ren'Py deja
        # el `say` visible detras del `choice`, y descartarlo primero es un bucle
        # infinito: el menu nunca se responde.
        # Un `say` SIN texto no es un dialogo pendiente: queda debajo de una
        # pantalla modal (el informe diario) tras un dialogo de objetivo lanzado
        # a mitad del dia. Avanzar dialogo ahi no hace nada; la persona cierra
        # el informe. Tratarlo como dialogo clavo 3 de 3 partidas (2026-10-03).
        _say_vacio = False
        _scr_say = renpy.get_screen("say")
        if _scr_say is not None:
            try:
                _what = (dict(_scr_say.scope or {})).get("what")
                _say_vacio = not (_what and str(_what).strip())
                if not _say_vacio:
                    # Lo ultimo que se LEYO: los menus que siguen a una pista
                    # ("Round one. ...") ya no la muestran en pantalla.
                    renpy.session["ap_last_say"] = str(_what)
            except Exception:
                _say_vacio = False
            if _say_vacio and "tavern" in _ap_shown_screens() and not renpy.session.get("ap_say_vacio_hub"):
                renpy.session["ap_say_vacio_hub"] = True
                ap_bug("O13-say-vacio", "un dialogo vacio sigue mostrado sobre el hub",
                       screens=_ap_shown_screens())
        if renpy.get_screen("choice") is None and _scr_say is not None and not _say_vacio:
            # O2-say: el atasco DENTRO de un dialogo. El return temprano de abajo
            # salta el oraculo O2 general, y un say que no avanza se comio 900
            # ticks sin ningun aviso (2026-10-03).
            _firma_say = (tuple(_ap_shown_screens()),
                          hash(tuple(sorted(t for _s, t in ap_visible_text()))))
            if _firma_say == renpy.session.get("ap_say_firma"):
                renpy.session["ap_say_racha"] = (renpy.session.get("ap_say_racha") or 0) + 1
            else:
                renpy.session["ap_say_firma"] = _firma_say
                renpy.session["ap_say_racha"] = 0
            if renpy.session.get("ap_say_racha") == 60:
                try:
                    _donde_say = "%s:%s" % renpy.get_filename_line()
                except Exception:
                    _donde_say = None
                try:
                    _ctx = len(renpy.game.contexts)
                except Exception:
                    _ctx = None
                ap_bug("O2-say", "60 avances de dialogo sin ningun cambio",
                       donde=_donde_say, contextos=_ctx, screens=_ap_shown_screens(),
                       textos=[t[:80] for _s, t in ap_visible_text()][:8],
                       pila=[str(x)[:60] for x in (renpy.get_return_stack() or [])][-6:])
            ap_dismiss()
            return

        affordances = ap_affordances()
        _ap.last_affordances = affordances


        # Capa permanente de invariantes: cada tick, en toda prueba.
        ap_oracles()
        ap_i7_check()
        if ap_i7_probe():
            return
        runner = getattr(store, 'ap_tests_tick', None)
        if callable(runner) and runner():
            return

        # O2: atasco de verdad. La huella ya incluye affordances y texto pintado,
        # asi que "sin cambio" significa que las pulsaciones no hacen NADA.
        signature = ap_signature()
        if signature == _ap.last_signature:
            _ap.same_signature_ticks += 1
            # Un boton que no cambia NADA tres veces seguidas es inerte para el
            # jugador (p. ej. "Auto-fill empty slots" en un edificio ya lleno:
            # el juego avisa con un notify identico). Insistir en el generaba
            # atascos falsos; se aparta un rato.
            ultimo = _ap.last_action or {}
            clave = (ultimo.get("screen"), (ultimo.get("label") or "").strip())
            if clave[1]:
                inertes = renpy.session.setdefault("ap_inertes", {})
                veces = inertes.get(clave, 0) + 1
                inertes[clave] = veces
                if veces == 3:
                    ap_note("INERTE", "%r en %s no cambia nada: se evita"
                            % (clave[1], clave[0]))
        else:
            _ap.same_signature_ticks = 0
            _ap.last_signature = signature
            ultimo = _ap.last_action or {}
            clave = (ultimo.get("screen"), (ultimo.get("label") or "").strip())
            inertes = renpy.session.get("ap_inertes") or {}
            if clave in inertes:
                del inertes[clave]
        # Antes de denunciar un atasco, hacer lo que haria una persona: salir de
        # la pantalla. Si con eso se desbloquea, era mi jugador dando vueltas en
        # un panel inerte, no el juego.
        if _ap.same_signature_ticks == 45:
            # Solo el boton de volver. Nada de pulsar Esc: abre el menu del
            # juego y descarrila la sesion entera (medido: de 9 profesiones a 0).
            for row in (_ap.last_affordances or []):
                etiqueta = (row.get("label") or "").strip().lower()
                if etiqueta in ("back", "return", "close", "volver", "cerrar"):
                    ap_note("ESCAPE", "saliendo de %s tras 45 ticks sin cambio" % row.get("screen"))
                    ap_click(row)
                    return

        if _ap.same_signature_ticks == 60:
            # Sin saber DONDE esta el juego, un atasco no se puede triar. El
            # fichero y la linea del statement actual lo dicen exactamente.
            donde = None
            try:
                donde = renpy.get_filename_line()
            except Exception:
                pass
            etiqueta = None
            try:
                etiqueta = renpy.get_return_stack()[-1] if renpy.get_return_stack() else None
            except Exception:
                pass
            # Estado interno de las pantallas mostradas: si el contador de la
            # narracion avanza, el clic SI se registro y el atasco es mio.
            estados = {}
            for _nombre in _ap_shown_screens():
                _scr = renpy.get_screen(_nombre)
                if _scr is None:
                    continue
                try:
                    _sc = dict(_scr.scope or {})
                except Exception:
                    continue
                estados[_nombre] = {k: repr(v)[:40] for k, v in _sc.items()
                                    if k in ("nidx", "lines", "message_index", "page")}
            textos = [txt[:60] for _s, txt in ap_visible_text()[:6]]
            ap_bug("O2-atasco", "60 ticks sin cambio observable pulsando",
                   screens=_ap_shown_screens(), last=_ap.last_action,
                   donde=("%s:%s" % donde) if donde else None, pila=str(etiqueta)[:80],
                   estados=estados, textos=textos, motivo=_ap.motivo,
                   pulsables=[(r.get("screen"), (r.get("label") or "")[:30],
                               r.get("sensitive"))
                              for r in (_ap.last_affordances or [])][:8],
                   historial=[{"tick": h[0], "screens": list(h[1]), "clic": h[2]}
                              for h in _ap.historial])

        if not affordances:
            # Nada pulsable: narracion, transicion de dia o una escena esperando
            # avance. Un jugador haria clic igualmente; "dismiss" es esa accion.
            ap_dismiss()
            return

        _ap.motivo_none = ""
        row = ap_choose(affordances)
        if row is None and affordances and not renpy.session.get("ap_none_diag"):
            renpy.session["ap_none_diag"] = True
            ap_note("DIAG", "choose=None con %d affordances; motivo_none=%r; filas=%r"
                    % (len(affordances), _ap.motivo_none,
                       [((r.get("label") or "")[:28], r.get("screen"), r.get("sensitive"))
                        for r in affordances[:4]]))
        _ap.motivo = ((_ap.motivo_none or "choose=None") if row is None and _ap.motivo_none
                      else "sin pulsables" if not affordances
                      else ("choose=None con %d pulsables" % len(affordances)) if row is None
                      else "clic")
        if row is None:
            if not renpy.session.get("ap_choose_diag"):
                renpy.session["ap_choose_diag"] = True
                ap_note("DIAG", "ap_choose devolvio None con %d affordances: %r"
                        % (len(affordances), [(a["label"], a["sensitive"]) for a in affordances[:8]]))
            return
        ap_watch_close(row)
        ap_click(row)

    # Nunca pulsar esto: termina la sesion o destruye datos.
    AP_FORBIDDEN = ("quit", "exit", "delete", "salir", "borrar", "uninstall", "desinstalar")

    # Guion de apertura: lo que un jugador pulsa para empezar una partida.
    def ap_opening_base():
        # El modo de contenido se elige explicitamente: dejarlo al azar hacia
        # que media suite no se ejecutase nunca en SFW, que es donde viven los
        # bugs de filtrado de contenido.
        modo = (_ap_os.environ.get("FM_AUTOPLAY_MODE") or "nsfw").strip().lower()
        contenido = "Disable NSFW content" if modo == "sfw" else "Enable NSFW content"
        titulo = (_ap_os.environ.get("FM_AUTOPLAY_TITLE") or "Lady").strip()
        return ["Start", "Yes, I am 18", contenido, titulo]

    AP_OPENING = ["Start", "Yes, I am 18", "Lady"]

    # Para probar contenido tardio (Academia, Arena, templo) hay que partir de una
    # partida avanzada: llegar ahi jugando desde cero exige jugar BIEN, que es otro
    # problema. La partida preparada es un fixture; cargarla se hace por la UI real.
    AP_OPENING_LOAD = ["Load"]

    def ap_opening_script():
        if _ap_os.environ.get("FM_AUTOPLAY_LOAD"):
            return list(AP_OPENING_LOAD)
        return ap_opening_base()

    def ap_forbidden(label):
        low = (label or "").lower()
        return any(word in low for word in AP_FORBIDDEN)

    # Objetivos dirigidos: (texto del boton, pantalla que debe abrirse).
    # Sin esto la exploracion aleatoria no entra nunca en Academia, Arena,
    # templo ni mods: se queda dando vueltas por el hub.
    AP_GOALS = [
        ("Academy", "academy_menu"),
        ("Arena", "arena_menu"),
        ("Church", "church_menu"),
        ("Temple", "church_menu"),
        ("Franchise", "franchise_holdings"),
        ("Holdings", "franchise_holdings"),
        ("Laboratory", "alchemy_recipe_menu"),
        ("Alchemy", "alchemy_recipe_menu"),
        ("Buy", "buy_map_building"),
        ("Servants", "buy_servants_table"),
        ("Shops", "shop_selection"),
        ("Manage", "job_selection"),
        ("Interact", "interaction_category"),
        ("Walk", "take_a_walk_result"),
        ("Training", "training_branch_menu"),
        ("Curriculum", "academy_curriculum_menu"),
        ("Preferences", "preferences"),
        ("Help", "help"),
        ("History", "history"),
    ]

    # El UI de ficheros es destructivo por exploracion: pulsar ranuras y
    # confirmar sobrescribe partidas o carga otra al azar, lo que reinicia el
    # progreso y hunde la cobertura. Las pruebas de save (T3.x) lo cubren aparte.
    AP_FILE_SCREENS = ("load", "save", "load_save_slot")

    # Pantallas donde se elige el trabajo de un worker.
    AP_JOB_SCREENS = ("job_selection", "Building_select_global", "batch_job_picker",
                      "worker_selection_popup", "Manager")

    def ap_profesiones_pendientes():
        """(nombre visible, id) de las profesiones que aun no se han trabajado.

        Lo ejercitado lo registra la prueba T5.2 al leer el historial: si una
        profesion nunca aparece ahi, nadie la ha trabajado todavia.
        """
        hechas = set(renpy.session.get("ap_t52_profesiones") or [])
        salida = []
        try:
            tipos = building_types_json.get("building_types") or []
        except Exception:
            return salida
        propios = set(getattr(store, "owned_buildings", None) or [])
        edificios = getattr(store, "available_buildings", None) or {}
        tipos_propios = set()
        if hasattr(edificios, "get"):
            for nombre in propios:
                b = edificios.get(nombre)
                if hasattr(b, "get") and b.get("type"):
                    tipos_propios.add(b.get("type"))
        for bt in tipos:
            if tipos_propios and bt.get("id") not in tipos_propios:
                continue
            for profesion in (bt.get("professions") or []):
                pid = profesion.get("id")
                if not pid or pid in hechas:
                    continue
                if not profession_is_visible(profesion, bt):
                    continue
                salida.append((profesion.get("name") or pid, pid))
        return salida

    def ap_pending_goals():
        """Objetivos vivos: pantalla no vista todavia y aun con intentos.

        El limite de intentos es imprescindible: un patron que casa con un boton
        que NO lleva a su pantalla (p. ej. "Buy" casa con media UI) monopoliza la
        politica y hunde la cobertura. Medido: sin limite, 7%; con limite, 30%+.
        """
        alive = []
        for text, screen in AP_GOALS:
            if screen in _ap.screens_seen:
                continue
            # Los intentos decaen: si el objetivo sigue sin cumplirse mas tarde,
            # el juego habra cambiado (mas dinero, otro dia) y merece reintento.
            if _ap.goal_attempts.get((text, screen), 0) >= 4:
                continue
            alive.append((text, screen))
        return alive

    # Pantallas donde se completa un paso de progreso.
    AP_PROGRESS_SCREENS = {
        "buy_map_building", "building_selection", "building_type_selection",
        "buy_servants_table", "job_selection", "Building_select_global",
        "worker_selection_popup", "batch_worker_manager", "batch_job_picker",
        "batch_building_picker", "autofill_settings", "autofill_building_picker",
    }

    def row_key(rows, text):
        """Identidad del objetivo de progreso: el boton concreto que se persigue.
        Sin esto el contador no distingue 'Buy' del mercado del 'Buy' del mapa."""
        for row in rows:
            if text.lower() in (row.get("label") or "").lower():
                return (row.get("screen"), row.get("label"))
        return None

    def ap_choose(affordances):
        """Politica: primero el guion pendiente, luego exploracion en anchura."""
        # Tope de repeticion: un par (pantalla, etiqueta) pulsado una y otra vez
        # sin que la partida avance es un bucle, cambie o no la pantalla.
        repetidos = renpy.session.setdefault("ap_repetidos", {})
        ultimo = _ap.last_action or {}
        clave_ult = (ultimo.get("screen"), (ultimo.get("label") or "").strip())
        if clave_ult[1]:
            repetidos[clave_ult] = repetidos.get(clave_ult, 0) + 1
        if _ap.tick % 300 == 0:
            repetidos.clear()

        if "Manager" in _ap_shown_screens() and not renpy.session.get("ap_mgr_diag"):
            renpy.session["ap_mgr_diag"] = True
            ap_note("DIAG", "etiquetas en Manager: %r"
                    % ([(r.get("label") or "")[:26] for r in affordances
                        if r.get("screen") == "Manager"][:22],))

        inertes = renpy.session.get("ap_inertes") or {}
        usable = [r for r in affordances
                  if r.get("sensitive", True) and not ap_forbidden(r.get("label"))
                  and inertes.get((r.get("screen"), (r.get("label") or "").strip()), 0) < 3
                  and repetidos.get((r.get("screen"), (r.get("label") or "").strip()), 0) < 25]
        if not usable:
            usable = [r for r in affordances
                      if r.get("sensitive", True) and not ap_forbidden(r.get("label"))]
        if not usable:
            # Ultimo recurso: si hay ALGO pulsable, pulsarlo. Devolver None
            # teniendo una afordancia sensible es siempre un fallo del jugador,
            # no del juego, y se denunciaba como atasco O2.
            #
            # Caso real que lo destapo (training_branch_narration,
            # worker_training.rpy:1219): una narracion a pantalla completa cuyo
            # UNICO pulsable es el mismo boton una y otra vez. Avanza de verdad
            # -- su nidx sube con cada pulsacion -- pero para la heuristica
            # anti-bucle parecia "pulsar lo mismo sin que cambie nada", asi que
            # lo prohibia y la sesion se quedaba clavada ahi.
            rescate = [r for r in affordances if r.get("sensitive", True)]
            if rescate:
                _ap.motivo_none = ""
                ap_note("RESCATE", "todos los filtros vaciaron la lista; se pulsa %r de %s"
                        % ((rescate[0].get("label") or "")[:40], rescate[0].get("screen")))
                return rescate[0]
            _ap.motivo_none = "no habia nada pulsable: %r" % (
                [[(r.get("label") or "")[:30], r.get("sensitive")] for r in affordances[:3]],)
            return None

        script = renpy.session.get("ap_script")
        if script is None:
            script = ap_opening_script()
            renpy.session["ap_script"] = script
        if script:
            pattern = script[0]
            for row in usable:
                if pattern.lower() in (row.get("label") or "").lower():
                    script.pop(0)
                    ap_note("GOAL", "guion: " + pattern)
                    return row

        # Cargar la partida preparada es un objetivo PERSISTENTE, no un paso de
        # guion: consumirlo al primer clic hacia que un clic fallido dejase la
        # sesion entera jugando desde cero sin que nadie se enterase.
        if _ap_os.environ.get("FM_AUTOPLAY_LOAD") and not getattr(store, "game_initialized", False):
            for row in usable:
                if (row.get("label") or "").strip().lower() == "load":
                    return row
            slots = [r for r in usable
                     if str(r.get("screen") or "") in ("load", "save", "load_save_slot")
                     and not any(word in (r.get("label") or "").lower()
                                 for word in ("page", "auto", "quick", "back", "return", "delete"))]
            if slots:
                ap_note("GOAL", "cargando partida preparada via %r" % slots[0].get("label"))
                return slots[0]

        # Modo "con objetivo" (tools/autoplay_goal.rpy): el jugador persigue los
        # objetivos del Journal en vez de explorar. Recibe TODAS las affordances,
        # no `usable`: los filtros anti-bucle de la exploracion apartan botones
        # que un jugador pulsa cada dia ("Next Day", "Yes"), y la tarea lleva su
        # propio tope de clics.
        goal_choose = getattr(store, "ap_goal_choose", None)
        # Solo con el guion de apertura agotado: si no, una eleccion al azar en
        # la intro podia contestar "No, I am under 18".
        if (callable(goal_choose) and getattr(store, "game_initialized", False)
                and not renpy.session.get("ap_script")):
            row = goal_choose(affordances)
            if row is None:
                _ap.motivo_none = "jugador con objetivo: nada que pulsar"
            return row

        # Modo "dias rapidos": para cubrir volumen (35 profesiones, 275 eventos)
        # hacen falta MUCHOS dias, y deambular consume ~500 acciones por dia.
        # Aqui el jugador va al grano: asigna si faltan profesiones y, si no,
        # pasa el dia. Sin exploracion.
        if _ap_os.environ.get("FM_AUTOPLAY_FASTDAYS") and                 getattr(store, "game_initialized", False) and                 not getattr(store, "main_menu", False):
            if ap_profesiones_pendientes():
                for texto in ("Auto-fill", "Manage", "Assign"):
                    for row in usable:
                        if texto.lower() in (row.get("label") or "").lower():
                            return row
            for row in usable:
                if "next day" in (row.get("label") or "").lower():
                    return row
            # Nada que hacer aqui: volver al hub para encontrar el boton del dia.
            for row in usable:
                if (row.get("label") or "").strip().lower() in ("back", "return", "volver"):
                    return row

        # Marcapasos: si el dia no avanza, nada mas importa. Sin esto el objetivo
        # de asignar acaparaba (258 intentos) y la partida se quedaba en el dia 8
        # tras 3.000 acciones, sin dinero para desbloquear Academia ni Arena.
        day_now = getattr(store, "current_day", None)
        if day_now != _ap.last_day_seen:
            _ap.last_day_seen = day_now
            _ap.last_day_at = _ap.actions
        # Cuanto mas rapido pasan los dias, mas profesiones y eventos se
        # ejercitan: una profesion solo cuenta cuando alguien la trabaja un dia
        # entero. 120 acciones por dia dejaban 6 dias por sesion.
        if _ap.actions - _ap.last_day_at > 55:
            for row in usable:
                if "next day" in (row.get("label") or "").lower():
                    ap_note("GOAL", "marcapasos: pasar el dia")
                    return row

        # Una confirmacion se confirma: un jugador que persigue progreso dice Si.
        # Pulsar "No" al azar era la mitad de las compras abortadas.
        # Las confirmaciones no se llaman todas "confirm": hay confirm_buy_worker,
        # confirm_sell_worker, confirm_upgrade, confirm_buy_potion... Filtrar por
        # el nombre exacto dejaba fuera justo las que deciden el progreso.
        en_ficheros = any(s in AP_FILE_SCREENS for s in _ap_shown_screens())
        cargando_fixture = bool(_ap_os.environ.get("FM_AUTOPLAY_LOAD")) and             not getattr(store, "game_initialized", False)
        if en_ficheros and not cargando_fixture:
            # Salir de ahi en vez de trastear: buscar el boton de volver.
            for row in usable:
                if (row.get("label") or "").strip().lower() in ("back", "return", "volver"):
                    return row

        # Ir a los ajustes del auto-relleno del edificio abierto ("..."), una
        # vez por edificio: es donde esta la casilla que permite mover workers
        # ya asignados, sin la cual el auto-relleno solo usa el pool libre y se
        # quedan 5 profesiones ocupadas de 35.
        if "Manager" in _ap_shown_screens() and "autofill_settings" not in _ap_shown_screens():
            permitidos = renpy.session.setdefault("ap_permitir_mover", [])
            if len(permitidos) < 6:
                for row in usable:
                    if (row.get("label") or "").strip() == "...":
                        ap_note("GOAL", "abriendo ajustes de auto-relleno")
                        return row

        if "autofill_settings" in _ap_shown_screens():
            if not renpy.session.get("ap_afs_diag"):
                renpy.session["ap_afs_diag"] = True
                ap_note("DIAG", "etiquetas en autofill_settings: %r"
                        % ([(r.get("label") or "")[:40] for r in usable
                            if r.get("screen") == "autofill_settings"][:14],))
            hechos = renpy.session.setdefault("ap_permitir_mover", [])
            for row in usable:
                etiqueta = (row.get("label") or "").strip()
                if "allow unassign" in etiqueta.lower():
                    if etiqueta not in hechos:
                        hechos.append(etiqueta)
                        ap_note("GOAL", "permitiendo mover workers entre puestos")
                        return row
            for row in usable:
                if (row.get("label") or "").strip().lower() in ("back", "return", "close", "volver"):
                    return row

        # No confirmar a ciegas los cambios estructurales: "Yes" en
        # confirm_change_type fallaba, abria error_popup y el jugador entraba en
        # bucle Yes/Ok que se comia la sesion (medido: 0 dias jugados).
        AP_NO_CONFIRMAR = ("confirm_change_type", "confirm_refresh_workers",
                           "confirm_sell_worker")
        confirming = [r for r in usable
                      if str(r.get("screen") or "").startswith("confirm")
                      and str(r.get("screen") or "") not in AP_NO_CONFIRMAR]
        if en_ficheros and not cargando_fixture:
            confirming = []
        if confirming:
            for word in ("yes", "ok", "confirm", "accept", "buy", "si", "aceptar"):
                for row in confirming:
                    if (row.get("label") or "").strip().lower() == word:
                        return row

        # Objetivos de PARTIDA: sin progresar no se desbloquea nada. Academia,
        # Arena y templo no se abren pulsando, se abren teniendo.
        workers = getattr(store, "workers", None) or []
        owned = getattr(store, "owned_buildings", None) or []
        money = getattr(store, "money", 0) or 0
        progress = []
        if not workers:
            progress = ["Buy Servants", "Servants", "Recruit", "Hire"]
        elif not owned:
            progress = ["Buy Buildings", "Buy"]
        elif len([w for w in workers if hasattr(w, "get")
                  and w.get("assigned_building", "Unassigned") != "Unassigned"]) < (
                      25 if ap_profesiones_pendientes() else 6):
            # Con profesiones sin estrenar, conviene tener MUCHA gente asignada:
            # cada dia ejercita todas las profesiones ocupadas a la vez, asi que
            # repartir 25 workers cubre en un dia lo que uno cubre en 25.
            # Umbral, no "todos": con 40+ workers siempre queda alguno sin
            # asignar, y el objetivo de asignar acaparaba la politica para
            # siempre. Con suficientes trabajando, toca explorar el resto.
            progress = ["Manage", "Assign", "Job"]
        elif money > 8000:
            progress = ["Buy Buildings", "Academy", "Arena"]
        else:
            # Todo el mundo trabajando y sin dinero para expandir: lo que hace un
            # jugador es PASAR EL DIA. Sin esta regla se queda dando vueltas por
            # los menus: medido, 3.043 acciones para llegar solo al dia 7, y sin
            # dinero no se desbloquean Academia ni Arena.
            progress = ["Next Day"]
        # Los flujos de progreso son de VARIOS pasos (abrir la tabla, elegir fila,
        # confirmar). Si al abrirlos el jugador se va a otra pantalla, no compra
        # ni asigna nunca: medido, 4 workers contratados y 0 asignados. Estando
        # dentro de una pantalla de progreso, se queda en ella hasta terminar.
        if progress:
            inside = [r for r in usable
                      if str(r.get("screen") or "") in AP_PROGRESS_SCREENS]
            if inside:
                usable = inside

        # Mientras quede progreso por hacer, no fundir el dinero en la tienda:
        # medido, gastaba los 6000 iniciales en pociones y se quedaba sin poder
        # contratar ni comprar edificios.
        #
        # Pero la prohibicion era absoluta y dejaba T12.3 ("comprar en cada
        # tienda: cobra y entrega") sin verificar NUNCA: el oraculo de compras no
        # vio ni una en 400 s. Con el fixture avanzado (150.000 de oro) gastar
        # unos miles no estorba a ningun progreso, asi que se permite un cupo
        # corto de compras cuando sobra dinero de verdad.
        if progress and not (isinstance(getattr(store, "money", None), int)
                             and store.money >= AP_ORO_PARA_COMPRAR
                             and _ap.compras_vistas < AP_CUPO_DE_COMPRAS):
            usable = [r for r in usable
                      if not (str(r.get("screen") or "") in ("manager_inventory", "shop_selection")
                              and (r.get("label") or "").strip().lower().startswith("buy"))]
            if not usable:
                _ap.motivo_none = "filtro de compras dejo la lista vacia"
                return None

        for text in progress:
            key = ("progreso", text, row_key(usable, text))
            if _ap.goal_attempts.get(key, 0) >= 6:
                continue
            for row in usable:
                if text.lower() in (row.get("label") or "").lower():
                    _ap.goal_attempts[key] = _ap.goal_attempts.get(key, 0) + 1
                    ap_note("GOAL", "progreso: %s via %r (intento %d)"
                            % (text, row.get("label"), _ap.goal_attempts[key]))
                    return row

        # Objetivo de compra (T12.3): con el cupo abierto, ir a la tienda y
        # comprar. Dejarlo al azar no sirve: medido, una semilla compraba 4 veces
        # y la siguiente ninguna, asi que el oraculo O11 no comprobaba nada.
        if (isinstance(getattr(store, "money", None), int)
                and store.money >= AP_ORO_PARA_COMPRAR
                and _ap.compras_vistas < AP_CUPO_DE_COMPRAS):
            pantallas_ahora = _ap_shown_screens()
            # Ya dentro de la tienda: pulsar un "Buy".
            if "manager_inventory" in pantallas_ahora or "shop_selection" in pantallas_ahora:
                for row in usable:
                    etiqueta = (row.get("label") or "").strip().lower()
                    if etiqueta.startswith("buy") or etiqueta == "purchase":
                        clave = ("comprar", row.get("label"))
                        if _ap.goal_attempts.get(clave, 0) < 8:
                            _ap.goal_attempts[clave] = _ap.goal_attempts.get(clave, 0) + 1
                            ap_note("GOAL", "compra: %r" % row.get("label"))
                            return row
            else:
                for texto in ("Shops", "Shop", "Market", "Inventory"):
                    clave = ("ir a tienda", texto)
                    if _ap.goal_attempts.get(clave, 0) >= 4:
                        continue
                    for row in usable:
                        if texto.lower() in (row.get("label") or "").lower():
                            _ap.goal_attempts[clave] = _ap.goal_attempts.get(clave, 0) + 1
                            ap_note("GOAL", "ir a la tienda via %r" % row.get("label"))
                            return row

        # Auto-relleno: asignar uno a uno gasta todos los clics de la sesion
        # (medido: 25 workers = 100+ clics y solo 3 dias jugados). "Auto-fill
        # Building" reparte un edificio entero de una vez.
        pendientes_prof = ap_profesiones_pendientes()
        if pendientes_prof:
            # El auto-relleno NO mueve a quien ya trabaja en otro edificio: solo
            # tira del pool sin asignar (gameplay_improvements.rpy:726). Con 40
            # workers repartidos, los edificios siguientes se quedan vacios y
            # solo se ejercitan 5-6 profesiones. La palanca que da el juego es
            # la casilla "Allow unassign lower skill workers".
            rellenados = renpy.session.setdefault("ap_autofill_hechos", [])
            if "autofill_building_picker" in _ap_shown_screens():
                salir = None
                for row in usable:
                    if row.get("screen") != "autofill_building_picker":
                        continue
                    etiqueta = (row.get("label") or "").strip()
                    bajo = etiqueta.lower()
                    if any(p in bajo for p in ("back", "return", "settings", "ajustes", "volver")):
                        salir = salir or row
                        continue
                    if etiqueta and etiqueta not in rellenados:
                        rellenados.append(etiqueta)
                        ap_note("GOAL", "auto-relleno: %r" % etiqueta)
                        return row
                # Todos los edificios rellenados: cerrar el selector, no insistir.
                if salir is not None:
                    return salir
            sin_asignar = [w for w in workers if hasattr(w, "get")
                           and w.get("assigned_building", "Unassigned") == "Unassigned"]
            # Solo mientras queden edificios por rellenar: sin este limite el
            # jugador reabria el selector 822 veces sobre el mismo edificio.
            propios_n = len(getattr(store, "owned_buildings", None) or [])
            # Hay DOS botones de auto-relleno: "Auto-fill Building" abre el
            # selector y "Auto-fill empty slots" rellena el edificio actual sin
            # abrirlo. Contando solo el primero, el jugador insistia 367 veces
            # con el segundo. Se cuentan los intentos, vengan de donde vengan.
            intentos = renpy.session.get("ap_autofill_intentos") or 0
            if len(sin_asignar) >= 5 and intentos < max(4, propios_n * 2):
                for row in usable:
                    if "auto-fill" in (row.get("label") or "").strip().lower():
                        renpy.session["ap_autofill_intentos"] = intentos + 1
                        ap_note("GOAL", "auto-relleno (intento %d)" % (intentos + 1))
                        return row

        # Para tocar una profesion hay que ENTRAR a gestionar su edificio. Si no
        # se dirige, el jugador se queda en el que ya esta y la rotacion oscila
        # entre sesiones (medido: de 9 profesiones a 3 sin esto).
        if pendientes_prof and "Manager" not in _ap_shown_screens():
            faltan_en = set()
            edificios = getattr(store, "available_buildings", None) or {}
            if hasattr(edificios, "get"):
                tipos = {}
                for bt in (building_types_json.get("building_types") or []):
                    tipos[bt.get("id")] = [p.get("id") for p in (bt.get("professions") or [])]
                hechas = set(renpy.session.get("ap_t52_profesiones") or [])
                for nombre in (getattr(store, "owned_buildings", None) or []):
                    b = edificios.get(nombre)
                    if not hasattr(b, "get"):
                        continue
                    if set(tipos.get(b.get("type"), [])) - hechas:
                        faltan_en.add(str(nombre))
            intentos_g = renpy.session.setdefault("ap_gestion_intentos", {})
            for row in usable:
                etiqueta = (row.get("label") or "").strip()
                if not (etiqueta in faltan_en or any(
                        n and n.lower() in etiqueta.lower() for n in faltan_en)):
                    continue
                # Tope por edificio: sin el, este objetivo se come la sesion
                # entera (medido: cobertura de 36% a 11%, cero dias jugados).
                hechos = intentos_g.get(etiqueta, 0)
                if hechos >= 3:
                    continue
                intentos_g[etiqueta] = hechos + 1
                ap_note("GOAL", "gestionar %r (intento %d)" % (etiqueta, hechos + 1))
                return row

        # Rotacion sistematica de profesiones: la lista pide las 35, y explorando
        # al azar solo se tocaban 4. Estando en el selector de trabajo, elegir
        # una profesion que AUN NO se haya ejercitado.
        if any(s in AP_JOB_SCREENS for s in _ap_shown_screens()):
            pendientes = pendientes_prof
            if pendientes:
                for row in usable:
                    etiqueta = (row.get("label") or "").strip().lower()
                    if not etiqueta:
                        continue
                    for nombre, pid in pendientes:
                        if nombre and nombre.lower() in etiqueta:
                            ap_note("GOAL", "rotacion: profesion %s" % pid)
                            return row

        # Objetivos dirigidos antes que exploracion ciega.
        for text, target in ap_pending_goals():
            # Exacto antes que parcial: "Academy" en el mapa abre academy_menu,
            # pero "Academy: Academy selected" es una fila de asignacion. Con
            # coincidencia parcial el objetivo gastaba sus intentos en la fila.
            ordered = ([r for r in usable if (r.get("label") or "").strip().lower() == text.lower()]
                       + [r for r in usable if (r.get("label") or "").strip().lower() != text.lower()])
            for row in ordered:
                if text.lower() in (row.get("label") or "").lower():
                    key = (text, target)
                    _ap.goal_attempts[key] = _ap.goal_attempts.get(key, 0) + 1
                    ap_note("GOAL", "buscando %s via %r (intento %d)"
                            % (target, row.get("label"), _ap.goal_attempts[key]))
                    return row

        # Exploracion: no despedir ni vender a tu propia plantilla por azar. Se
        # probaran dirigidas (T6.3); al azar solo saboteaban la progresion, y el
        # roster vaciado hacia inalcanzable medio juego.
        usable = [r for r in usable
                  if not any(word in (r.get("label") or "").strip().lower()
                             for word in ("sell", "fire", "dismiss", "vender", "despedir"))] or usable
        if not cargando_fixture:
            sin_ficheros = [r for r in usable
                            if str(r.get("screen") or "") not in AP_FILE_SCREENS]
            usable = sin_ficheros or usable

        # Exploracion: preferir lo que no se ha pulsado aun en esta screen.
        visited = renpy.session.setdefault("ap_visited", set())
        fresh = [r for r in usable
                 if (r.get("screen"), r.get("label")) not in visited]
        pool = fresh or usable
        if not pool:
            _ap.motivo_none = "pool de exploracion vacio"
            return None
        row = _ap_random.choice(pool)
        visited.add((row.get("screen"), row.get("label")))
        return row


screen ap_driver():
    zorder 1500
    timer 0.15 repeat True action Function(ap_tick)


init python:
    def ap_all_screens():
        """Todas las screens DEFINIDAS en el juego, para medir cobertura sola."""
        names = set()
        try:
            for key in renpy.display.screen.screens:
                names.add(key[0] if (hasattr(key, "__getitem__") and not _ap_is_text(key)) else key)
        except Exception:
            pass
        return names

    # Infraestructura: no son destino de la exploracion.
    AP_PLUMBING = {
        "say", "input", "choice", "confirm", "notify", "tooltip", "quick_menu",
        "navigation", "esc_key_handler", "bubble", "nvl", "nvl_dialogue",
        "error_popup", "skip_indicator", "table_rule", "message_window",
        "worker_portrait_thumb", "auto_advance_summary", "more_options",
        "ap_driver", "main_menu", "menu",
        # Red de seguridad del hub: infraestructura, no contenido que visitar.
        "fm_hub_recovery",
    }

    def ap_report(status="done"):
        every = ap_all_screens()
        # Las screens internas del motor (_console, _developer, _gallery...) no son
        # contenido del juego y falsearian la cobertura hacia abajo.
        every = {n for n in every if not str(n).startswith("_")}
        targets = sorted(every - AP_PLUMBING)
        reached = sorted((_ap.screens_seen & every) - AP_PLUMBING)
        report = {
            "coverage": {
                "screens_total": len(every),
                "targets": len(targets),
                "reached": len(reached),
                "percent": (100 * len(reached) // len(targets)) if targets else 0,
                "unreached": sorted(set(targets) - set(reached)),
            },
            "status": status,
            "ticks": _ap.tick,
            "actions": _ap.actions,
            "screens_seen": sorted(_ap.screens_seen),
            "findings": _ap.findings,
            "tests": renpy.session.get("ap_results") or {},
            # Volumen REAL ejercitado: la lista pide 35 profesiones y 275
            # eventos; sin medirlo, "todo verde" no dice cuanto se toco.
            "ejercitado": {
                "profesiones": sorted(renpy.session.get("ap_t52_profesiones") or []),
                "eventos": sorted((getattr(store, "event_occurrences", None) or {}).keys()),
                "dias_jugados": len(renpy.session.get("ap_t46_days") or []),
                # Diagnostico del cuello: cuantas profesiones estan OCUPADAS
                # frente a cuantas llegan a trabajarse. Si se ocupan muchas y se
                # trabajan pocas, el problema no es asignar.
                "profesiones_ocupadas": sorted(renpy.session.get("ap_ocupadas") or []),
                # Censo de la sonda de scroll: sin esto, "0 hallazgos de scroll"
                # no distingue "todas las listas se recorren" de "no mire ninguna".
                "scroll_censo": dict(_ap.scroll_censo),
                "compras_verificadas": _ap.compras_vistas,
                "compras_rechazadas": _ap.rechazos_vistos,
                "coste_next_day": list(_ap.coste_next_day),
                "next_day_ctx": list(_ap.next_day_ctx),
                "coste_roster": list(_ap.coste_roster),
                "coste_abrir_roster": list(_ap.coste_abrir_roster),
            },
            "day": getattr(store, "current_day", None),
            "money": getattr(store, "money", None),
            "objective": getattr(store, "current_objective", None),
            "workers": len(getattr(store, "workers", None) or []),
            "owned_buildings": list(getattr(store, "owned_buildings", None) or []),
            "assigned": len([w for w in (getattr(store, "workers", None) or [])
                             if hasattr(w, "get")
                             and w.get("assigned_building", "Unassigned") != "Unassigned"]),
            "goal_attempts": {"%s|%s" % (k[0], k[1]): v
                              for k, v in list(_ap.goal_attempts.items())[:40]},
        }
        with open(_ap_out("autoplay-report.json"), "w", encoding="utf-8") as handle:
            _ap_json.dump(report, handle, indent=2, ensure_ascii=False, default=str)
        return report

    def ap_exception_handler(short, full, traceback_fn):
        # O1: un crash es el hallazgo mas valioso; registrarlo con contexto.
        try:
            ap_shot("crash")
            ap_note("ERROR", "EXCEPCION: " + str(short),
                    screens=_ap_shown_screens(), last=_ap.last_action, full=str(full)[:4000])
            ap_report("crashed")
        except Exception:
            pass
        return False  # que el motor siga con su manejo normal

    config.exception_handler = ap_exception_handler

    # I6: el motor avisa de cada imagen que no puede cargar. Es la deteccion
    # fiable; buscar "No Image Available" en pantalla no vale, porque ese
    # placeholder tambien sale legitimamente con el filtro de contenido.
    def ap_missing_image(filename):
        # Ren'Py consulta assets de su plantilla GUI (gui/button/background.png,
        # gui/scrollbar/...) que este proyecto no incluye a proposito: los
        # resuelve por estilo. Solo el arte del juego (images/) importa aqui.
        name = str(filename).replace("\\", "/")
        if name.startswith("images/"):
            ap_bug("I6-imagen", "imagen ausente: %s" % name)
        return None

    config.missing_image_callback = ap_missing_image

    # El jugador debe estar activo TAMBIEN en el menu principal: always_shown_screens
    # muestra la screen en todos los contextos, sin tocar el arranque del juego.
    if "ap_driver" not in config.always_shown_screens:
        config.always_shown_screens.append("ap_driver")

    _ap_random.seed(int(_ap_os.environ.get("FM_AUTOPLAY_SEED", "1")))
    ap_note("START", "autoplay iniciado, semilla=%s" % _ap_os.environ.get("FM_AUTOPLAY_SEED", "1"))
