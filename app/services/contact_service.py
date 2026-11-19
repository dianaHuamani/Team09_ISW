from app.database import db
from app.models import ContactMessage


def submit_contact_message(name, email, phone, subject, message):
    fields = [name.strip(), email.strip(), subject.strip(), message.strip()]
    if not all(fields):
        return False, "Completa los campos obligatorios para enviar tu mensaje."

    entry = ContactMessage(
        name=fields[0],
        email=fields[1],
        phone=phone.strip() or None,
        subject=fields[2],
        message=fields[3],
    )
    db.session.add(entry)
    db.session.commit()
    return True, "Gracias por escribirnos. Recibimos tu mensaje."
