from datetime import date

from pathlib import Path

from flask import Blueprint, current_app, flash, redirect, render_template, request, send_from_directory, url_for

from app.constants import APPOINTMENT_SERVICES
from app.services.appointment_service import request_appointment
from app.services.catalog_service import list_public_categories, list_public_products
from app.services.contact_service import submit_contact_message

bp = Blueprint("main", __name__)


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
