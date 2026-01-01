"""View routes for page rendering."""
from flask import Blueprint, render_template

views_bp = Blueprint('views', __name__)


@views_bp.route('/')
def index():
    """Render the main dashboard page."""
    return render_template('index.html')


@views_bp.route('/compare')
def compare():
    """Render the asset comparison page."""
    return render_template('compare.html')
