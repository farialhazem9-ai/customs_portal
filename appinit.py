from flask import Flask
from .config import Config

def create_app():

    app = Flask(__name__)
    app.config.from_object(Config)

    # Blueprints
    from .auth.routes import auth_bp
    from .dashboard.routes import dashboard_bp
    from .items.routes import items_bp
    from .stores.routes import stores_bp
    from .stock.routes import stock_bp
    from .purchases.routes import purchases_bp
    from .issues.routes import issues_bp
    from .reports.routes import reports_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(items_bp)
    app.register_blueprint(stores_bp)
    app.register_blueprint(stock_bp)
    app.register_blueprint(purchases_bp)
    app.register_blueprint(issues_bp)
    app.register_blueprint(reports_bp)

    return app