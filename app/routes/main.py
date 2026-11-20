from datetime import date, datetime
from decimal import Decimal, InvalidOperation
import hmac
import secrets

from pathlib import Path

from flask import Blueprint, current_app, flash, redirect, render_template, request, send_from_directory, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from app.constants import APPOINTMENT_SERVICES
from app.services.appointment_service import request_appointment
from app.services.catalog_service import list_public_categories, list_public_products
from app.services.contact_service import submit_contact_message
from app.database import db
from app.models import AdminUser, Appointment, Category, ContactMessage, Product

bp = Blueprint("main", __name__)


def admin_required():
    user = db.session.get(AdminUser, session.get("admin_user_id"))
    if not user or not user.active:
        session.clear()
        return redirect(url_for("main.admin_login"))
    return None


def principal_required():
    auth = admin_required()
    if auth:
        return auth
    user = db.session.get(AdminUser, session.get("admin_user_id"))
    if user.role != "primary":
        flash("Solo el usuario principal puede administrar cuentas.", "error")
        return redirect(url_for("main.admin_products"))
    return None


def valid_csrf():
    return hmac.compare_digest(request.form.get("csrf_token", ""), session.get("csrf_token", ""))


@bp.route("/admin", methods=["GET", "POST"])
@bp.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if session.get("admin_user_id"):
        return redirect(url_for("main.admin_products"))
    if request.method == "POST":
        if not valid_csrf():
            flash("La sesión del formulario venció. Intenta de nuevo.", "error")
        else:
            username = request.form.get("username", "").strip()
            user = AdminUser.query.filter_by(username=username).first()
            if user and user.active and check_password_hash(user.password_hash, request.form.get("password", "")):
                session.clear()
                session["admin_user_id"] = user.id
                session["admin_role"] = user.role
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


@bp.route("/admin/contactos")
def admin_contacts():
    auth = admin_required()
    if auth:
        return auth
    messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
    return render_template("admin_contacts.html", messages=messages)


@bp.route("/admin/citas")
def admin_appointments():
    auth = admin_required()
    if auth:
        return auth
    appointments = Appointment.query.order_by(Appointment.created_at.desc()).all()
    return render_template("admin_appointments.html", appointments=appointments)


@bp.route("/admin/usuarios", methods=["GET", "POST"])
def admin_users():
    auth = principal_required()
    if auth:
        return auth
    if request.method == "POST":
        if not valid_csrf():
            flash("La sesión del formulario venció. Intenta de nuevo.", "error")
        else:
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            if not username or len(username) > 80 or not username.replace("_", "").replace("-", "").isalnum():
                flash("El usuario debe tener hasta 80 caracteres y usar letras, números, guion o guion bajo.", "error")
            elif len(password) < 8:
                flash("La contraseña debe tener al menos 8 caracteres.", "error")
            elif AdminUser.query.filter_by(username=username).first():
                flash("Ese usuario ya existe.", "error")
            else:
                db.session.add(AdminUser(username=username, password_hash=generate_password_hash(password), role="secondary", active=True))
                db.session.commit()
                flash("Usuario secundario creado.", "success")
                return redirect(url_for("main.admin_users"))
    users = AdminUser.query.order_by(AdminUser.role, AdminUser.username).all()
    return render_template("admin_users.html", users=users)


@bp.route("/admin/usuarios/<int:user_id>/editar", methods=["GET", "POST"])
def admin_user_edit(user_id):
    auth = principal_required()
    if auth:
        return auth
    user = db.get_or_404(AdminUser, user_id)
    if user.role == "primary":
        flash("La cuenta principal se configura con ADMIN_USERNAME y ADMIN_PASSWORD.", "error")
        return redirect(url_for("main.admin_users"))
    if request.method == "POST":
        if not valid_csrf():
            flash("La sesión del formulario venció. Intenta de nuevo.", "error")
        else:
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            duplicate = AdminUser.query.filter(AdminUser.username == username, AdminUser.id != user.id).first()
            if not username or len(username) > 80 or duplicate:
                flash("Escribe un usuario válido que no esté en uso.", "error")
            elif password and len(password) < 8:
                flash("La contraseña nueva debe tener al menos 8 caracteres.", "error")
            else:
                user.username = username
                user.active = request.form.get("active") == "on"
                if password:
                    user.password_hash = generate_password_hash(password)
                db.session.commit()
                flash("Usuario secundario actualizado.", "success")
                return redirect(url_for("main.admin_users"))
    return render_template("admin_user_form.html", item=user)


