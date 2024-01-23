from flask import Flask, request, make_response
from bs4 import BeautifulSoup
import numpy as np
import cv2
import glob
from pathlib import Path
from scinumtools import ThumbnailImage
import io
from PIL import Image, ImageDraw, ImageFont
from pillow_heif import register_heif_opener
register_heif_opener()
import os
from tinydb import TinyDB, Query

from .settings import *
from .steps import intro, setup, preview

app = Flask(__name__)

def stepper(html, step):
    step_back = step-1 if step>0 else 0
    step_next = step+1
    
    stepper = html.new_tag('div', **{'class':'content'})
    button_back = html.new_tag("a", href=f"?step={step_back}")
    button_back.string = "Previous step"
    stepper.append(button_back)
    stepper.append("|")
    button_next = html.new_tag("a", href=f"?step={step_next}")
    button_next.string = "Next step"
    stepper.append(button_next)
    return stepper

@app.route('/')
def index():

    step = request.args.get('step')
    step = 0 if step is None else int(step)

    with open('./html/main.html','r') as f:
        html = BeautifulSoup(f.read(), "html.parser")

    style = html.new_tag('link', rel="stylesheet", href="./css/main.css")
    html.head.append(style)

    content = html.find('div', id='content')

    content.append(stepper(html,step))

    steps = [
        intro,
        setup,
        preview,
    ]
    content.append(steps[step](html))

    content.append(stepper(html,step))
    
    return html.prettify()
    
@app.route('/image')
def image():

    db = TinyDB(DIR_PHOBO/DB_NAME)
    User = Query()

    file_id = request.args.get('file')

    db_file_list = db.table('file_list')
    file_object = db_file_list.get(doc_id=file_id)

    file_name = file_object['name']
    file_path = DIR_PHOTO/file_name

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
