# Fantasy Manager Devkit — User guide

## Create and install mods

The devkit edits a separate project. It never writes to your original game files. The bundled reference includes the game version shown at the top of the page; you can create a pack without selecting a game folder.

Save draft downloads an editable .fmproject.json file containing your project and pictures. Open draft restores that file. Export ZIP produces the pack players install. A ZIP is not an editable project backup. Save form changes to the project before saving a draft; keep the draft before closing or refreshing the browser.

## Choose the right project mode

Character pack adds regular named characters and their images. It supports the in-game installer on PC and Android. Procedural templates, monsters, custom traits, recruitment-only logic and custom events are outside this mode.

JSON override (experimental) starts from existing game files. Each file in the exported ZIP replaces that complete original file, at the same data/... path. Other entries and unknown fields in the copied file are retained when you edit one entry. Images, scripts and Interactions are not imported in this mode.

Manual JSON files (PC only) keeps the advanced authoring tools for content outside the managed importer. Its ZIP is for manual installation into a backed-up PC game. Do not select this mode for the Android Mods installer.

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

Manual PC installation: back up the game and saves, unpack the manual ZIP into a separate folder, inspect its data/... and images/... paths, then copy only the intended files into the game folder. Files with matching paths replace existing files. Start a new game for testing. Managed Mods → Uninstall cannot remove files installed by hand.

## Understand the checks and common errors

Missing portrait: add a portrait in Manage character images. Invalid folder: use only letters, numbers, underscores or hyphens and keep it under 81 characters. Duplicate worker: use a different name or edit the existing project entry.

Unknown override target: use Edit existing and select an original file from this game version. Different game reference: open the draft with its original reference or port the changes to a fresh project. Unsupported fields: remove fields unavailable in the chosen pack mode, or use an appropriate override/manual project.

An invalid JSON file, duplicate key, invalid number or failed read is reported instead of being treated as an empty file. The devkit does not save over that source. Drafts may be incomplete; export is blocked until the whole pack passes validation.

The devkit supports up to 1,000 characters, 10,000 files and 128 MB of unpacked content per project. JSON files must fit the importer’s 4 MB limit. Split large projects into smaller packs. Pictures are stored in editable drafts, so draft files are larger than the pictures alone.

Passing validation or the installer’s preview confirms format compatibility, not every possible gameplay outcome. Test new events from beginning to end, including choices and failure branches, in a fresh game before sharing a mod. Keep your editable draft and a backup of the game used for testing.

Overrides of nameless monster templates and catalogs with SFW/NSFW variants of the same worker (Kar/Kara) require the game-side identity fix included with this devkit update. Older APKs may reject those catalogs; regular character packs and the other existing-file overrides still use the previously supported format.
