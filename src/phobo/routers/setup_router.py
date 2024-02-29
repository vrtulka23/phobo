from flask import Blueprint, render_template, jsonify, request, url_for

from ..settings import *
from ..models.photo_model import PhotoModel
from ..models.variant_model import VariantModel

SetupRouter = Blueprint(
    'SetupRouter', 
    __name__,
    template_folder='templates'
)

@SetupRouter.route('/setup')
def setup_view():
    with PhotoModel() as p:
        counts = p.count()
    return render_template(
        PAGE_INDEX, 
        content_page='setup.html', 
        counts = counts,
    )
    
@SetupRouter.route('/api/setup/get_counts')
def get_counts():
    with PhotoModel() as p:
        counts = p.count()
    return jsonify(counts)
    
@SetupRouter.route('/api/setup/remove_item', methods=['GET'])
def remove_item():
    with PhotoModel() as p:
        doc_id = request.args.get('doc_id')
        if doc_id:
            p.remove_variant(int(doc_id))
        else:
            p.remove_all_variants()
        counts = p.count()
    return jsonify(counts)
    
@SetupRouter.route('/api/setup/add_item', methods=['GET'])
def add_item():
    with PhotoModel() as p:
        doc_id = request.args.get('doc_id')
        if doc_id:
            p.add(doc_id=int(doc_id)-1)
        else:
            p.add_all()
        counts = p.count()
    return jsonify(counts)

@SetupRouter.route('/api/setup/show_files')
def show_files():
    p = PhotoModel()
    data = []
    for i, item in enumerate(p.list_files()):
        url_image = url_for(
            'PhotoRouter.api_imports',
            file_name = item['file_name'],
        )
        if item['registered']:
            url_photo = url_for(
                'PhotoRouter.photo_preview',
                doc_id = p.get_photo(variant_id=item['variant_id']).doc_id,
                variant_id = item['variant_id'],
            )
        else:
            url_photo = None
        data.append({
            'item_id':       i+1,
            'variant_id':    item['variant_id'] if item['registered'] else 0,
            'name':          item['file_name'],
            'format':        item['image_format'],
            'registered':    item['registered'],
            'url_image':     url_image,
            'url_photo':     url_photo,
        })
    return jsonify({
        'data': data,
        'type': 'unregistered'
    })

@SetupRouter.route('/api/setup/show_unregistered')
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

@SetupRouter.route('/api/setup/show_registered')
def show_registered():
    with PhotoModel() as p:
        data = []
        for doc in p.list_registered():
            with VariantModel() as var:
                variant = var.get(doc['variant_id'])
            url_image = url_for(
                'photo_page.api_imports',
                file_name = variant['name_original'],
            )
            url_photo = url_for(
                'photo_page.photo_preview',
                doc_id = doc.doc_id,
                variant_id = doc['variant_id'],
            )
            data.append({
                'doc_id':        doc.doc_id,
                'variant_id':    doc['variant_id'],
                'name':          variant['name_original'],
                'format':        variant['image_format'],
                'url_image':     url_image,
                'url_photo':     url_photo,
            })
    return jsonify({
        'data': data,
        'type': 'registered'
    })
