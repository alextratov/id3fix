#!/usr/bin/env python3
"""
Fix malformed or non-UTF-8 ID3 tags to UTF-8 in MP3 files
"""
import codecs
import os
import sys
import argparse
import unicodedata
from pathlib import Path
from mutagen.id3 import ID3

def text_quality_score(text):
    score = 0
    for ch in text:
        if ch == '�':
            score -= 10
            continue

        category = unicodedata.category(ch)
        if category.startswith('C'):
            score -= 5
        elif ch.isalpha():
            score += 2
        elif ch.isdigit() or ch.isspace():
            score += 1
        elif category.startswith(('P', 'S')):
            score += 1
        elif ord(ch) >= 0x80:
            score += 1
        else:
            score += 1
    return score


def contains_cyrillic(text):
    for ch in text:
        try:
            if 'CYRILLIC' in unicodedata.name(ch):
                return True
        except ValueError:
            continue
    return False


def looks_like_cp1251_mojibake(text):
    if len(text) < 6:
        return False
    marker_chars = set('РСТНМБПДВКЗШАЮЫАОЭЯЁ')
    marker_count = sum(1 for ch in text if ch in marker_chars)
    return marker_count >= max(3, len(text) * 0.2)


MOJIBAKE_REPAIR_CANDIDATES = [
    ('latin-1', 'cp1251'),
    ('cp1252', 'cp1251'),
    ('latin-1', 'cp1252'),
    ('cp1251', 'cp1252'),
    ('latin-1', 'utf-8'),
    ('cp1252', 'utf-8'),
    ('cp1251', 'utf-8'),
    ('latin-1', 'koi8-r'),
    ('latin-1', 'koi8-u'),
    ('latin-1', 'cp866'),
]


_SINGLE_BYTE_REVERSE_CACHE = {}

def reverse_single_byte_encoding(text, encoding):
    if encoding not in _SINGLE_BYTE_REVERSE_CACHE:
        decode_table = bytes(range(256)).decode(encoding, errors='replace')
        reverse_map = {}
        for i, ch in enumerate(decode_table):
            if ch not in reverse_map:
                reverse_map[ch] = i
        _SINGLE_BYTE_REVERSE_CACHE[encoding] = reverse_map

    reverse_map = _SINGLE_BYTE_REVERSE_CACHE[encoding]
    encoded_bytes = bytearray()
    for ch in text:
        if ch in reverse_map:
            encoded_bytes.append(reverse_map[ch])
        else:
            # Preserve unknown characters as question mark bytes.
            encoded_bytes.append(0x3f)
    return bytes(encoded_bytes)


def encode_text(text, encoding):
    try:
        return text.encode(encoding)
    except UnicodeEncodeError:
        try:
            return reverse_single_byte_encoding(text, encoding)
        except LookupError:
            encoder = codecs.getencoder(encoding)
            encoded, _ = encoder(text, 'replace')
            return encoded


def repair_mojibake_text(text):
    if not text or text.isascii():
        return None

    original_score = text_quality_score(text)
    best_text = text
    best_score = original_score

    for source_enc, target_enc in MOJIBAKE_REPAIR_CANDIDATES:
        try:
            candidate = encode_text(text, source_enc).decode(target_enc)
        except (UnicodeEncodeError, UnicodeDecodeError, LookupError):
            continue

        candidate_score = text_quality_score(candidate)
        if candidate_score > best_score:
            best_text = candidate
            best_score = candidate_score

        # If the text clearly looks like cp1251 mojibake, prefer the cp1251->utf-8 repair.
        if source_enc == 'cp1251' and target_enc == 'utf-8' and contains_cyrillic(candidate):
            return candidate

    if best_text != text and best_score >= original_score + 3:
        return best_text
    return None


def fix_encoding(filepath):
    """Convert malformed ID3 tags to UTF-8 in a single MP3 file"""
    try:
        tags = ID3(filepath)
        modified = False

        for frame_id, frame in list(tags.items()):
            if not hasattr(frame, 'text'):
                continue

            frame_modified = False
            for i, text_value in enumerate(frame.text):
                text_str = str(text_value)
                repaired_text = repair_mojibake_text(text_str)

                if repaired_text is not None:
                    frame.text[i] = repaired_text
                    frame_modified = True

            if frame_modified:
                modified = True

            if hasattr(frame, 'encoding') and getattr(frame, 'encoding', None) != 3:
                try:
                    frame.encoding = 3
                    modified = True
                except Exception:
                    pass

        if modified:
            tags.save()
            return True, "Fixed"
        return True, "No changes needed"

    except Exception as e:
        return False, str(e)

def main():
    parser = argparse.ArgumentParser(
        description='Fix malformed or non-UTF-8 ID3 tags and normalize them to UTF-8 in MP3 files',
        epilog='Examples:\n  id3fix.py -f song.mp3\n  id3fix.py -f track1.mp3 track2.mp3 track3.mp3',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '-f', '--files',
        nargs='*',
        metavar='FILE',
        help='MP3 file(s) to process'
    )
    
    args = parser.parse_args()
    
    # Show help if no files provided
    if not args.files:
        parser.print_help()
        sys.exit(0)
    
    files = args.files
    fixed_count = 0
    error_count = 0
    
    for filename in files:
        filepath = Path(os.path.expanduser(filename))
        
        if not filepath.exists():
            print(f"✗ {filepath}: does not exist")
            error_count += 1
            continue
        
        if not filepath.suffix.lower() == '.mp3':
            print(f"✗ {filepath}: not an MP3 file")
            error_count += 1
            continue
        
        success, msg = fix_encoding(str(filepath))

        if success:
            if msg == "Fixed":
                print(f"✓ {filepath.name}")
                fixed_count += 1
            else:
                print(f"• {filepath.name}: {msg}")
        else:
            print(f"✗ {filepath.name}: {msg}")
            error_count += 1
    
    if len(files) > 1:
        print(f"\nSummary: {fixed_count} fixed, {error_count} errors")

if __name__ == "__main__":
    main()
