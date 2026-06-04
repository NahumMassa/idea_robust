


import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'db'))


import argparse
from db.create_setlist import format
from db.upload import upload_and_format
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
args = parser.parse_args()

if args.mode == 'format':
    try:
        data = nano_editor(blueprint=blueprint)
        if data:
            format(data)
    except Exception as e: 
        print(f"Error: {e}")

elif args.mode == 'upload':
    try:
        data = nano_editor(blueprint=blueprint)
    except Exception as e:
        print(f"Error: {e}")
    if data:
        upload_and_format(data)