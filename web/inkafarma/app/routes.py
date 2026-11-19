from datetime import date, datetime, time

from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.extensions import db
from app.models import Appointment, ContactMessage, Product

bp = Blueprint("main", __name__)


@bp.app_context_processor
def inject_today():
    return {"today": date.today()}


def _text(name):
    return request.form.get(name, "").strip()


@bp.route("/")
def dashboard():
    products = Product.query.filter(Product.stock > 0).filter(
        (Product.expiry_date.is_(None)) | (Product.expiry_date >= date.today())
    ).order_by(Product.name).limit(6).all()
    return render_template("home.html", products=products)


@bp.route("/productos")
def inventory():
    search = request.args.get("q", "").strip()
    category = request.args.get("categoria", "").strip()
    query = Product.query.filter(Product.stock > 0).filter(
        (Product.expiry_date.is_(None)) | (Product.expiry_date >= date.today())
    )
    if search:
        pattern = f"%{search}%"
        query = query.filter(Product.name.ilike(pattern))
    if category:
        query = query.filter_by(category=category)
    products = query.order_by(Product.name).all()
    categories = [row[0] for row in db.session.query(Product.category).filter(
        Product.stock > 0
    ).distinct().order_by(Product.category).all()]
    return render_template("products.html", products=products, categories=categories,
                           search=search, category=category)


@bp.route("/citas", methods=["GET", "POST"])
def appointments():
    if request.method == "POST":
        try:
            appointment_at = datetime.fromisoformat(_text("appointment_at"))
        except ValueError:
            appointment_at = None
        if not appointment_at or appointment_at <= datetime.now():
            flash("Elige una fecha y hora futura para tu solicitud.", "error")
        else:
            entry = Appointment(
                patient_name=_text("patient_name"),
                phone=_text("phone"),
                service=_text("service"),
                professional="Por asignar",
                appointment_at=appointment_at,
                status="Solicitud recibida",
                notes=None,
            )
            if not entry.patient_name or not entry.phone or not entry.service:
                flash("Completa tu nombre, teléfono y servicio.", "error")
            else:
                db.session.add(entry)
                db.session.commit()
                flash("Recibimos tu solicitud. La farmacia se comunicará contigo para confirmar la disponibilidad.", "success")
                return redirect(url_for("main.appointments"))
    return render_template("appointments.html")


@bp.route("/contacto", methods=["GET", "POST"])
def contacts():
    if request.method == "POST":
        entry = ContactMessage(
            name=_text("name"),
            email=_text("email"),
            phone=_text("phone") or None,
            subject=_text("subject"),
            message=_text("message"),
        )
        if not all([entry.name, entry.email, entry.subject, entry.message]):
            flash("Completa los campos obligatorios para enviar tu mensaje.", "error")
        else:
            db.session.add(entry)
            db.session.commit()
            flash("Gracias por escribirnos. Recibimos tu mensaje.", "success")
            return redirect(url_for("main.contacts"))
    return render_template("contacts.html")
