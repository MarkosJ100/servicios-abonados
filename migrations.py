from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///servicios_abonados.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'tu_clave_secreta_unica_y_segura_2024'

db = SQLAlchemy(app)
migrate = Migrate(app, db)

class Registro(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.Date, nullable=False)
    numero_despacho = db.Column(db.String(50), nullable=False)
    importe = db.Column(db.Float, nullable=False)
    nombre_compania = db.Column(db.String(100), nullable=False)
    estado = db.Column(db.String(20), default='Pendiente')
    pagado = db.Column(db.Boolean, default=False, nullable=False)

    def __repr__(self):
        return f'<Registro {self.id}>'

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
