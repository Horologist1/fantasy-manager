# Fantasy Manager Devkit — User guide

## Quick guide: a character pack in 5 steps

1. Keep the project mode on Character pack and type a mod name at the top of the page.
2. Under Workers, choose ＋ Unique Worker, answer the questions and choose Save to project. Give the character a plain-text name and a short image folder such as mira_storm.
3. Choose Manage character images, then Choose portrait for each character. Add other PNG, JPG or WebP pictures with Add other images.
4. Optional: add new traits, events, recruitment events or daily stories with the assistants in the other sections (see “Adding events, traits and daily stories to a character pack” below).
5. Choose Save draft to keep an editable copy, then Review & export ZIP. Fix every error and choose Export ZIP. Players install the ZIP from the game’s Mods → Install mods, or extract it and drag its game folder onto the game’s main folder. README.txt inside the ZIP explains both methods.



## Create and install mods

The devkit edits a separate project. It never writes to your original game files. The bundled reference includes the game version shown at the top of the page; you can create a pack without selecting a game folder.

Save draft downloads an editable .fmproject.json file containing your project and pictures. Open draft restores that file. Export ZIP produces the pack players install. A ZIP is not an editable project backup. Save form changes to the project before saving a draft; keep the draft before closing or refreshing the browser.

## Choose the right project mode

Character pack adds regular named characters and their images, plus optional new traits, events, recruitment events and daily stories for existing jobs. It supports the in-game installer on PC and Android, and manual drag & drop on PC. Procedural templates, monsters, items, buildings, interactions and monthly conditions are outside this mode.

JSON override (experimental) starts from existing game files. Each file in the exported ZIP replaces that complete original file, at the same data/... path. Other entries and unknown fields in the copied file are retained when you edit one entry. Images, scripts and Interactions are not imported in this mode.

Manual JSON files (PC only) keeps the advanced authoring tools for content outside the managed importer. Its ZIP contains a game folder for manual installation into a backed-up PC game. Do not select this mode for the Android Mods installer.

## What is inside an exported character pack

Every file of a character pack sits under a top-level game folder, for example game/data/workers/mira.json and game/images/workers/mira_storm/profile.png. A README.txt at the top of the ZIP lists the contents and explains how to install and uninstall the pack.

The same ZIP works in two ways. In the game, Mods → Install mods reads the ZIP directly (leave Import as JSON override off) and ignores README, LICENSE, CHANGELOG and CREDITS text files. On PC you can instead extract the ZIP and drag the game folder onto the game’s main folder (the folder that contains Fantasy_Manager.exe), merging folders. A character pack only adds new files, so it never replaces original game files; the devkit refuses project file names that already exist in the game.

Use only one method for a pack. Installing it both ways loads the same content twice. To remove a pack installed in the game, use Uninstall in Mods → Install mods. To remove a manual install, delete the files listed in README.txt.

JSON override ZIPs keep data/... paths without a game folder. Install them only through Mods → Install mods with Import as JSON override enabled; never drag & drop them, because each file would replace an original game file.

## Adding events, traits and daily stories to a character pack

