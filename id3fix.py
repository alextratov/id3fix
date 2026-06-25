#!/usr/bin/env python3
"""
Fix CP1251 encoded ID3 tags to UTF-8 in MP3 files
"""
import os
import sys
import argparse
from pathlib import Path
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TRCK, TDRC, COMM

def fix_encoding(filepath):
    """Convert CP1251 ID3 tags to UTF-8 in a single MP3 file"""
    try:
        tags = ID3(filepath)
        modified = False
        
        # Map of ID3 frame types to TextFrame constructors
        text_frames = {
            'TIT2': TIT2,  # Title
            'TPE1': TPE1,  # Artist
            'TPE2': None,  # Album artist (generic)
            'TALB': TALB,  # Album
            'TDRC': TDRC,  # Date
            'TIT3': None,  # Subtitle
            'TPE3': None,  # Conductor
            'TPE4': None,  # Remixer
            'TEXT': None,  # Text writer
            'TCON': None,  # Content type
            'COMM': COMM,  # Comments
        }
        
        for frame_id, frame in list(tags.items()):
            if not hasattr(frame, 'text'):
                continue
                
            # Try to detect and fix UTF-8 mojibake
            for i, text_value in enumerate(frame.text):
                text_str = str(text_value)
                
                # Check if it looks like mojibake (CP1251 interpreted as Latin-1)
                # CP1251 Cyrillic in 0xC0-0xFF range interpreted as Latin-1 display as mojibake
                if any(ord(c) in range(0x00C0, 0x0100) for c in text_str):
                    try:
                        # Encode as Latin-1 (which gives us the raw CP1251 bytes), then decode as CP1251
                        fixed_text = text_str.encode('latin-1').decode('cp1251')
                        frame.text[i] = fixed_text
                        frame.encoding = 3  # UTF-8 encoding
                        modified = True
                    except (UnicodeDecodeError, UnicodeEncodeError):
                        pass
        
        if modified:
            tags.save()
            return True, "Fixed"
        else:
            return False, "Already UTF-8"
            
    except Exception as e:
        return False, str(e)

def main():
    parser = argparse.ArgumentParser(
        description='Fix CP1251 encoded ID3 tags to UTF-8 in MP3 files',
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
            print(f"✓ {filepath.name}")
            fixed_count += 1
        else:
            print(f"✗ {filepath.name}: {msg}")
            error_count += 1
    
    if len(files) > 1:
        print(f"\nSummary: {fixed_count} fixed, {error_count} errors")

if __name__ == "__main__":
    main()
