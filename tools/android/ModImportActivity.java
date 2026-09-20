package org.fantasymanager.mods;

import android.app.Activity;
import android.app.ProgressDialog;
import android.content.Intent;
import android.database.Cursor;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.provider.OpenableColumns;
import org.json.JSONObject;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;

/** SAF bridge. Own activity also isolates nullable results from older Ren'Py SDKs. */
public final class ModImportActivity extends Activity {
    private static final int PICK_ZIP = 4172;
    private static final long MAX_BYTES = 1024L * 1024L * 1024L;
    private static String status = "idle", path = "", message = "";
    private static long copied = 0, generation = 0;
    private static File staged;
    private long request;
    private ProgressDialog progress;

    public static synchronized String poll() {
        try {
            return new JSONObject().put("status", status).put("path", path)
                .put("message", message).put("bytes", copied).toString();
        } catch (Exception e) { return "{\"status\":\"error\",\"message\":\"Picker state unavailable.\"}"; }
    }

    public static synchronized boolean open(final Activity parent) {
        if (status.equals("picking") || status.equals("copying")) return false;
        discard();
        // A previous process may have died during copying. Only our private, flat
        // staging directories are eligible for cleanup; no document URI is deleted.
        File root = new File(parent.getCacheDir(), "fm-mod-import");
        File[] oldDirs = root.listFiles();
        if (oldDirs != null) for (File dir : oldDirs) {
            if (!dir.getName().matches("[0-9a-f-]{36}")) continue;
            File[] files = dir.listFiles();
            if (files != null) for (File file : files) if (file.isFile()) file.delete();
            dir.delete();
        }
        status = "picking";
        final long token = generation;
        parent.runOnUiThread(() -> {
            try {
                Intent intent = new Intent(parent, ModImportActivity.class);
                intent.putExtra("generation", token);
                parent.startActivity(intent);
            } catch (Exception e) { complete(token, "error", "Android could not open the file picker."); }
        });
        return true;
    }

    // Deletes only the bridge's own completed temporary ZIP, never a selected document.
    public static synchronized void discard() {
        generation++;
        if (staged != null) {
            staged.delete();
            staged.getParentFile().delete();
        }
        staged = null;
        path = "";
        message = "";
        copied = 0;
        status = "idle";
    }

    private static synchronized void complete(long token, String next, String detail) {
        if (token != generation) return;
        status = next;
        message = detail;
    }

    @Override public void onCreate(Bundle saved) {
        super.onCreate(saved);
        request = getIntent().getLongExtra("generation", -1);
        if (saved != null) {
            synchronized (ModImportActivity.class) {
                if (request != generation) { finish(); return; }
                if (status.equals("copying")) showProgress();
                else if (!status.equals("picking")) finish();
            }
            return; // Android delivers the outstanding result after recreation.
        }
        try {
            Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
            intent.addCategory(Intent.CATEGORY_OPENABLE);
            // Some Downloads providers label ZIPs as octet-stream. Validate the contents in Python.
            intent.setType("*/*");
            intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
            startActivityForResult(intent, PICK_ZIP);
        } catch (Exception e) {
            complete(request, "error", "No document picker is available on this device.");
            finish();
        }
    }

    @Override protected void onActivityResult(int code, int result, Intent data) {
        super.onActivityResult(code, result, data);
        if (code != PICK_ZIP) return;
        if (result != RESULT_OK || data == null || data.getData() == null) {
            complete(request, "cancelled", "Selection cancelled.");
            finish();
        } else {
            final Uri uri = data.getData();
            final long token = request;
            complete(token, "copying", "Copying selected ZIP...");
            showProgress();
            new Thread(() -> copyDocument(uri, token), "FM-Mod-Import").start();
        }
    }

    private void showProgress() {
        progress = new ProgressDialog(this);
        progress.setMessage("Copying selected mod ZIP...");
        progress.setIndeterminate(true);
        progress.setCancelable(true);
        progress.setCanceledOnTouchOutside(false);
        progress.setOnCancelListener(dialog -> { discard(); finish(); });
        progress.show();
        final Handler handler = new Handler(Looper.getMainLooper());
        handler.postDelayed(new Runnable() {
            @Override public void run() {
                if (isFinishing() || isDestroyed()) return;
                synchronized (ModImportActivity.class) {
                    if (request != generation || !status.equals("copying")) { finish(); return; }
                    progress.setMessage(String.format(java.util.Locale.ROOT, "Copying mod ZIP: %.1f MB...", copied / 1048576.0));
                }
                handler.postDelayed(this, 300);
            }
        }, 300);
    }

    @Override protected void onDestroy() {
        if (progress != null && progress.isShowing()) progress.dismiss();
        super.onDestroy();
    }

    private void copyDocument(Uri uri, long token) {
        File file = null, directory = null;
        boolean ready = false;
        try {
            String name = "character-pack.zip";
            // Display names and size are optional, untrusted provider metadata.
            try (Cursor cursor = getContentResolver().query(uri,
                    new String[]{OpenableColumns.DISPLAY_NAME}, null, null, null)) {
                if (cursor != null && cursor.moveToFirst() && !cursor.isNull(0)) name = cursor.getString(0);
            } catch (RuntimeException ignored) { }
            name = name.replaceAll("[^a-zA-Z0-9._ -]", "_");
            if (name.length() > 120) name = name.substring(0, 120);
            if (name.isEmpty() || name.startsWith(".")) name = "character-pack.zip";
            if (!name.toLowerCase(java.util.Locale.ROOT).endsWith(".zip")) name += ".zip";
            File root = new File(getCacheDir(), "fm-mod-import");
            if (!root.isDirectory() && !root.mkdirs()) throw new IOException("Temporary storage unavailable.");
            directory = new File(root, java.util.UUID.randomUUID().toString());
            if (!directory.mkdir()) throw new IOException("Temporary storage unavailable.");
            file = new File(directory, name);
            long total = 0;
            try (InputStream input = getContentResolver().openInputStream(uri);
                 FileOutputStream output = new FileOutputStream(file)) {
                if (input == null) throw new IOException("Cannot read the selected document.");
                byte[] buffer = new byte[65536];
                int count;
                while ((count = input.read(buffer)) != -1) {
                    total += count;
                    if (total > MAX_BYTES) throw new IOException("The selected file exceeds the 1 GB limit.");
                    synchronized (ModImportActivity.class) {
                        if (token != generation) throw new IOException("Import cancelled.");
                        copied = total;
                    }
                    output.write(buffer, 0, count);
                }
            }
            if (total == 0) throw new IOException("The selected document is empty.");
            synchronized (ModImportActivity.class) {
                if (token != generation) return;
                staged = file;
                path = file.getAbsolutePath();
                status = "ready";
                ready = true;
            }
        } catch (Exception e) {
            complete(token, "error", e instanceof IOException ? e.getMessage() : "Could not read this document. Try a ZIP saved in Downloads.");
        } finally {
            if (!ready && file != null) file.delete();
            if (!ready && directory != null) directory.delete();
            // Keep this activity alive until the URI stream closes, retaining its
            // temporary read grant without requesting persistent storage access.
            runOnUiThread(() -> {
                if (progress != null && progress.isShowing()) progress.dismiss();
                finish();
            });
        }
    }
}
