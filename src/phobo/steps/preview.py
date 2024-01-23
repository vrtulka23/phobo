from bs4 import BeautifulSoup
from tinydb import TinyDB, Query

from ..settings import *

def preview(html):

    with open('./html/preview.html','r') as f:
        preview = BeautifulSoup(f.read(), "html.parser")
    
    db = TinyDB(DIR_PHOBO/DB_NAME)
    User = Query()
    
    db_file_list = db.table('file_list')

    file_object = db_file_list.all()[0]
    file_name = file_object['name']
    file_id = file_object.doc_id

    img = preview.find('img', **{'id':'preview-image'})
    img['src'] = f"/image?file={file_id}"
    
    return preview