@bp.route("/admin/usuarios/<int:user_id>/eliminar", methods=["POST"])
def admin_user_delete(user_id):
    auth = principal_required()
    if auth:
        return auth
    user = db.get_or_404(AdminUser, user_id)
    if not valid_csrf():
        flash("La sesión del formulario venció.", "error")
    elif user.role == "primary":
        flash("No se puede eliminar la cuenta principal.", "error")
    else:
        db.session.delete(user)
        db.session.commit()
        flash("Usuario secundario eliminado.", "success")
    return redirect(url_for("main.admin_users"))


@bp.route("/admin/contactos/<int:message_id>/editar", methods=["GET", "POST"])
def admin_contact_edit(message_id):
    auth = admin_required()
    if auth:
        return auth
    message = db.get_or_404(ContactMessage, message_id)
    if request.method == "POST":
        if not valid_csrf():
            flash("La sesión del formulario venció. Intenta de nuevo.", "error")
        else:
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip()
            phone = request.form.get("phone", "").strip()
            subject = request.form.get("subject", "").strip()
            body = request.form.get("message", "").strip()
            status = request.form.get("status", "").strip()
            from app.services.contact_service import EMAIL_PATTERN
            if (not name or len(name) > 120 or not EMAIL_PATTERN.fullmatch(email) or len(email) > 160
                    or len(phone) > 30 or not subject or len(subject) > 140
                    or len(body) < 10 or len(body) > 4000 or status not in {"Pendiente", "Revisado", "Respondido"}):
                flash("Revisa los datos: verifica el correo, los límites de caracteres y el estado.", "error")
            else:
                message.name, message.email, message.phone = name, email, phone or None
                message.subject, message.message, message.status = subject, body, status
                db.session.commit()
                flash("Mensaje actualizado.", "success")
                return redirect(url_for("main.admin_contacts"))
    return render_template("admin_contact_form.html", item=message)


@bp.route("/admin/citas/<int:appointment_id>/editar", methods=["GET", "POST"])
def admin_appointment_edit(appointment_id):
    auth = admin_required()
    if auth:
        return auth
    appointment = db.get_or_404(Appointment, appointment_id)
    if request.method == "POST":
        if not valid_csrf():
            flash("La sesión del formulario venció. Intenta de nuevo.", "error")
        else:
            patient_name = request.form.get("patient_name", "").strip()
            phone = request.form.get("phone", "").strip()
            service = request.form.get("service", "").strip()
            professional = request.form.get("professional", "").strip()
            status = request.form.get("status", "").strip()
            notes = request.form.get("notes", "").strip()
            try:
                appointment_at = datetime.fromisoformat(request.form.get("appointment_at", ""))
            except ValueError:
                appointment_at = None
            if (not patient_name or len(patient_name) > 140 or not phone or len(phone) > 30
                    or service not in APPOINTMENT_SERVICES or not appointment_at
                    or not professional or len(professional) > 100 or not status or len(status) > 20
                    or len(notes) > 300):
                flash("Revisa los datos de la cita y sus límites de caracteres.", "error")
            else:
                appointment.patient_name = patient_name
                appointment.phone = phone
                appointment.service = service
                appointment.professional = professional
                appointment.appointment_at = appointment_at
                appointment.status = status
                appointment.notes = notes or None
                db.session.commit()
                flash("Solicitud de cita actualizada.", "success")
                return redirect(url_for("main.admin_appointments"))
    return render_template("admin_appointment_form.html", item=appointment, services=APPOINTMENT_SERVICES)


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
