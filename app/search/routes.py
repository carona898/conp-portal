# -*- coding: utf-8 -*-
""" Routes Module

    Currently this module contains all of the routes in search blueprint
"""
import json
import os
from datetime import datetime, timedelta

import requests
from flask import Response, abort, render_template, request, current_app, send_from_directory
from flask_login import current_user
from sqlalchemy import func, or_

from app.models import Dataset, User
from app.search import search_bp


@search_bp.route('/search')
def search():
    """ Dataset Search Route

        This route executes a dataset search

        Args:
            search is the search term in the GET Request

        Retuns:
            JSON containing the matching datasets
    """
    return render_template('search.html', title='CONP | Search', user=current_user)


def get_dataset_logo(dataset_id):
    """
        Gets data set logos that are statically stored in the portal
        TODO: This should not be static, should be a fucntion the dataset in the database

        Args:
            dataset_id: the unique identifier of the dataset

        Returns:
            path to the png file for the logo
    """
    return "/static/img/default_dataset.jpeg"
    logos = {
        "8de99b0e-5f94-11e9-9e05-52545e9add8e": "/static/img/loris.png",
        "0ea345b4-62cf-11e9-b202-52545e9add8e": "/static/img/preventad.png",
        "0c1d0fe0-5240-11e9-9178-3417ebb10536": "/static/img/perform.png",
        "86970552-6828-11e9-89e5-52545e9add8e": "/static/img/medics.png",
        "47902f52-0d1c-11e9-9526-0242ac13001f": "/static/img/openneuro.png",
        "eb7b9b10-56ec-11e9-af32-0800277806bd": "/static/img/1000genomes.png"
    }
    return logos[dataset_id]


@search_bp.route('/dataset-search', methods=['GET'])
def dataset_search():
    """ Dataset Search Route

        This route executes a dataset search

        Args:
            search is the search term in the GET Request

        Retuns:
            JSON containing the matching datasets
    """
    datasets = []

    if current_user.is_authenticated:
        authorized = True
    else:
        authorized = False

    if request.args.get('search'):
        term = '%' + request.args.get('search') + '%'
        # Query datasets
        datasets = Dataset.query.filter(
            or_(func.lower(Dataset.name)
                .like(func.lower(term)),
                func.lower(Dataset.description)
                .like(func.lower(term)))
        )

    else:
        # Query datasets

        datasets = Dataset.query.order_by(Dataset.id).all()

    # Element input for payload
    elements = []

    # Build dataset response
    for d in datasets:
        dataset = {
            "authorized": authorized,
            "id": d.dataset_id,
            "title": d.name.replace("'", ""),
            "isPrivate": d.is_private,
            "thumbnailURL": get_dataset_logo(d.dataset_id),
            "imagePath": "?",
            "downloadPath": '?',
            "URL": '?',
            "downloads": "?",
            "views": "?",
            "likes": "?",
            "dateAdded": str(d.date_created.date()),
            "dateUpdated": str(d.date_updated.date()),
            "size": "?",
            "files": "?",
            "subjects": "?",
            "format": "?",
            "modalities": "?",
            "sources": "?"
        }
        elements.append(dataset)

    cursor = max(min(int(request.args.get('cursor') or 0), 0), 0)
    limit = max(min(int(request.args.get('limit') or 10), 10), 0)
    sort_key = request.args.get('sortKey') or "id"
    paginated = elements[(cursor):(cursor + limit)]
    paginated.sort(key=lambda o: o[sort_key])

    # Construct payload
    payload = {
        "authorized": authorized,
        "total": len(elements),
        "sortKeys": [
            {
                "key": "title",
                "label": "Title"
            },
            {
                "key": "imagePath",
                "label": "Image Path"
            },
            {
                "key": "downloads",
                "label": "Downloads"
            },
            {
                "key": "views",
                "label": "Views"
            },
            {
                "key": "likes",
                "label": "Likes"
            },
            {
                "key": "dateAdded",
                "label": "Date Added"
            },
            {
                "key": "dateUpdated",
                "label": "Date Updated"
            },
            {
                "key": "size",
                "label": "Size"
            },
            {
                "key": "files",
                "label": "Files"
            },
            {
                "key": "subjects",
                "label": "Subjects"
            },
            {
                "key": "format",
                "label": "Format"
            },
            {
                "key": "modalities",
                "label": "Modalities"
            },
            {
                "key": "sources",
                "label": "Sources"
            }
        ],
        "elements": paginated
    }

    return json.dumps(payload)


