from flask import Flask, render_template, redirect, url_for, session, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
import datetime as dt
import os

app = Flask(__name__)
app.secret_key = 'dnfg23het4ttreh'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


migrate = Migrate(app, db)

current_date = dt.date.today()

class Users(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(100))
    lastName = db.Column(db.String(100))
    username = db.Column(db.String(100))
    email = db.Column(db.String(100))
    password = db.Column(db.String(100))

    tareas = db.relationship('Post', backref='users', lazy=True)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    descripcion = db.Column(db.String(200), nullable=False)

    users_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

with app.app_context():
    db.create_all()

def login_requerido(f):
    @wraps(f)
    def decorador(*args, **kwargs):
        if 'id' not in session:
            return redirect(url_for('Login'))

        return f(*args, **kwargs)
    return decorador

@app.route('/', methods=['GET', 'POST'])
@login_requerido
def InicioUsuario():
    user_id = session.get('id')
    name = session['username']

    if request.method == 'POST':
        post = request.form['post']

        if not post == "":
            nueva_tarea = Post(descripcion=post, users_id=user_id)
            db.session.add(nueva_tarea)
            db.session.commit()



    tareas = Post.query.filter_by(users_id=user_id).all()
    return render_template('InicioUsuario.html', tareas=tareas, username=name, date=current_date)

@app.route('/register', methods=["GET", "POST"])
def Register():
    if request.method == 'POST':
        name = request.form['name']
        lastname = request.form['lastname']
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        usuario_existente = Users.query.filter_by(username=username).first()
        email_existente = Users.query.filter_by(email=email).first()

        def not_data():
            datos = [name, lastname, username, email, password]
            for dato in datos:
                if dato.strip() == "":
                    return True
            return False
            
        def not_caracter():
            caracteres_prohibidos = ["/", ":", "(", ")", "$", "@", '"', "?", "!", "'", "[", "]", "{", "}", "#", "%", "^", "*", "+", "=", "/", "|", "¢", "<", ">", "€", "º", "ª"]
            for caractere in name:
                if caractere in caracteres_prohibidos:
                    return True
            return False
            
        if not_data():
            return "Falta un dato"
        elif usuario_existente:
            return "El username ingresado ya existe"
        elif len(username) < 8:
            return "El username es muy corto"
        elif not_caracter():
            return "Solo son permitidos los caracteres especiales de -, _"
        elif email_existente or "@" not in email or not email.endswith(".com"):
            return "Correo no valido"
        
        password_hash = generate_password_hash(password, method='pbkdf2:sha256')

        new_user = Users(name=name, lastName=lastname, username=username, email=email, password=password_hash)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('Login'))
        
        
    return render_template('Register.html')

@app.route('/login', methods=["GET", "POST"])
def Login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']

        exist_user = Users.query.filter_by(username=username).first()

        if not exist_user:
            flash("El usuario es incorrecto.", 'error')
        elif not check_password_hash(exist_user.password, password):
            flash("La contraseña es incorrecta.", 'error')
        else: 
            session["id"] = exist_user.id
            session["username"] = username
            return redirect(url_for("InicioUsuario"))

    return render_template('Login.html')

@app.route('/logout')
def Logout():
    session.clear()  # Limpia toda la sesión
    return redirect(url_for('Login'))

if __name__ == '__main__':
    app.run(debug=True)
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)