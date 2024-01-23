from flask import Flask, render_template, url_for
from bs4 import BeautifulSoup as bs
from PIL import Image
import os
from datetime import datetime

from .settings import *

app = Flask(__name__)

@app.route("/")
def phobo():
    
    file_html = 'index.html'
    file_content = 'item.html'
    
    img_data = {}
    
    img_file = 'figure.png'
    exif = Image.open('src/static/'+img_file).getexif()
    if exif:
        print(exif[36867])
        
    img_stat = os.stat('src/static/'+img_file)
    img_data = {
        'created': datetime.fromtimestamp(img_stat.st_ctime).strftime(FORMAT_DATE),
        'modified': datetime.fromtimestamp(img_stat.st_mtime).strftime(FORMAT_DATE),
    }

    return render_template(file_html, img_data=img_data)