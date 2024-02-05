from flask import Blueprint, render_template, jsonify, request, url_for

from ..settings import *
from ..models.photo_model import PhotoModel

setup_page = Blueprint(
    'setup_page', 
    __name__,
    template_folder='templates'
)

@setup_page.route('/setup')
def setup_view():
    with PhotoModel() as p:
        counts = p.count()
    return render_template(
        PAGE_INDEX, 
        content_page='setup.html', 
        counts = counts,
    )
    
@setup_page.route('/api/setup/get_counts')
def get_counts():
    with PhotoModel() as p:
        counts = p.count()
    return jsonify(counts)
    
@setup_page.route('/api/setup/remove_registered', methods=['GET'])
def remove_registered():
    with PhotoModel() as p:
        doc_id = request.args.get('doc_id')
        if doc_id:
            p.remove(int(doc_id))
        else:
            p.remove_all()
        counts = p.count()
    return jsonify(counts)
    
@setup_page.route('/api/setup/add_unregistered', methods=['GET'])
def add_unregistered():
    with PhotoModel() as p:
        doc_id = request.args.get('doc_id')
        if doc_id:
            p.add(doc_id=int(doc_id)-1)
        else:
            p.add_all()
        counts = p.count()
    return jsonify(counts)

@setup_page.route('/api/setup/show_unregistered')
def show_unregistered():
    with PhotoModel() as p:
        data = []
        for i, item in enumerate(p.list_unregistered()):
            url_image = url_for(
                'photo_page.api_imports',
                file_name = item['file_name'],
            )
            data.append({
                'doc_id':        i+1,
                'variant_id':    '-',
                'name':          item['file_name'],
                'format':        item['image_format'],
                'url_image':     url_image
            })
    return jsonify({
        'data': data,
        'type': 'unregistered'
    })

@setup_page.route('/api/setup/show_registered')
def show_registered():
    with PhotoModel() as p:
        data = []
        for doc in p.list_registered():
            for variant in doc['variants']:
                if variant['variant_id']==doc['variant_id']:
                    break
            url_image = url_for(
                'photo_page.api_imports',
                file_name = variant['name_original'],
            )
            url_photo = url_for(
                'photo_page.photo_preview',
                doc_id = doc.doc_id,
                variant_id = doc['variant_id'][:VARIANT_ID_CUT],
            )
            data.append({
                'doc_id':        doc.doc_id,
                'variant_id':    doc['variant_id'][:VARIANT_ID_CUT],
                'name':          variant['name_original'],
                'format':        variant['image_format'],
                'url_image':     url_image,
                'url_photo':     url_photo,
            })
    return jsonify({
        'data': data,
        'type': 'registered'
    })
