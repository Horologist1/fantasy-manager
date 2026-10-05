# Character Pack: Quick Guide

> The main, always up-to-date reference is the **Mods** tab of the online Field Guide: https://horologist1.github.io/fantasy-manager/guide/#mods (also in `field_guide.html` next to this file).

Five steps from nothing to a character that plays in the game. Details in the [Character Pack Guide](character_pack_guide.md).

1. **Copy the template.** Duplicate `templates/character_pack/`. It's a working pack (Mira) with a character, 2 traits, a story event, a recruitment scene and a daily story.

2. **Make it yours.** Rename `Mira` everywhere: `name`, `folder`, `worker_name`, `has_worker:Mira`, file names and the image folder. Also give your traits, event ids and story ids new names. Names that already exist in the game are rejected.

3. **Add images.** Put them in `game/images/workers/<YourFolder>/`. A `profile` image is required. The other images follow the game's names (`agility (1).jpg`, `rest_tavern (1).png`…).

4. **Zip it.** Put `README.txt` and the `game` folder at the top of the ZIP (not inside another folder). Update the README's file list. The devkit (Mods > Create Mods) can build and check the ZIP for you.

5. **Test it.** Mods > Install mods > choose your ZIP. Check the summary ("1 character / 1 event / 2 traits…"), install, restart and start a new game.

**Rules to remember**
- Packs only add content. Daily stories use `"merge_mode": "append"`.
- One skill check (`condition` + `threshold`) per event choice.
- Conditions: `has_flag:`, `has_worker:`, `after_days:` and similar prefixes. No code.
- Players install a pack **either** with the importer **or** by dragging the `game` folder, never both.
