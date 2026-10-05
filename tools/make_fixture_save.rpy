# Genera una partida AVANZADA como fixture para el autojugador.
#
# Sembrar un PUNTO DE PARTIDA es legitimo: es lo que hace un tester cuando quiere
# probar contenido tardio. Lo que no vale es sembrar y luego llamar a la logica
# del juego en vez de jugarla. Esta partida se guarda en el slot 1 y el
# autojugador la carga por la UI real (menu -> Load -> ranura).

init python:
    import os as _fx_os

    def fx_log(message):
        with open(_fx_os.path.join(config.savedir, "fixture.txt"), "a", encoding="utf-8") as handle:
            handle.write(str(message) + "\n")

    def fx_worker(template, index):
        worker = dict(template)
        for key, value in list(worker.items()):
            if hasattr(value, "items"):
                worker[key] = dict(value)
            elif hasattr(value, "__iter__") and not isinstance(value, str):
                worker[key] = list(value)
        worker["name"] = "%s %d" % (worker.get("name", "Worker"), index) if index else worker.get("name")
        worker.update({"assigned_building": "Unassigned", "level": 4,
                       "energy": 15, "health": 25, "joy": 60})
        ensure_worker_defaults(worker)
        return worker

    def fx_build(name, kind, price=0):
        add_new_building(name, price)
        building = available_buildings.get(name)
        building["type"] = kind
        building["owned"] = True
        building["base_level"] = 2
        if name not in store.owned_buildings:
            store.owned_buildings.append(name)
        return building

    def fx_make():
        store.main_menu = False
        store.at_main_menu = False
        store.tutorial_active = False
        store.game_initialized = True
        store.is_new_game = False
        store.player_title = "Lady"
        store.player_name = "Tester"
        store.money = 150000
        store.current_day = 12
        store.current_month = 3
        store.current_year = 1
        persistent.age_verified = True
        persistent.nsfw_enabled = bool(_fx_os.environ.get("FM_FIXTURE_NSFW"))
        persistent.worker_gender_filter = "both"
        persistent.intro_popups_enabled = True

        # Roster grande: tambien cubre el caso de rendimiento (40-50 workers).
        catalog = [w for w in load_workers(include_unique=True, include_encounter_only=False,
                                           apply_content_filters=True)
                   if hasattr(w, "get") and w.get("name") and not w.get("monster")]
        store.workers = []
        index = 0
        objetivo = int(_fx_os.environ.get("FM_FIXTURE_WORKERS", "40"))
        while len(store.workers) < objetivo and catalog:
            template = catalog[index % len(catalog)]
            store.workers.append(fx_worker(template, index // len(catalog)))
            index += 1

        # Las profesiones van POR TIPO DE EDIFICIO. Repartir la plantilla entre
        # seis edificios deja a casi todos vacios, porque el auto-relleno solo
        # tira del pool sin asignar. Con UN edificio por partida, los 40 workers
        # cubren todas SUS profesiones; rotando el tipo entre sesiones se cubren
        # las 35. FM_FIXTURE_BUILDING elige cual.
        store.owned_buildings = []
        store.available_buildings = {}
        _fx_tipos = {
            "tavern": ("Tavern", "tavern"),
            "brothel": ("Brothel A", "brothel"),
            "casino": ("Casino", "casino"),
            "castle": ("Castle", "governor_castle"),
            "guild": ("Guild", "adventurers_guild"),
            "restaurant": ("Restaurant", "restaurant"),
        }
        _fx_elegido = (_fx_os.environ.get("FM_FIXTURE_BUILDING") or "").strip().lower()
        if _fx_elegido in _fx_tipos:
            _nombre, _tipo = _fx_tipos[_fx_elegido]
            fx_build(_nombre, _tipo)
            if _tipo != "tavern":
                # La taberna es el hub del juego: se conserva siempre.
                fx_build("Tavern", "tavern")
        else:
            for _nombre, _tipo in _fx_tipos.values():
                fx_build(_nombre, _tipo)
        fx_build("Academy", "academy")
        fx_build("Arena", "arena")
        store.academy_enrolled = True
        store.arena_unlocked = True
        store.arena_lanista_paid = True
        store.alchemy_unlocked = True
        store.current_objective = 9
        for number in range(1, 9):
            setattr(store, "objective_%d_complete" % number, True)
        store.event_flags = {"academy_lib_manual_found": True}
        store.manager_inventory = []
        for item in ("health_potion", "energy_potion"):
            try:
                add_item_to_inventory(store.manager_inventory, item, quantity=5)
            except Exception:
                pass

        # T12.8 pide guardar/cargar con el inventario LLENO y comprobar que
        # cantidades y equipados quedan intactos. Sin esto ningun worker llevaba
        # nada y ninguna entrada estaba equipada, asi que la mitad de la
        # comprobacion era vacia: solo se verificaban las pilas del manager.
        # Se reparte equipo real a los primeros workers, con pilas de varias
        # unidades y una parte equipada (que es la ruta donde ya hubo un bug:
        # _is_equipped leyendo con isinstance una lista nativa de JSON).
        _fx_equipo = ("iron_sword", "leather_armor", "enchanted_ring")
        _fx_consumibles = ("health_potion", "energy_potion")
        for _fx_i, _fx_w in enumerate(store.workers[:12]):
            if not hasattr(_fx_w, "get"):
                continue
            _fx_w.setdefault("inventory", [])
            try:
                # Un consumible apilado: verifica que la cantidad sobrevive.
                add_item_to_inventory(_fx_w["inventory"],
                                      _fx_consumibles[_fx_i % len(_fx_consumibles)],
                                      quantity=3)
                # Y una pieza de equipo, equipada en la mitad de los casos.
                _fx_pieza = _fx_equipo[_fx_i % len(_fx_equipo)]
                add_item_to_inventory(_fx_w["inventory"], _fx_pieza, quantity=1)
                if _fx_i % 2 == 0:
                    toggle_equip_item(_fx_w["inventory"], _fx_pieza, worker=_fx_w)
            except Exception as _fx_e:
                fx_log("no se pudo dar equipo a %s: %r" % (_fx_w.get("name"), _fx_e))
        set_save_blocked_context(None)

        SnapshotFileSave(1)()
        fx_log("fixture guardado: dia %s/%s, %s workers, edificios %s, dinero %s"
               % (store.current_day, store.current_month, len(store.workers),
                  sorted(store.owned_buildings), store.money))


label splashscreen:
    $ fx_make()
    $ renpy.quit(status=0)
