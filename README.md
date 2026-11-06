# Chatferry

Move WhatsApp chats from an **Android phone** to an **iPhone that is already set up**, on a Mac, without erasing the iPhone. It has a point-and-click interface, so you don't need to type commands for each step.

> [!WARNING]
> **Experimental.** It edits WhatsApp's database inside an iPhone backup and restores the whole backup to the phone. Both are undocumented and unsupported by WhatsApp or Apple. It has been tested on one iPhone (iPhone 13 Pro Max, iOS 27) with one Android export. Keep the Android phone and its backup. Keep two archived Finder backups of the iPhone. A restore can take hours.

Chatferry is a fork of [alicin/wamove](https://github.com/alicin/wamove) (GPL-3.0). Credit for the original Android decryption, database conversion and device code goes to its author.

## What this fork changes, and why

The original builds a **WhatsApp-only** backup and restores it. On a recent iPhone that restore is treated as a whole-device restore, and **photos, hidden photos and local files were lost** in testing. Chatferry fixes that:

1. **Complete backup.** Nothing is stripped from the backup. Only WhatsApp's chat database changes. `chatferry check` proves this (nothing removed, nothing changed outside WhatsApp, every file present) before you restore.
2. **Media paths.** On newer iOS versions WhatsApp lives in `data/<UUID>/`. Media written to the old top-level path showed as broken images, audio and video. Files are now written inside that container.
3. **Messages first.** Media is off by default in the interface (`--no-media`). Messages are the safe part. Media is less tested, so try it separately.
4. **A local web interface.** `chatferry ui` opens a page on your own Mac. Nothing is uploaded and it listens on 127.0.0.1 only.

## Requirements

A Mac with Xcode Command Line Tools, [uv](https://docs.astral.sh/uv/) (`brew install uv`), `adb` (`brew install --cask android-platform-tools`), a USB cable for each phone, and free disk space for a full iPhone backup. WhatsApp (not Business) on both phones with the same number.

## Install and start

```sh
uv tool install --python 3.13 git+https://github.com/thescarcerebel/chatferry.git
chatferry ui
```

## Before you start (do not skip)

1. In **Finder**, back up the iPhone and **archive** that backup (Manage Backups, right-click, Archive). Finder overwrites the previous backup otherwise. Keep two.
2. Turn **Find My** off on the iPhone for the restore, and Airplane mode on during it.
3. On Android: WhatsApp, Settings, Chats, Chat backup, End-to-end encrypted backup, **Use 64-digit key**. Save the key, tap **Back up**, and turn on USB debugging.
4. On the iPhone: install WhatsApp, register the same number, and skip restoring from iCloud.

## Steps (also buttons in the interface)

```sh
chatferry doctor     # check phones and disk space
chatferry pull       # chat backup (media too unless --no-media)
chatferry decrypt    # asks for the 64-digit key
chatferry backup     # COMPLETE iPhone backup (large and slow)
chatferry build      # add Android chats to a copy of that backup
chatferry check      # must print "OK: only WhatsApp's data differs"
chatferry restore    # FULL restore: plugged in, unlocked, Mac awake
chatferry rollback   # restore the untouched backup
```

The restore reboots the iPhone into its setup screens. Sign in again and **never choose Erase**. Then check Photos (including Hidden), Files and your apps before opening WhatsApp. If anything is missing, restore your archived Finder backup from Finder.

If the iPhone backup is encrypted, Chatferry asks for its password. It is typed locally and never stored.

## Known limits

- Not proven across iOS versions or large group chats. Group history may not appear.
- Notes and other iCloud data sync back from iCloud after the restore. That's normal.
- Media-only messages are skipped when media is off.
- Use at your own risk. See `LICENSE` (GPL-3.0). Not affiliated with WhatsApp, Meta or Apple.
