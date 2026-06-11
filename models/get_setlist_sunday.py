import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "db"))

from db.upload import get_timestamp_for_Sunday


def query_setlist_for_sunday():
    date_sunday = get_timestamp_for_Sunday()
    query = """
    SELECT s.all, p.all
    FROMS songs.s, performance.p 
    """


if __name__ == "__main__":
    query_setlist_for_sunday()