@search_bp.route('/dataset', methods=['GET'])
def dataset_info():
    """ Dataset Route

        Route to get the page for one dataset

        Args:
            id (REQ ARG): the id of the dataset to display

        Returns:
            rendered dataset.html for the dataset

    """

    dataset_id = request.args.get('id')

    # Query dataset
    d = Dataset.query.filter_by(dataset_id=dataset_id).first()

    if current_user.is_authenticated:
        authorized = True
    else:
        authorized = False

    dataset = {
        "authorized": authorized,

        "id": d.dataset_id,
        "title": d.name.replace("'", ""),
        "isPrivate": d.is_private,
        "thumbnailURL": get_dataset_logo(d.dataset_id),
        "imagePath": "/?",
        "downloadPath": 'download_path',
        "URL": 'raw_data_url',
        "downloads": "0",
        "views": "0",
        "likes": "0",
        "dateAdded": str(d.date_created.date()),
        "dateUpdated": str(d.date_updated.date()),
        "size": "0",
        "files": "0",
        "subjects": "0",
        "format": "?",
        "modalities": "?",
        "sources": "?"
    }

    metadata = get_dataset_metadata_information(d)

    return render_template(
        'dataset.html',
         title='CONP | Dataset',
         data=dataset,
         metadata=metadata,
         user=current_user
    )


@search_bp.route('/download_metadata', methods=['GET'])
def download_metadata():
    """ Download Metadata Route

        route to allow downloading the metadata for a dataset

        Args:
            dataset (REQ ARG): the dataset

        Returns:
            Response to the zipped metadata for the browser to download

        Raises:
            HTML error if this fails
    """
    from zipfile import ZipFile
    from tempfile import TemporaryDirectory

    # This should be made dynamic based on the dataset
    metadata_file_list = ["DATS.json", ".datalad"]
    dataset_directory = os.path.basename(request.args.get('dataset'))
    abs_dataset_directory = os.path.join(
        current_app.config['DATA_PATH'], dataset_directory)

    tmpDir = TemporaryDirectory()

    with TemporaryDirectory() as tmpDir:
        with ZipFile("{}/{}.zip".format(tmpDir, dataset_directory), "w") as zip:
            for f in metadata_file_list:
                abs_file_path = os.path.join(abs_dataset_directory, f)
                zip_file_path = os.path.join(dataset_directory, f)
                if os.path.exists(abs_file_path):
                    if os.path.isdir(abs_file_path):
                        file_paths = []
                        for root, directories, files in os.walk(abs_file_path):
                            for filename in files:
                                root_name = filename.replace(root, "")
                                file_path = os.path.join(root, filename)
                                file_paths.append((root_name, file_path))
                        for rn, fp in file_paths:
                            if os.path.isfile(fp):
                                zip.write(
                                    fp, "{}/{}".format(zip_file_path, rn))
                    else:
                        zip.write(abs_file_path, zip_file_path)

        return send_from_directory(tmpDir, "{}.zip".format(dataset_directory), as_attachment=True)


def get_dataset_metadata_information(dataset):
    """
        returns the datasets metadata

        Args:
            dataset: dictionary for the dataset

        Returns
            payload containing the datasets metadata

    """

    descriptor_path = os.path.join(
        current_app.config['DATA_PATH'],
        'conp-dataset',
        dataset.dataset_id,
        'DATS.json'
    )

    with open(descriptor_path, 'r') as json_file:
        data = json.load(json_file)

        authorString = data.get('creators', 'Undefined')
        if type(authorString) == list:
            authors = ", ".join([x['name'] for x in authorString])
        elif 'name' in authorString:
            authors = authorString['name']
        else:
            authors = authorString

        licenseString = data.get('licenses', 'None') 
        if type(licenseString) == list:
            licenseString = ", ".join([x['name'] for x in licenseString])
        else:
            if 'name' in licenseString:
                licenseString = licenseString['name']
            elif '$schema' in licenseString:
                licenseString = licenseString['$schema']
            elif 'dataUsesConditions' in licenseString:
                licenseString = licenseString['dataUsesConditions']
            else:
                licence = licenseString

        payload = {
            "authors": authors,
            "description": data.get('description', 'Undefined'),
            "contact": None,  # data['contact'],
            "version": data.get('version', 'Undefined'),
            "licenses": licenseString
        }

    return payload
