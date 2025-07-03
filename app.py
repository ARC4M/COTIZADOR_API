from database import init_app, db
from cotizacion_controller import cotizacion_bp

app = init_app()
app.register_blueprint(cotizacion_bp)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
