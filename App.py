# Ruta para cambiar contraseña
from flask_login import login_required



from flask import render_template, request, redirect, url_for, flash, session, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from Database import app, init_database
from Models import db, User, Question, TestResult, TestAnswer
import bcrypt, random
from datetime import datetime

def get_user_by(field, value):
    return User.query.filter(getattr(User, field)==value).first()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form.get('role', 'estudiante')
        if get_user_by('username', username):
            flash('El nombre de usuario ya existe')
        elif get_user_by('email', email):
            flash('El email ya está registrado')
        else:
            password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            db.session.add(User(username=username, email=email, password_hash=password_hash, role=role))
            db.session.commit()
            flash('Registro exitoso. Por favor inicia sesión.')
            return redirect(url_for('login'))
        return redirect(url_for('register'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = get_user_by('username', request.form['username'])
        if user and bcrypt.checkpw(request.form['password'].encode(), user.password_hash.encode()):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Usuario o contraseña incorrectos')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    results = TestResult.query.filter_by(user_id=current_user.id).order_by(TestResult.completed_at.desc()).limit(5).all()
    has_delete_account = 'delete_account' in current_app.view_functions
    return render_template('dashboard.html', results=results, has_delete_account=has_delete_account)

@app.route('/select_test')
@login_required
def select_test():
    # Solo mostrar SaberPro como opción
    return render_template('test_selection.html', test_types=['SaberPro'])

@app.route('/start_test/<test_type>')
@login_required
def start_test(test_type):
    # Solo permitir SaberPro
    if test_type != 'SaberPro':
        flash('Tipo de prueba no válido')
        return redirect(url_for('select_test'))
    questions = Question.query.filter_by(test_type='SaberPro').all()
    if not questions:
        flash('No hay preguntas disponibles para esta prueba')
        return redirect(url_for('select_test'))
    random.shuffle(questions)
    session.update({
        'test_questions': [q.id for q in questions],
        'test_type': 'SaberPro',
        'test_start_time': datetime.utcnow().isoformat(),
        'current_question': 0,
        'answers': {}
    })
    return redirect(url_for('take_test'))

@app.route('/take_test')
@login_required
def take_test():
    if 'test_questions' not in session:
        return redirect(url_for('select_test'))
    qids, idx = session['test_questions'], session.get('current_question', 0)
    if idx >= len(qids):
        return redirect(url_for('finish_test'))
    question = Question.query.get(qids[idx])
    time_elapsed = int((datetime.utcnow() - datetime.fromisoformat(session['test_start_time'])).total_seconds())
    return render_template('test.html', question=question, question_number=idx+1, total_questions=len(qids), time_elapsed=time_elapsed)

@app.route('/submit_answer', methods=['POST'])
@login_required
def submit_answer():
    if 'test_questions' not in session:
        return jsonify({'error': 'No hay prueba activa'}), 400
    qid, answer = request.form.get('question_id'), request.form.get('answer')
    if not qid or not answer:
        return jsonify({'error': 'Respuesta inválida'}), 400
    session['answers'][qid] = answer
    session['current_question'] = session.get('current_question', 0) + 1
    return jsonify({'success': True})

@app.route('/finish_test')
@login_required
def finish_test():
    if 'test_questions' not in session:
        return redirect(url_for('dashboard'))
    qids, test_type, answers = session['test_questions'], session['test_type'], session['answers']
    correct_count, test_answers = 0, []
    for qid in qids:
        q = Question.query.get(qid)
        user_answer = answers.get(str(qid), '')
        is_correct = user_answer == q.correct_answer
        if is_correct: correct_count += 1
        test_answers.append(TestAnswer(question_id=qid, user_answer=user_answer, is_correct=is_correct))
    time_taken = int((datetime.utcnow() - datetime.fromisoformat(session['test_start_time'])).total_seconds())
    score = (correct_count / len(qids)) * 100
    test_result = TestResult(user_id=current_user.id, test_type=test_type, score=score, total_questions=len(qids), correct_answers=correct_count, time_taken=time_taken)
    db.session.add(test_result)
    db.session.flush()
    for ans in test_answers:
        ans.test_result_id = test_result.id
        db.session.add(ans)
    db.session.commit()
    for key in ['test_questions', 'test_type', 'test_start_time', 'current_question', 'answers']:
        session.pop(key, None)
    return redirect(url_for('view_results', test_id=test_result.id))

@app.route('/results/<int:test_id>')
@login_required
def view_results(test_id):
    result = TestResult.query.get_or_404(test_id)
    if result.user_id != current_user.id:
        flash('No tienes permiso para ver estos resultados')
        return redirect(url_for('dashboard'))
    answers = (
        db.session.query(TestAnswer, Question)
        .join(Question, TestAnswer.question_id == Question.id)
        .filter(TestAnswer.test_result_id == test_id)
        .all()
    )
    questions_with_answers = [
        {'question': q, 'user_answer': a.user_answer, 'is_correct': a.is_correct}
        for a, q in answers
    ]
    return render_template('results.html', result=result, questions=questions_with_answers)

@app.route('/history')
@login_required
def history():
    results = TestResult.query.filter_by(user_id=current_user.id).order_by(TestResult.completed_at.desc()).all()
    has_delete_account = 'delete_account' in current_app.view_functions
    return render_template('history.html', results=results, has_delete_account=has_delete_account)

@app.route('/delete_result/<int:test_id>', methods=['POST'])
@login_required
def delete_result(test_id):
    result = TestResult.query.get_or_404(test_id)
    if result.user_id != current_user.id:
        flash('No tienes permiso para eliminar este resultado')
        return redirect(url_for('history'))
    # Eliminar respuestas asociadas
    TestAnswer.query.filter_by(test_result_id=test_id).delete()
    db.session.delete(result)
    db.session.commit()
    flash('Resultado eliminado correctamente')
    return redirect(url_for('history'))

@app.route('/change_password')
@login_required
def change_password():
    has_delete_account = 'delete_account' in current_app.view_functions
    return render_template('change_password.html', has_delete_account=has_delete_account)


# Ruta para crear simulacro (solo profesores)
from flask import session

@app.route('/crear_simulacro', methods=['GET', 'POST'])
@login_required
def crear_simulacro():
    if not getattr(current_user, 'is_profesor', False):
        flash('Solo los profesores pueden acceder a esta página.')
        return redirect(url_for('dashboard'))

    if 'simulacro_preguntas' not in session:
        session['simulacro_preguntas'] = []

    if request.method == 'POST':
        # Fijar test_type como SaberPro
        pregunta = {
            'test_type': 'SaberPro',
            'category': request.form.get('category', ''),
            'question_text': request.form.get('question_text', ''),
            'option_a': request.form.get('option_a', ''),
            'option_b': request.form.get('option_b', ''),
            'option_c': request.form.get('option_c', ''),
            'option_d': request.form.get('option_d', ''),
            'correct_answer': request.form.get('correct_answer', ''),
            'explanation': request.form.get('explanation', '')
        }
        preguntas = session['simulacro_preguntas']
        preguntas.append(pregunta)
        session['simulacro_preguntas'] = preguntas
        flash('Pregunta agregada. Puedes seguir añadiendo más o guardar el simulacro.')

    if request.args.get('guardar') == '1' and session.get('simulacro_preguntas'):
        for p in session['simulacro_preguntas']:
            db.session.add(Question(**p))
        db.session.commit()
        session.pop('simulacro_preguntas', None)
        flash('Simulacro guardado exitosamente.')
        return redirect(url_for('dashboard'))

    preguntas = session.get('simulacro_preguntas', [])
    return render_template('crear_simulacro.html', preguntas=preguntas)

if __name__ == '__main__':
    init_database()
    app.run(debug=True)