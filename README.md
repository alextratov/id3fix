# id3fix

A small utility to repair malformed ID3 tags in MP3 files and normalize text frames to UTF-8.

## Files

- `id3fix.py` — repairs mojibake or non-UTF-8 ID3 text tags in one or more MP3 files and writes UTF-8 text frames.
- `id3batch.sh` — recursively finds MP3 files in a directory and runs `id3fix.py` on each one.

## Requirements

- Python 3
- `mutagen` Python package

Install `mutagen` with:

```bash
pip install mutagen
```

## `id3fix.py`

This script reads ID3 tags from MP3 files and normalizes all text frames to UTF-8.

### Usage

```bash
./id3fix.py -f file1.mp3 file2.mp3
```

### Options

- `-f, --files` — one or more MP3 file paths to process.

### Behavior

- Repairs mojibake encodings CP1251.

## `id3batch.sh`

This shell helper recursively searches a directory for `.mp3` files and passes each file to `id3fix.py`.

### Usage

```bash
./id3batch.sh /path/to/directory
```