# Audio Download Manager - User Guide

Audio Download Manager is a small program that downloads radio show audio
files from several websites and saves them into organized folders on your
computer. It does the clicking, waiting, and filing-away for you so you
don't have to.

This guide explains everything in plain language. If you can send an email,
you can use this program.

---

## Table of Contents

1. [What This Program Does](#what-this-program-does)
2. [What You Need Before You Start](#what-you-need-before-you-start)
3. [First-Time Setup (Important)](#first-time-setup-important)
4. [The Main Screen - Every Button Explained](#the-main-screen---every-button-explained)
5. [The Download Log](#the-download-log)
6. [Where Your Files Go](#where-your-files-go)
7. [Automatic Scheduled Downloads](#automatic-scheduled-downloads)
8. [Troubleshooting](#troubleshooting)

---

## What This Program Does

The program downloads audio files from five different sources, each one a
radio show or feature:

| Source | What it is | How it downloads |
|--------|-----------|------------------|
| **Melinda Myers** | Short gardening tips (one for each weekday) | From the Melinda Myers website |
| **Northwest Outdoors** | A weekly outdoor radio show | From a Dropbox shared link (a ZIP file) |
| **Whittler** | A radio show split into four parts | From a Dropbox shared link (a ZIP file) |
| **Clear Out West** | A radio show with several tracks | From the Clear Out West website (needs a password) |
| **Weekend In The Country** | A radio show with segments and a promo | From an FTP server (needs a username and password) |

The program opens a hidden Firefox web browser in the background, visits each
website, clicks the download buttons, waits for the files to finish, then
renames and sorts them into the right folders. You don't have to click
anything on the websites yourself.

There is also a special **Download Promo** button that downloads just the
promo file from Northwest Outdoors and adds a short audio "tag" (like a
station jingle) onto the end of it.

---

## What You Need Before You Start

These are one-time things to set up. Once done, you usually never have to
touch them again.

### 1. Firefox web browser

The program uses Firefox to visit the download websites. If you don't
already have Firefox installed, download it for free from
https://www.mozilla.org/firefox/ and install it normally.

You do **not** need to open Firefox yourself. The program opens it
automatically when needed and closes it when finished.

### 2. FFmpeg (only needed for the promo tag)

The "Download Promo" feature uses a free tool called FFmpeg to blend a short
jingle onto the end of the promo audio. If you never use Download Promo, you
can skip this.

If you do want the promo tag feature, FFmpeg must be installed on your
computer and available on your system PATH. Ask whoever set up your computer
to install it, or follow a guide for "installing FFmpeg on Windows." If it
is missing, the promo will still download fine, just without the tag added.

### 3. Your account details handy

You will need:

- The **Clear Out West password** (for the Clear Out West source)
- The **Weekend In The Country FTP server address, username, and password**
- The **Dropbox shared links** for Northwest Outdoors and Whittler (these
  look like `https://www.dropbox.com/scl/fo/...`)

If you don't have these, the program will tell you which ones are missing
when you try to download.

---

## First-Time Setup (Important)

The very first time you run the program, you should check your settings.
This only takes a minute and makes sure everything downloads to the right
place.

1. Open the program (double-click `AudioDownloader.exe`).
2. Look at the top-right corner of the window. You will see a small
   **gear icon** (it looks like this: a little wheel). Click it.
3. A **Settings** window opens with four tabs across the top:
   **General**, **Paths**, **Auth**, and **URLs**.

Go through each tab below.

### General tab

This tab controls where files are saved and how the program behaves.

- **Output Directory** - This is the main folder where all your downloaded
  audio ends up. Inside this folder, the program creates two sub-folders
  automatically: one called "Global Features" and one called "Promos" (see
  [Where Your Files Go](#where-your-files-go) below). You can type a folder
  path here, or click the **Browse** button next to it to pick a folder
  using the normal folder picker. The default is a folder called
  `downloads` next to the program itself.

- **Auto-close browser after downloads** - A small box you can check or
  uncheck. When checked (the default), the program closes the hidden
  Firefox browser automatically when a download finishes. Leave this
  checked unless you have a reason not to. If you uncheck it, Firefox
  stays open in the background after each download and you would have to
  close it yourself.

- **Retry Attempts** - A number from 0 to 5. This tells the program how many
  extra times to try again if a download fails (for example, if a website
  is slow or temporarily down). The default is 2, which means it tries up
  to 3 times total (the first try plus 2 retries). If your internet is
  unreliable, you might raise this to 3 or 4. Setting it to 0 means it
  only tries once with no retries.

### Paths tab

This tab is for special file locations. Most people can leave these alone,
but here is what each one means.

- **Tag File** - This is the short audio jingle file (a `.wav` file) that
  gets blended onto the end of the Northwest Outdoors promo. If you leave
  this blank, the program looks for a file called `NWKORVTAG.wav` inside
  your Promos folder. If you have your tag file somewhere else, click the
  **...** button to find and select it. Only needed if you use the
  Download Promo button.

- **Browser Download Dir** - This is a temporary "holding" folder where
  Firefox saves files *while* they are downloading, before the program
  moves them to their final home. You normally never look in this folder.
  The default is a folder called `browser_downloads` next to the program.
  You can change it with the **Browse** button if needed, but there is
  rarely a reason to.

### Auth tab

This tab holds your passwords and login details. These are stored only on
your own computer in a settings file next to the program. They are never
sent anywhere except to the websites they belong to.

- **Clear Out West Password** - The password for the Clear Out West
  website. Type it in. It will show as dots (hidden) so nobody can read
  it over your shoulder. Without this, the Clear Out West download will
  not work.

- **WITC FTP Server** - The server address for Weekend In The Country
  (for example, `ftp.example.com`). Get this from the show provider.

- **WITC FTP Username** - The username for the Weekend In The Country FTP
  server.

- **WITC FTP Password** - The password for the Weekend In The Country FTP
  server. Shows as dots.

If you don't use the Weekend In The Country source, you can leave its three
fields blank. But if you ever click that download button, it will fail
until you fill them in.

### URLs tab

This tab holds the Dropbox shared links for two of the sources.

- **Northwest Outdoors** - Paste the Dropbox shared link for Northwest
  Outdoors here. It should look like
  `https://www.dropbox.com/scl/fo/...`. Get this link from the show
  provider. If this still says `YOUR_LINK_HERE`, the Northwest Outdoors
  download will not work.

- **Whittler** - Paste the Dropbox shared link for Whittler here, the same
  way. If it still says `YOUR_LINK_HERE`, the Whittler download will not
  work.

### Saving your settings

When you are done with all four tabs, click the **Save** button at the
bottom. You will see a small message saying "Settings saved successfully!"
Click OK, and the settings window closes.

If you change your mind and don't want to save, click **Cancel** instead
and nothing will be changed.

---

## The Main Screen - Every Button Explained

When you open the program, you see the main window. From top to bottom:

### The gear icon (top-right corner)

This opens the Settings window described above. You can change your
settings any time, even in the middle of downloads.

### "Download Global Features" button

This is the big button near the top. Click it to download **all five
sources one after another**: Melinda Myers, Northwest Outdoors, Whittler,
Clear Out West, and Weekend In The Country. The program goes through them
in order. You will see the progress bar move and the status text change as
each one starts and finishes.

When everything is done, a small summary window pops up telling you how
many succeeded and listing any that failed. Click **OK** to close it.

This is the button you will use most often. It does the whole week's
downloads in one go.

### "Download Promo" button

This downloads **only** the Northwest Outdoors promo file and adds the
audio tag (jingle) onto the end of it. Use this when you only need the
promo, not the full shows. It is a separate button because promos are
usually needed on a different day than the full shows.

Note: This needs the Tag File setting (see the Paths tab above) and FFmpeg
installed. If either is missing, the promo still downloads but without the
tag.

### "Downloads:" section

Below the two big buttons, you see a label "Downloads:" and then a list of
five buttons, one for each source:

- **Melinda Myers** - Downloads only the Melinda Myers gardening tips.
- **Northwest Outdoors** - Downloads only the Northwest Outdoors show
  (the full show files, not the promo).
- **Whittler** - Downloads only the Whittler show.
- **Clear Out West** - Downloads only the Clear Out West show.
- **Weekend In The Country** - Downloads only the Weekend In The Country
  show.

Use these when you only want one specific show instead of all of them.
Clicking one of these does exactly the same thing as the big "Download
Global Features" button, but for just that one source.

### Progress bar

The thin blue bar below the buttons fills up from left to right as a
download progresses. When it reaches the right side, the download is done.
It resets to empty a couple of seconds after each download finishes.

### Status text

Just below the progress bar, a line of text tells you what is happening
right now, for example "Downloading Monday..." or "Done - Melinda Myers
completed!" or "FAIL - Whittler failed." This is your quick at-a-glance
status.

---

## The Download Log

The big box at the bottom labeled "Download Log" shows a running list of
everything the program is doing, with a time stamp on each line. It
scrolls automatically so the newest message is always visible.

You don't need to read this normally. It is there so that if something
goes wrong, you (or whoever helps you) can look back and see exactly what
happened and when.

If a download fails, the log will usually say why, for example "Error:
cow_password not configured" or "No downloaded file found after waiting."

---

## Where Your Files Go

All your finished audio files end up inside the **Output Directory** you
set in the General settings tab. Inside it, the program creates two
sub-folders automatically:

```
Your Output Directory/
    Global Features/
        MMMON.mp3        (Melinda Myers - Monday)
        MMWED.mp3        (Melinda Myers - Wednesday)
        MMFRI.mp3        (Melinda Myers - Friday)
        MMTUE.mp3        (Melinda Myers - Tuesday)
        MMTHU.mp3        (Melinda Myers - Thursday)
        Whittler1.mp3    (Whittler - Part A)
        Whittler2.mp3    (Whittler - Part B)
        Whittler3.mp3    (Whittler - Part C)
        Whittler4.mp3    (Whittler - Part D)
        COW1.mp3 ...     (Clear Out West tracks)
        COWPROMO.mp3      (Clear Out West promo track)
        WITC_HR1_PT1.mp3  (Weekend In The Country - Hour 1, Part 1)
        WITC_PROMO.mp3    (Weekend In The Country promo)
        ...and the Northwest Outdoors show files
    Promos/
        ...the Northwest Outdoors promo file (with tag added)
```

- **Global Features** holds all the full show files and regular features.
- **Promos** holds promo files, including the Northwest Outdoors promo
  with the tag blended onto the end.

The program renames the files automatically so they always have
consistent, predictable names. You never have to rename anything yourself.

---

## Automatic Scheduled Downloads

If you want the program to run by itself on a schedule (so you don't have
to remember), there are two ready-made files included:

- **`download_global_features.bat`** - Runs "Download Global Features"
  (all five sources). Meant to be scheduled for **Thursdays at 11:00 PM**.
- **`download_promos.bat`** - Runs "Download Promo" only. Meant to be
  scheduled for **Tuesdays at 11:00 PM**.

These are small files that simply tell the program to run in automatic
mode without opening the window.

To set up the schedule on Windows, you use a built-in tool called **Task
Scheduler**. This is a bit more technical, so you may want to ask whoever
helps you with your computer to set it up. Once it is set up, the program
will download everything by itself overnight on the right days, and the
files will be waiting for you in the morning.

If you prefer, you can skip the schedule entirely and just click the
buttons yourself whenever you want.

---

## Troubleshooting

### A download says "FAIL"

Look at the Download Log for the reason. The most common causes:

- **"cow_password not configured"** - You haven't set the Clear Out West
  password in the Auth settings tab. Open Settings, go to the Auth tab,
  type it in, and Save.
- **"FTP credentials not configured"** - You haven't filled in the
  Weekend In The Country server, username, and password in the Auth tab.
- **"URL not configured"** - The Dropbox link for Northwest Outdoors or
  Whittler still says `YOUR_LINK_HERE`. Paste the real link in the URLs
  tab.
- **"No downloaded file found after waiting"** - The website was slow or
  the file didn't arrive in time. Try again. If it keeps happening, check
  your internet connection.

### The program seems stuck

Downloads can take a few minutes, especially the ZIP files from Dropbox.
The progress bar and status text should keep moving. If nothing changes
for several minutes, close the program and try again. The program
automatically retries failed downloads up to the number you set in Retry
Attempts.

### A Firefox window appeared and won't go away

If you unchecked "Auto-close browser after downloads" in the General
settings, Firefox stays open after downloads finish. Either close it
yourself, or re-check that box in Settings so the program closes it
automatically.

### The promo downloaded but has no tag

This means either FFmpeg is not installed on your computer, or the Tag
File setting points to a file that doesn't exist. Check the Paths tab in
Settings and make sure FFmpeg is installed (see
[What You Need Before You Start](#what-you-need-before-you-start)).

### I changed settings but nothing changed

Make sure you clicked the **Save** button at the bottom of the Settings
window. If you clicked Cancel or closed the window with the X, your
changes were not saved.

### Where is my settings file?

All your settings are saved in a file called `download_config.json` that
sits next to the program. You never need to open it yourself, but it is
there if you ever need to back it up or copy it to another computer.

---

If you get stuck and this guide doesn't answer your question, ask whoever
set up the program for you, and show them the Download Log, which will
help them figure out what went wrong.