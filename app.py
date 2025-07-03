from flask import Flask
from cotizacion_controller import cotizacion_bp

app = Flask(__name__)
app.register_blueprint(cotizacion_bp)

if __name__ == "__main__":
    app.run(debug=True)
