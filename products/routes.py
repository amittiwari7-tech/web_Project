from flask import render_template, abort
from . import products_bp
from core.sheets_service import get_products, get_product_by_id

@products_bp.route("/products")
def list_products():
    products = get_products()
    return render_template("products/list.html", products=products)

@products_bp.route("/products/<product_id>")
def detail(product_id):
    product = get_product_by_id(product_id)
    if not product:
        abort(404)
    return render_template("products/detail.html", product=product)

