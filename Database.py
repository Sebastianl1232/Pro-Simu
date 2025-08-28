from flask import Flask
from flask_login import LoginManager
from Models import db, User, Question
import bcrypt

app = Flask(__name__)
app.config['SECRET_KEY'] = 'tu-clave-secreta-aqui'
import os
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root@127.0.0.1/simulacro.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def init_database():
    with app.app_context():
        db.create_all()
        
        # Insertar preguntas de ejemplo si no existen
        if Question.query.count() == 0:
            # Preguntas para Saber ICFES
            icfes_questions = [
                {
                    'test_type': 'ICFES',
                    'category': 'Matemáticas',
                    'question_text': 'Si x + 5 = 12, ¿cuál es el valor de x?',
                    'option_a': '5',
                    'option_b': '7',
                    'option_c': '17',
                    'option_d': '2',
                    'correct_answer': 'B',
                    'explanation': 'x + 5 = 12, entonces x = 12 - 5 = 7'
                },
                {
                    'test_type': 'ICFES',
                    'category': 'Lenguaje',
                    'question_text': '¿Cuál de las siguientes palabras es un sinónimo de "rápido"?',
                    'option_a': 'Lento',
                    'option_b': 'Veloz',
                    'option_c': 'Tranquilo',
                    'option_d': 'Pesado',
                    'correct_answer': 'B',
                    'explanation': 'Veloz es un sinónimo de rápido'
                },
                {
                    'test_type': 'ICFES',
                    'category': 'Ciencias',
                    'question_text': '¿Cuál es el planeta más cercano al Sol?',
                    'option_a': 'Venus',
                    'option_b': 'Tierra',
                    'option_c': 'Mercurio',
                    'option_d': 'Marte',
                    'correct_answer': 'C',
                    'explanation': 'Mercurio es el planeta más cercano al Sol'
                },
                {
                    'test_type': 'ICFES',
                    'category': 'Matemáticas',
                    'question_text': '¿Cuál es el resultado de 2³?',
                    'option_a': '6',
                    'option_b': '8',
                    'option_c': '9',
                    'option_d': '4',
                    'correct_answer': 'B',
                    'explanation': '2³ = 2 × 2 × 2 = 8'
                },
                {
                    'test_type': 'ICFES',
                    'category': 'Lenguaje',
                    'question_text': 'En la oración "El gato subió al árbol", ¿cuál es el sujeto?',
                    'option_a': 'subió',
                    'option_b': 'al árbol',
                    'option_c': 'El gato',
                    'option_d': 'árbol',
                    'correct_answer': 'C',
                    'explanation': 'El sujeto es quien realiza la acción, en este caso "El gato"'
                }
            ]
            
            # Preguntas para SaberPro
            saberpro_questions = [
                {
                    'test_type': 'SaberPro',
                    'category': 'Razonamiento Cuantitativo',
                    'question_text': 'Una empresa tiene utilidades de $50,000 y gastos de $30,000. ¿Cuál es la ganancia neta?',
                    'option_a': '$20,000',
                    'option_b': '$80,000',
                    'option_c': '$15,000',
                    'option_d': '$25,000',
                    'correct_answer': 'A',
                    'explanation': 'Ganancia neta = Utilidades - Gastos = $50,000 - $30,000 = $20,000'
                },
                {
                    'test_type': 'SaberPro',
                    'category': 'Lectura Crítica',
                    'question_text': 'En un texto argumentativo, la tesis principal:',
                    'option_a': 'Siempre aparece al final',
                    'option_b': 'Es la idea principal que se defiende',
                    'option_c': 'No es necesaria',
                    'option_d': 'Debe ser contradictoria',
                    'correct_answer': 'B',
                    'explanation': 'La tesis es la idea principal que el autor defiende a lo largo del texto'
                },
                {
                    'test_type': 'SaberPro',
                    'category': 'Competencias Ciudadanas',
                    'question_text': 'La democracia se caracteriza principalmente por:',
                    'option_a': 'El poder de una sola persona',
                    'option_b': 'La participación ciudadana',
                    'option_c': 'La ausencia de leyes',
                    'option_d': 'La desigualdad social',
                    'correct_answer': 'B',
                    'explanation': 'La democracia se basa en la participación activa de los ciudadanos'
                },
                {
                    'test_type': 'SaberPro',
                    'category': 'Razonamiento Cuantitativo',
                    'question_text': 'Si el 25% de un número es 50, ¿cuál es el número completo?',
                    'option_a': '200',
                    'option_b': '150',
                    'option_c': '100',
                    'option_d': '75',
                    'correct_answer': 'A',
                    'explanation': 'Si 25% = 50, entonces 100% = 50 × 4 = 200'
                },
                {
                    'test_type': 'SaberPro',
                    'category': 'Lectura Crítica',
                    'question_text': 'Un texto expositivo tiene como propósito principal:',
                    'option_a': 'Convencer al lector',
                    'option_b': 'Informar sobre un tema',
                    'option_c': 'Entretener',
                    'option_d': 'Expresar emociones',
                    'correct_answer': 'B',
                    'explanation': 'Los textos expositivos buscan informar y explicar un tema de manera objetiva'
                }
            ]
            
            for q_data in icfes_questions + saberpro_questions:
                question = Question(**q_data)
                db.session.add(question)
            
            db.session.commit()
            print("Base de datos inicializada con preguntas de ejemplo")

if __name__ == '__main__':
    init_database()