A character pack can carry these JSON files next to its workers: data/traits/*.json (new traits), data/events/*.json (daily and story events), data/events/recruit/*.json (recruitment events) and data/buildings/daily_story_extensions/*.json (new daily stories for existing jobs). A pack may even have no workers at all, for example new events for base-game characters.

Everything must be new. Trait names, event IDs and daily story IDs must not exist in the game already and must not repeat inside the pack. Daily and recruitment events share one ID list. Daily event IDs must not start with event_recruit_, because the game keeps those out of the daily event pool; put recruitment events in data/events/recruit/.

Daily stories are always added to a job: building_id and profession_id must name an existing building and job, and the devkit writes merge_mode "append" for you. Character packs cannot use "upsert" or "replace_all" to change the game’s own stories; use a JSON override for that.

Conditions (start_when and stop_when) may only combine, with AND or OR: True, False, a prefixed condition (has_flag:, flag_value:, after_days_from_flag:, exact_date:, has_worker:, not_has_worker:, has_folder_worker:, not_has_folder_worker:, after_date:, before_days:, after_days:), or a simple comparison such as money >= 500 or store.current_objective == 7. Brackets, parentheses, function calls and double underscores are rejected, because the game would run them as code.

Event flag values (event_flags) must be plain values such as true, numbers or text. The only allowed [code] value is "[calculate_total_days()]": it stores today’s day number so a later event can wait with after_days_from_flag:<flag>,<days>. Any other value written in square brackets is rejected.

Refer to your own characters by their exact name (worker_name, has_worker:Mira Storm) and image folder (has_folder_worker:mira_storm, specific_worker_images). If the game has to rename a pack character because the name is already taken, the installer updates these references for you.

Items, buildings, interactions and monthly conditions cannot go into a character pack. Create them in a JSON override or manual PC project. A complete example pack (Mira) is published in user_docs/templates/character_pack.

Minimal example: a two-step chain for the pack character Mira Storm. The first event fires once she works for you; its choice sets a flag and a day stamp; the second event waits three days after the first.

```json
[
  {
    "id": "mira_storm_first_visit",
    "description": "Mira Storm waits by the door, rain still dripping from her cloak.",
    "worker_name": "Mira Storm",
    "worker_selection": "random",
    "weight": 5,
    "excluded_flags": {"mira_storm_met": true},
    "conditions": {"start_when": "has_worker:Mira Storm"},
    "choices": [
      {
        "option": "Offer her a seat by the fire",
        "message": "She smiles for the first time since she arrived.",
        "effect": {"event_flags": {"mira_storm_met": true, "mira_storm_met_at": "[calculate_total_days()]"}}
      }
    ]
  },
  {
    "id": "mira_storm_second_visit",
    "description": "Three days later, Mira Storm brings you a small gift.",
    "worker_name": "Mira Storm",
    "worker_selection": "random",
    "weight": 5,
    "required_flags": {"mira_storm_met": true},
    "excluded_flags": {"mira_storm_thanked": true},
    "conditions": {"start_when": "has_worker:Mira Storm AND after_days_from_flag:mira_storm_met_at,3"},
    "choices": [
      {
        "option": "Thank her",
        "message": "Mira Storm nods, pleased.",
        "effect": {"event_flags": {"mira_storm_thanked": true}}
      }
    ]
  }
]
```

## Make your first character pack

1. Choose Character pack and enter a mod name.
2. Open Unique Worker, complete the assistant, then choose Save to project. Use a plain-text character name. The image folder is a short identifier using letters, numbers, underscores or hyphens, such as mira_storm.
3. Open Manage character images. Choose portrait adds the selected picture as profile.png, profile.jpg or profile.webp in the correct folder. Add other images keeps their filenames. Use PNG, JPG or WebP; each file must be at most 32 MB.
4. Use the game’s normal image names for other pictures, such as rest.png. A portrait is required for every image folder, even if that folder already exists in your PC installation. GIF and WebM are not included by the character-pack importer.
5. Add more workers as needed. Character names must be unique across the pack. Characters sharing an image folder can share its pictures.
6. Save draft, then Review & export ZIP. Fix every error and review warnings. Export ZIP creates the installable pack.



## Example: change an ingredient price

1. Start an empty project and select JSON override (experimental). Read the notice.
2. Under Items, choose Edit existing…, then data/items/alchemy_ingredients.json.
3. Choose Ironroot (alchemy_ironroot) and change its price in the editor. Save draft to project.
4. Review the project. The ZIP will contain the complete ingredient catalog with your price change; the other ingredients remain in it.
5. Save draft and export the ZIP. Install it in the game with JSON override enabled, restart the game and start a new game.

An assistant can also add a new entry to an existing catalog: select the original target file when asked. It cannot create a new override filename. If the identifier already exists, the devkit asks before replacing that entry in the project copy.

For a daily story, edit the corresponding file under data/buildings/daily_story_extensions. Editing only a building file may not change a story applied later by an extension.

## Install on PC or Android

1. Transfer the exported ZIP to the device, or download it there. Keep the ZIP intact.
2. Open the game’s main menu → Mods → Install mods.
3. For a character pack, leave JSON override off. For an override ZIP, enable it and accept the notice.
4. Select the ZIP, inspect the preview and install. Restart the game to apply the change.
5. For overrides, start a new game and keep the same packs installed for the whole playthrough. Use the Mods list and Uninstall to remove a pack, then restart.

Android uses its normal file picker to read the ZIP and copies supported files into the game’s managed storage. You do not open, unpack or modify the APK. You need a game build that includes the Mods ZIP importer; the older APK may not have every feature of the game version used by this devkit.

Removing a mod does not undo changes already stored in a save. If two overrides replace the same file, the later-installed pack wins for that whole file. The devkit does not merge separate packs or resolve their dependencies.

## Continue editing and update for a new game version

Open draft restores the project, including attached pictures. The draft must match the selected game reference. For a new game version, port your changes into a fresh project made from the new original catalogs; do not blindly reuse old complete-file overrides.

Read PC game reference optionally reads a PC installation with read access only. Start an empty project before changing the reference. It reads the installation’s data files; it does not inspect managed packs in the saves folder or inside an APK.

New entries in the project immediately update the editor’s reference lists. Renaming an ID or name does not rewrite references elsewhere: check dependent events, jobs and conditions yourself.

Remove from project removes the draft file from the exported pack and leaves the original game unchanged. To undo an entry edit after saving it to the project, reopen an earlier saved draft or remove the draft file and start again from the original catalog.

## Whoremaster and advanced PC tools

The Whoremaster importer uses a compatible desktop browser to read the source folder, convert worker data and copy/rename pictures into the project. Review its log for skipped characters or images, then review the pack. In Character pack mode, map unknown traits to existing traits or skip them; new trait definitions need a separate supported project.

The GIF → WebM tool is a separate PC file conversion tool. It writes converted files beside the selected GIFs and downloads its converter on first use. Its WebM output is for manual PC use, not for the current managed character importer.

Manual PC installation of a Manual JSON files ZIP: back up the game and saves, unpack the ZIP into a separate folder, inspect the files inside its game folder, then drag the game folder onto the game’s main folder. Files with matching paths replace existing files. Start a new game for testing. Managed Mods → Uninstall cannot remove files installed by hand; README.txt lists the files to delete.

## Understand the checks and common errors

Missing portrait: add a portrait in Manage character images. Invalid folder: use only letters, numbers, underscores or hyphens and keep it under 81 characters. Duplicate worker: use a different name or edit the existing project entry.

Unknown override target: use Edit existing and select an original file from this game version. Different game reference: open the draft with its original reference or port the changes to a fresh project. Unsupported fields: remove fields unavailable in the chosen pack mode, or use an appropriate override/manual project.

An invalid JSON file, duplicate key, invalid number or failed read is reported instead of being treated as an empty file. The devkit does not save over that source. Drafts may be incomplete; export is blocked until the whole pack passes validation.

The devkit supports up to 1,000 characters, 10,000 files and 128 MB of unpacked content per project. JSON files must fit the importer’s 4 MB limit. Split large projects into smaller packs. Pictures are stored in editable drafts, so draft files are larger than the pictures alone.

Passing validation or the installer’s preview confirms format compatibility, not every possible gameplay outcome. Test new events from beginning to end, including choices and failure branches, in a fresh game before sharing a mod. Keep your editable draft and a backup of the game used for testing.

Overrides of nameless monster templates and catalogs with SFW/NSFW variants of the same worker (Kar/Kara) require the game-side identity fix included with this devkit update. Older APKs may reject those catalogs; regular character packs and the other existing-file overrides still use the previously supported format.
