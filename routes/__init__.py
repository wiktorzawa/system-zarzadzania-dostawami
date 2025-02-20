from flask import Blueprint

def init_app(app):
    # Import blueprintów
    from .MAIN.routes import main_bp
    from .admin.routes import admin_bp
    from .staff.routes import staff_bp
    from .supplier.routes import supplier_bp
    
    # Rejestracja blueprintów
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(staff_bp, url_prefix='/staff')
    app.register_blueprint(supplier_bp, url_prefix='/supplier') 