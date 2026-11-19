from datetime import date

from sqlalchemy import or_

from app.models import Product


def list_public_products(search="", category="", limit=None):
    query = Product.query.filter(Product.stock > 0).filter(
        or_(Product.expiry_date.is_(None), Product.expiry_date >= date.today())
    )
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))
    if category:
        query = query.filter_by(category=category)
    query = query.order_by(Product.sku)
    if limit:
        query = query.limit(limit)
    return query.all()


def list_public_categories():
    return [
        row[0]
        for row in Product.query.with_entities(Product.category)
        .filter(Product.stock > 0)
        .distinct()
        .order_by(Product.category)
        .all()
    ]
