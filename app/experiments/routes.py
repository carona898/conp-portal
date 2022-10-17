from __future__ import annotations

from flask import current_app, flash, render_template, request, redirect, url_for, send_from_directory
from sqlalchemy import or_

from . import experiments_bp
from .data import data
from .filters import get_filters
from .forms import ExperimentForm
from .search import SearchEngine
from .sort import SortKey
from .utils import upload_file, get_column_type
from .. import config, db
from ..models import Experiment

@experiments_bp.route('/')
def home():
  return render_template('experiments/home.html')

@experiments_bp.route('/search')
def search():
  filters = get_filters(request)
  page = request.args.get('page', 1, int)
  per_page = request.args.get('per_page', 10, int)
  search_term = request.args.get('search_term', None, str)
  sort_key = SortKey(request.args.get('sort_key', 'title_asc', str))
  
  active_filters = []
  for filter in filters:
    for option, active in filters[filter]['options'].items():
      if active:
        active_filters.append(getattr(Experiment, filter).contains(option))
  query = Experiment.query.filter(or_(*active_filters))
  query = query.order_by(sort_key.column())
  
  if search_term:
    search_engine = SearchEngine()
    matching_ids = search_engine.search(search_term, query.all())
    query = query.filter(Experiment.id.in_(matching_ids))
  
  pagination = query.paginate(page=page, per_page=per_page)
  
  return render_template(
    'experiments/search.html', 
    filters=filters,
    pagination=pagination,
    sort_key=sort_key
  )

@experiments_bp.route('/submit', methods=['GET', 'POST'])
def submit():
  form = ExperimentForm() # ExperimentForm()
  print(form.other_software.render_kw)
  if form.validate_on_submit():
    flash('Done!')
    repository_file = upload_file(form.repository)
    image_file = upload_file(form.image_file)
    experiment = Experiment(
      title = form.title.data,
      description = form.description.data,
      creators = form.creators.data,
      contact_person = form.contact_person.data,
      contact_email = form.contact_email.data,
      keywords = form.keywords.data,
      modalities = form.modalities.data,
      primary_software = form.primary_software.data,
      primary_function = form.primary_function.data,
      repository_file = repository_file,
      image_file = image_file
    )
    db.session.add(experiment)
    db.session.commit()
    return redirect(url_for('.submit'))
  return render_template('experiments/submit.html', data=data, form=form)

@experiments_bp.route('/uploads/<name>')
def download_file(name):
    return send_from_directory(current_app.config["EXPERIMENTS_UPLOAD_DIRECTORY"], name)
