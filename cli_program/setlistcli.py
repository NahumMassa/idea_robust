import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'db'))


import argparse
from format_setlist import get_data_from_text, print_table
from upload import upload_data_to_db
from call_nano import nano_editor

blueprint = """
#title
----
#artist
----
#link
---- 
"""

parser = argparse.ArgumentParser(description='Setlist upload to db and format.')
parser.add_argument('--mode', choices=['format', 'upload'], default='format', help='Mode of operation.')
parser.add_argument('--date', type=str, default=None, help='Optional manual date (YYYY-MM-DD). If not specified, defaults to the next Sunday.')
args = parser.parse_args()

if args.mode == 'format':
    try:
        data = nano_editor(blueprint=blueprint)
        if data:
            songs, artists, links = get_data_from_text(data)
            print_table(songs, artists, links)
    except Exception as e: 
        print(f"Error: {e}")

elif args.mode == 'upload':
    try:
        data = nano_editor(blueprint=blueprint)

    except Exception as e:
        print(f"Error: {e}")
    if data:
        data_tuple = get_data_from_text(data)
        upload_data_to_db(data_tuple, args.date)
        songs, artists, links = data_tuple
        print_table(songs, artists, links)