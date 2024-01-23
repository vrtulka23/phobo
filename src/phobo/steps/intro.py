from ..settings import *

def intro(html):
    
    info = html.new_tag('div', **{'class':'info'})

    info.string = 'Hello to PhoBo'
    
    return info
