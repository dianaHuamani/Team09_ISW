from datetime import date
from decimal import Decimal, InvalidOperation
import hmac
import os
import secrets

from pathlib import Path

from flask import Blueprint, current_app, flash, redirect, render_template, request, send_from_directory, session, url_for

from app.constants import APPOINTMENT_SERVICES
from app.services.appointment_service import request_appointment
from app.services.catalog_service import list_public_categories, list_public_products
from app.services.contact_service import submit_contact_message
from app.database import db
from app.models import Category, Product

bp = Blueprint("main", __name__)


def admin_required():
    if not session.get("admin_logged_in"):
        return redirect(url_for("main.admin_login"))
    return None


def valid_csrf():
    return hmac.compare_digest(request.form.get("csrf_token", ""), session.get("csrf_token", ""))


@bp.route("/admin", methods=["GET", "POST"])
@bp.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if session.get("admin_logged_in"):
        return redirect(url_for("main.admin_products"))
    if request.method == "POST":
        if not valid_csrf():
            flash("La sesión del formulario venció. Intenta de nuevo.", "error")
        else:
            username = os.getenv("ADMIN_USERNAME", "admin")
            password = os.getenv("ADMIN_PASSWORD", "admin123")
            if hmac.compare_digest(request.form.get("username", ""), username) and hmac.compare_digest(request.form.get("password", ""), password):
                session.clear()
                session["admin_logged_in"] = True
                session["csrf_token"] = secrets.token_urlsafe(32)
                return redirect(url_for("main.admin_products"))
            flash("Usuario o contraseña incorrectos.", "error")
    session.setdefault("csrf_token", secrets.token_urlsafe(32))
    return render_template("admin_login.html")


@bp.route("/admin/logout", methods=["POST"])
def admin_logout():
    if not valid_csrf():
        flash("La sesión del formulario venció.", "error")
        return redirect(url_for("main.admin_products"))
    session.clear()
    flash("Sesión cerrada.", "success")
    return redirect(url_for("main.admin_login"))


@bp.route("/admin/productos")
def admin_products():
    auth = admin_required()
    if auth:
        return auth
    products = Product.query.join(Category).order_by(Product.sku).all()
    return render_template("admin_products.html", products=products)


def product_form(product=None):
    categories = Category.query.order_by(Category.name).all()
    if request.method == "POST":
        if not valid_csrf():
            flash("La sesión del formulario venció. Intenta de nuevo.", "error")
            return render_template("admin_product_form.html", product=product, categories=categories)
        try:
            sku = request.form.get("sku", "").strip().upper()
            name = request.form.get("name", "").strip()
            category = db.session.get(Category, int(request.form.get("category_id", "")))
            price = Decimal(request.form.get("price", ""))
            stock = int(request.form.get("stock", ""))
            min_stock = int(request.form.get("min_stock", ""))
            expiry = request.form.get("expiry_date", "").strip()
            if not sku or len(sku) > 32 or not name or len(name) > 140 or not category:
                raise ValueError("Completa el código, nombre y categoría válidos.")
            duplicate = Product.query.filter(Product.sku == sku, Product.id != (product.id if product else 0)).first()
            if duplicate:
                raise ValueError("Ya existe un producto con ese código.")
            if price < 0 or stock < 0 or min_stock < 0:
                raise ValueError("Precio y existencias deben ser valores positivos.")
            product = product or Product()
            product.sku, product.name = sku, name
            product.category_ref = category
            product.presentation = request.form.get("presentation", "").strip() or "Unidad"
            product.stock, product.min_stock, product.price = stock, min_stock, price
            product.expiry_date = date.fromisoformat(expiry) if expiry else None
            db.session.add(product)
            db.session.commit()
            flash("Producto guardado correctamente.", "success")
            return redirect(url_for("main.admin_products"))
        except (ValueError, InvalidOperation, TypeError):
            db.session.rollback()
            flash("Revisa los campos: el precio, las existencias y la fecha deben ser válidos.", "error")
    return render_template("admin_product_form.html", product=product, categories=categories)


@bp.route("/admin/productos/nuevo", methods=["GET", "POST"])
def admin_product_create():
    auth = admin_required()
    if auth:
        return auth
    return product_form()


@bp.route("/admin/productos/<int:product_id>/editar", methods=["GET", "POST"])
def admin_product_edit(product_id):
    auth = admin_required()
    if auth:
        return auth
    product = db.get_or_404(Product, product_id)
    return product_form(product)


@bp.route("/admin/productos/<int:product_id>/eliminar", methods=["POST"])
def admin_product_delete(product_id):
    auth = admin_required()
    if auth:
        return auth
    if not valid_csrf():
        flash("La sesión del formulario venció.", "error")
    else:
        db.session.delete(db.get_or_404(Product, product_id))
        db.session.commit()
        flash("Producto eliminado.", "success")
    return redirect(url_for("main.admin_products"))


@bp.route("/sitemap.xml")
def sitemap():
    project_root = Path(current_app.root_path).parent
    return send_from_directory(project_root, "sitemap.xml", mimetype="application/xml")


@bp.app_context_processor
def inject_today():
    return {"today": date.today()}


@bp.route("/")
def dashboard():
    return render_template("home.html", products=list_public_products(limit=6))


@bp.route("/productos")
def inventory():
    search = request.args.get("q", "").strip()
    category = request.args.get("categoria", "").strip()
    return render_template(
        "products.html",
        products=list_public_products(search=search, category=category),
        categories=list_public_categories(),
        search=search,
        category=category,
    )


@bp.route("/citas", methods=["GET", "POST"])
def appointments():
    if request.method == "POST":
        success, message = request_appointment(
            request.form.get("patient_name", ""),
            request.form.get("phone", ""),
            request.form.get("service", ""),
            request.form.get("appointment_at", ""),
        )
        flash(message, "success" if success else "error")
        if success:
            return redirect(url_for("main.appointments"))
    return render_template("appointments.html", services=APPOINTMENT_SERVICES)


@bp.route("/contacto", methods=["GET", "POST"])
def contacts():
    if request.method == "POST":
        success, message = submit_contact_message(
            request.form.get("name", ""),
            request.form.get("email", ""),
            request.form.get("phone", ""),
            request.form.get("subject", ""),
            request.form.get("message", ""),
        )
        flash(message, "success" if success else "error")
        if success:
            return redirect(url_for("main.contacts"))
    return render_template("contacts.html")
