import os

from flask import Flask
from werkzeug.security import generate_password_hash

from app.config import Config
from app.database import db


def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)
    db.init_app(app)

    from app import models  # noqa: F401
    from app.routes import bp

    app.register_blueprint(bp)

    with app.app_context():
        db.create_all()
        from app.models import AdminUser

        primary_username = os.getenv("ADMIN_USERNAME", "admin").strip() or "admin"
        primary_password = os.getenv("ADMIN_PASSWORD", "admin123")
        primary = AdminUser.query.filter_by(role="primary").first()
        if primary is None:
            primary = AdminUser(
                username=primary_username,
                password_hash=generate_password_hash(primary_password),
                role="primary",
                active=True,
            )
            db.session.add(primary)
            db.session.commit()
        if app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite:"):
            from app.models import Category, Product

            if Product.query.count() == 0:
                category_names = ["Analgésicos", "Antisépticos", "Dermocosmética", "Vitaminas"]
                categories = {name: Category(name=name) for name in category_names}
                db.session.add_all(categories.values())
                db.session.flush()
                db.session.add_all(
                    [
                        Product(
                            sku="DEM-001",
                            name="Paracetamol 500 mg",
                            category_ref=categories["Analgésicos"],
                            presentation="Caja x 100 tabletas",
                            stock=50,
                            min_stock=10,
                            price=12.50,
                        ),
                        Product(
                            sku="DEM-002",
                            name="Alcohol Medicinal 70°",
                            category_ref=categories["Antisépticos"],
                            presentation="Frasco x 120 ml",
                            stock=40,
                            min_stock=10,
                            price=4.50,
                        ),
                        Product(
                            sku="DEM-003",
                            name="Protector Solar FPS 50",
                            category_ref=categories["Dermocosmética"],
                            presentation="Frasco x 50 ml",
                            stock=25,
                            min_stock=5,
                            price=65.00,
                        ),
                        Product(
                            sku="DEM-004",
                            name="Vitamina C 500 mg",
                            category_ref=categories["Vitaminas"],
                            presentation="Frasco x 60 tabletas",
                            stock=35,
                            min_stock=8,
                            price=28.90,
                        ),
                    ]
                )
                db.session.commit()

    return app
