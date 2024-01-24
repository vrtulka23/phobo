from flask import Blueprint, render_template, jsonify
from tinydb import TinyDB, Query
from pathlib import Path
import glob
import os

from .settings import *

setup_page = Blueprint(
    'setup_page', 
    __name__,
    template_folder='templates'
)

@setup_page.route('/setup')
def setup_view():
    counts = _file_info()
    return render_template(
        PAGE_INDEX, 
        content_page='setup.html', 
        counts = _file_info(),
    )
    
def _file_info():
    with TinyDB(DB_FILE_PATH) as db:
        User = Query()
        db_file_list = db.table(DB_TABLE_FILES)
        counts = {'registered':0,'unregistered':0,'missing':len(db_file_list)}
        for file_path in glob.glob(f"{DIR_PHOTO}/**", recursive=True):
            if os.path.isdir(file_path):
                continue
            file_name = str(Path(file_path).relative_to(DIR_PHOTO))
            if db_file_list.count(User.name==file_name):
                counts['registered'] += 1
                counts['missing'] -= 1
            else:
                counts['unregistered'] += 1
    return counts
    
@setup_page.route('/api/setup/get_counts')
def get_counts():
    counts = _file_info()
    return jsonify(counts)
    
@setup_page.route('/api/setup/remove_registered')
def remove_registered():
    with TinyDB(DB_FILE_PATH) as db:
        User = Query()
        db.drop_table(DB_TABLE_FILES)
    counts = _file_info()
    return jsonify(counts)

@setup_page.route('/api/setup/remove_missing')
def remove_missing():
    with TinyDB(DB_FILE_PATH) as db:
        User = Query()
        db_file_list = db.table(DB_TABLE_FILES)
        for file_data in db_file_list.all():
            exists = os.path.isfile(f"{DIR_PHOTO}/{file_data['name']}")
            if not exists:
                db_file_list.remove(doc_ids=[file_data.doc_id])
    counts = _file_info()
    return jsonify(counts)
    
@setup_page.route('/api/setup/add_unregistered')
def add_unregistered():
    with TinyDB(DB_FILE_PATH) as db:
        User = Query()
        db_file_list = db.table(DB_TABLE_FILES)
        for file_path in glob.glob(f"{DIR_PHOTO}/**", recursive=True):
            if os.path.isdir(file_path):
                continue
            file_name = str(Path(file_path).relative_to(DIR_PHOTO))
            if not db_file_list.count(User.name==file_name):
                db_file_list.insert({'name':file_name})
    counts = _file_info()
    return jsonify(counts)

@setup_page.route('/api/setup/remove_unregistered')
def remove_unregistered():
    with TinyDB(DB_FILE_PATH) as db:
        User = Query()
        db_file_list = db.table(DB_TABLE_FILES)
        for file_path in glob.glob(f"{DIR_PHOTO}/**", recursive=True):
            if os.path.isdir(file_path):
                continue
            file_name = str(Path(file_path).relative_to(DIR_PHOTO))
            if not db_file_list.count(User.name==file_name):
                os.remove(file_path)
    counts = _file_info()
    return jsonify(counts)
