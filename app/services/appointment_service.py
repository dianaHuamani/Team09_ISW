from datetime import datetime

from app.constants import APPOINTMENT_REQUEST_STATUS, DEFAULT_PROFESSIONAL
from app.database import db
from app.models import Appointment


def request_appointment(patient_name, phone, service, preferred_time):
    patient_name = patient_name.strip()
    phone = phone.strip()
    service = service.strip()
    try:
        appointment_at = datetime.fromisoformat(preferred_time)
    except (TypeError, ValueError):
        return False, "Elige una fecha y hora válida."

    if appointment_at <= datetime.now():
        return False, "Elige una fecha y hora futura para tu solicitud."
    if not patient_name or not phone or not service:
        return False, "Completa tu nombre, teléfono y servicio."

    db.session.add(Appointment(
        patient_name=patient_name,
        phone=phone,
        service=service,
        professional=DEFAULT_PROFESSIONAL,
        appointment_at=appointment_at,
        status=APPOINTMENT_REQUEST_STATUS,
    ))
    db.session.commit()
    return True, "Recibimos tu solicitud. La farmacia se comunicará contigo para confirmar la disponibilidad."
