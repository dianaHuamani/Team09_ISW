from datetime import date, datetime

from app.extensions import db


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(32), unique=True, nullable=False, index=True)
    name = db.Column(db.String(140), nullable=False, index=True)
    category = db.Column(db.String(80), nullable=False, default="General")
    presentation = db.Column(db.String(80), nullable=False, default="Unidad")
    stock = db.Column(db.Integer, nullable=False, default=0)
    min_stock = db.Column(db.Integer, nullable=False, default=5)
    price = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    expiry_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    @property
    def stock_state(self):
        if self.stock <= 0:
            return "Agotado"
        if self.stock <= self.min_stock:
            return "Por reponer"
        return "Disponible"

    @property
    def expiry_state(self):
        if not self.expiry_date:
            return "Sin fecha"
        days = (self.expiry_date - date.today()).days
        if days < 0:
            return "Vencido"
        if days <= 90:
            return "Próximo a vencer"
        return "Vigente"


class Appointment(db.Model):
    __tablename__ = "appointments"

    id = db.Column(db.Integer, primary_key=True)
    patient_name = db.Column(db.String(140), nullable=False)
    phone = db.Column(db.String(30), nullable=False)
    service = db.Column(db.String(100), nullable=False)
    professional = db.Column(db.String(100), nullable=False, default="Por asignar")
    appointment_at = db.Column(db.DateTime, nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default="Programada")
    notes = db.Column(db.String(300), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class ContactMessage(db.Model):
    __tablename__ = "contact_messages"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(160), nullable=False)
    phone = db.Column(db.String(30), nullable=True)
    subject = db.Column(db.String(140), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="Pendiente")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
