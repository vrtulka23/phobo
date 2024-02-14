from flask import Flask, render_template, url_for
from flask import send_file
from bs4 import BeautifulSoup as bs
from PIL import Image
from tinydb import TinyDB, Query
from pathlib import Path
import glob
import os
from datetime import datetime

from .settings import *
from .routers.setup import setup_page
from .routers.photo import photo_page

app = Flask(__name__)
app.register_blueprint(setup_page)
app.register_blueprint(photo_page)

@app.route("/")
def index():
    return render_template(
        PAGE_INDEX, 
        content_page='home.html', 
        dir_import = DIR_IMPORT,
        dir_phobo = DIR_PHOBO,
        dir_photos = DIR_PHOTOS,
        file_database1 = DB_PHOTOS,
        file_database2 = DB_VARIANTS,
    )

@app.route('/favicon.ico')
def favicon():
    return send_file(f"../../img/favicon.ico", mimetype="image/x-icon")

@app.route('/vue/<file_path>')
def vue(file_path):
    return send_file(f"vue/{file_path}", mimetype=VUE_MIMETYPE)
    
