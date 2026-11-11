from flask import render_template, session, redirect, url_for
from . import home_bp
from core.sheets_service import get_products

@home_bp.route("/")
def index():
    products = get_products()
    # Featured items on landing page
    featured_products = products[:6] if products else []
    return render_template("home/index.html", products=featured_products)


@home_bp.route('/about')
def about():
    return render_template('home/about.html')


@home_bp.route('/dashboard')
def dashboard():
    if not session.get('status'):
        return redirect(url_for('auth.login'))
    return render_template('home/dashboard.html')