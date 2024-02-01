from flask import Flask, render_template, url_for
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
        file_database = DB_FILE,
    )

@app.route('/image')
def image():

    db = TinyDB(Path(DIR_PHOBO)/DB_NAME)
    User = Query()

    file_id = request.args.get('file')

    db_file_list = db.table('file_list')
    file_object = db_file_list.get(doc_id=file_id)

    file_name = file_object['name']
    file_path = Path(DIR_IMPORT)/file_name

    image_size=(300, 300)
    if os.path.isfile(file_path):
        image = Image.open(file_path)
        image.thumbnail(image_size)
    else:
        text="Not Available"
        font_size=20
        background_color=(255, 255, 255)
        text_color=(0, 0, 0)
        image = Image.new("RGB", image_size, background_color)
        draw = ImageDraw.Draw(image)
        font = ImageFont.load_default()
        text_width = draw.textlength(text, font)
        text_height = font_size
        x = (image_size[0] - text_width) // 2
        y = (image_size[1] - text_height) // 2
        draw.text((x, y), text, font=font, fill=text_color)

    position = (
        int(0.5*(image_size[0]-image.size[0])),
        int(0.5*(image_size[1]-image.size[1]))
    )

    new_image = Image.new("RGB", image_size, "WHITE")
    new_image.paste(image, position)
    new_image.convert('RGB')
    image = new_image
        
    with io.BytesIO() as buffer:
        image.save(buffer, format="JPEG") 
        image_binary = buffer.getvalue()

    response = make_response(image_binary)
    response.headers.set('Content-Type', 'image/jpeg')
    #response.headers.set(
    #    'Content-Disposition', 'attachment', filename='%s.jpg' % pid)
    return response
