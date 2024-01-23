import os
from tinydb import TinyDB, Query
import glob

from ..settings import *

def display_image(html, row_data):
    table = html.new_tag("table")

    file_path = row_data[0]
    
    row = html.new_tag("tr")
    image = html.new_tag("img", src=f"/image?file={file_path}") #, height=30)
    cell = html.new_tag("td")
    cell.append(image)
    row.append(cell)
    table.append(row)

    row = html.new_tag("tr")
    cell = html.new_tag("td")
    cell.string = str(file_path)
    row.append(cell)
    table.append(row)
    
    return table

def setup(html):
    info = html.new_tag('div', **{'class':'info'})

    item = html.new_tag('div')
    item.string = f"Phobo directory: {os.getcwd()/DIR_PHOBO}"
    info.append(item)
    if not os.path.exists(DIR_PHOBO):
        info.append("Setting up a new PhoBo directory.")
        os.mkdir(DIR_PHOBO)
    else:
        item = html.new_tag('div')
        item.string = "PhoBo directory already exists."
        info.append(item)
    db = TinyDB(DIR_PHOBO/DB_NAME)
    User = Query()
    #db.drop_table('file_list')
    db_file_list = db.table('file_list')

    counters = {'existing':0,'new':0,'missing':len(db_file_list)}
    for file_path in glob.glob(f"{DIR_PHOTO}/*"):
        file_name = Path(file_path).name
        if db_file_list.count(User.name==file_name):
            counters['existing'] += 1
            counters['missing'] -= 1
        else:
            counters['new'] += 1
            db_file_list.insert({'name':file_name})
        
    item = html.new_tag('div')
    item.string = f"Existing images: {counters['existing']}"
    info.append(item)
    item = html.new_tag('div')
    item.string = f"New images: {counters['new']}"
    info.append(item)
    item = html.new_tag('div')
    item.string = f"Missing images: {counters['missing']}"
    info.append(item)

    """
    file_list = html.new_tag('div', **{'class':'list-group'})
    for file_list_item in db_file_list.all():
        item = html.new_tag('div', **{'class':'list-group-item'})
        item.string = file_list_item['name']
        file_list.append(item)
    info.append(file_list)
    """
    
    db.close()

    return info
