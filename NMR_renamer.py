import os
import re
import shutil
from pathlib import Path

def process_folders(src_dir, dest_dir):
    src_path = Path(src_dir)
    dest_path = Path(dest_dir)
    
    # Create destination directory if it doesn't exist
    dest_path.mkdir(parents=True, exist_ok=True)
    
    # Regex 1: Matches folder names directly (e.g., 4_ald_17_am OR 4_ald_17am)
    # The `_?` makes the underscore before 'am' optional.
    pattern_folder = re.compile(r'^(\d+)_ald_(\d+)_?am$')
    
    # Regex 2: Matches "am[number]ald[number]" in text file (e.g., am4ald17)
    pattern_am_ald = re.compile(r'^am(\d+)ald(\d+)$')
    
    # Regex 3: Matches "[number]_[number]" in text file (e.g., 4_17)
    pattern_num_num = re.compile(r'^(\d+)_(\d+)$')
    
    for folder in src_path.iterdir():
        if not folder.is_dir():
            continue
        
        # --- Logic Step 1: Check Folder Name (Fastest) ---
        # Checks for "4_ald_17_am" OR "4_ald_17am"
        folder_match = pattern_folder.match(folder.name)
        
        new_folder_name = None
        parent_dir = None
        
        if folder_match:
            # Extract numbers from folder name
            # Note: Input is [ald] first, [am] second
            ald_num = folder_match.group(1)
            am_num = folder_match.group(2)
            
            # FLIP: Output is [am] first, [ald] second
            new_folder_name = f"{am_num}_am_{ald_num}_ald"
            parent_dir = dest_path / f"Block_{am_num}"
            
        else:
            # --- Logic Step 2: Check File Content (Slower) ---
            text_file = folder / 'PRESAT_01.fid' / 'text'
            
            if not text_file.exists():
                print(f"Skipping '{folder.name}': Text file missing and folder name format unrecognized.")
                continue
                
            try:
                with open(text_file, 'r', encoding='utf-8') as f:
                    content = f.readline().strip()
                    # Extract 4th item (index 3), remove quotes
                    raw_var_name = content.split(':')[3].replace('"', '').strip()
            except (IndexError, ValueError, FileNotFoundError):
                print(f"Skipping '{folder.name}': Error reading text file.")
                continue

            match_am = pattern_am_ald.match(raw_var_name)
            match_num = pattern_num_num.match(raw_var_name)
            
            if match_am:
                # Format: am4ald17 -> 4_am_17_ald
                am_num = match_am.group(1)
                ald_num = match_am.group(2)
                new_folder_name = f"{am_num}_am_{ald_num}_ald"
                parent_dir = dest_path / f"Block_{am_num}"
                
            elif match_num:
                # Format: 4_17 -> 4_am_17_ald
                am_num = match_num.group(1)
                ald_num = match_num.group(2)
                new_folder_name = f"{am_num}_am_{ald_num}_ald"
                parent_dir = dest_path / f"Block_{am_num}"
                
            else:
                # Fallback: Use raw name, put in Unsorted
                new_folder_name = raw_var_name
                parent_dir = dest_path / "Unsorted"
            
        # --- Logic Step 3: Copy Data ---
        
        # Ensure the Block_X or Unsorted folder exists
        parent_dir.mkdir(parents=True, exist_ok=True)
            
        dest_folder = parent_dir / new_folder_name
        
        # Check for duplicates (e.g., if you have two experiments with same params)
        counter = 1
        while dest_folder.exists():
            dest_folder = parent_dir / f"{new_folder_name}_{counter}"
            counter += 1
            
        # Logging for user verification
        try:
            display_path = dest_folder.relative_to(dest_path.parent)
        except ValueError:
            display_path = dest_folder.name
            
        print(f"Copying '{folder.name}' -> '{display_path}'")
        shutil.copytree(folder, dest_folder)

    print("\nBatch processing complete!")

if __name__ == "__main__":
    process_folders('data/raw', 'data/processed')