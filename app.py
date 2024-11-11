import os
from datetime import timedelta
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_migrate import Migrate
from models import db, bcrypt, User, Card, Transaction, DollarRate
from config import Config
from sqlalchemy.exc import SQLAlchemyError

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
bcrypt.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
migrate = Migrate(app, db)

# Load user for flask-login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def get_latest_dollar_rate():
    """Obtener la última tasa de cambio o valores predeterminados."""
    dollar_rate = DollarRate.query.order_by(DollarRate.timestamp.desc()).first()
    return {
        'buy_rate': dollar_rate.buy_rate if dollar_rate else 1115.0,
        'sell_rate': dollar_rate.sell_rate if dollar_rate else 1135.0,
        'blue_buy_rate': dollar_rate.blue_buy_rate if dollar_rate else 1200.0,
        'blue_sell_rate': dollar_rate.blue_sell_rate if dollar_rate else 1250.0
    }

def validate_amount(amount):
    """Validar y retornar el monto ingresado si es positivo."""
    try:
        amount = float(amount)
        if amount > 0:
            return amount
        else:
            flash('El monto debe ser positivo.', 'danger')
    except ValueError:
        flash('Por favor, ingresa un monto válido.', 'danger')
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')

        if not all([username, password, email]):
            flash('Todos los campos son obligatorios', 'danger')
            return redirect(url_for('register'))

        if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
            flash('El usuario o correo ya existe.', 'danger')
            return redirect(url_for('register'))

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, password=hashed_password, email=email, is_active=True)
        db.session.add(user)
        db.session.commit()

        flash('Registro exitoso. Ahora puedes iniciar sesión.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash('Has iniciado sesión con éxito.', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Usuario o contraseña incorrectos', 'danger')
    
    return render_template('index.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión con éxito', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    rates = get_latest_dollar_rate()
    transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.timestamp.desc()).limit(5).all()
    
    return render_template(
        'dashboard.html',
        balance_pesos=current_user.balance_pesos,
        balance_dollars=current_user.balance_dollars,
        buy_rate=rates['buy_rate'],
        sell_rate=rates['sell_rate'],
        blue_buy_rate=rates['blue_buy_rate'],
        blue_sell_rate=rates['blue_sell_rate'],
        transactions=transactions
    )

@app.route('/add-card', methods=['POST'])
@login_required
def add_card():
    card_number = request.form.get('card_number')
    if not (len(card_number) == 16 and card_number.isdigit()):
        flash('El número de tarjeta no es válido.', 'danger')
        return redirect(url_for('dashboard'))
    
    card = Card(card_number=card_number, user_id=current_user.id)
    db.session.add(card)
    db.session.commit()
    flash('Tarjeta agregada con éxito', 'success')
    return redirect(url_for('dashboard'))

@app.route('/transaction', methods=['POST'])
@login_required
def transaction():
    type = request.form.get('type')
    amount = validate_amount(request.form.get('amount'))
    if amount is None:
        return redirect(url_for('dashboard'))
    
    destination_username = request.form.get('destination')
    rates = get_latest_dollar_rate()

    if not rates['buy_rate'] or not rates['sell_rate']:
        flash('Las tasas de cambio no están disponibles actualmente.', 'danger')
        return redirect(url_for('dashboard'))

    try:
        if type == 'deposit':
            if not current_user.cards:
                flash('Debe agregar una tarjeta antes de realizar un depósito.', 'warning')
                return redirect(url_for('dashboard'))
            current_user.balance_pesos += amount
            transaction = Transaction(user_id=current_user.id, amount=amount, type=type)

        elif type == 'withdraw':
            if current_user.balance_pesos < amount:
                flash('Fondos insuficientes.', 'danger')
                return redirect(url_for('dashboard'))
            current_user.balance_pesos -= amount
            transaction = Transaction(user_id=current_user.id, amount=amount, type=type)

        elif type == 'transfer':
            recipient = User.query.filter_by(username=destination_username).first()
            if not recipient:
                flash('El usuario destinatario no existe.', 'danger')
                return redirect(url_for('dashboard'))
            if current_user.balance_pesos < amount:
                flash('Fondos insuficientes para esta operación.', 'danger')
                return redirect(url_for('dashboard'))
            
            current_user.balance_pesos -= amount
            recipient.balance_pesos += amount

            transaction_sender = Transaction(user_id=current_user.id, amount=amount, type=type, destination=destination_username)
            transaction_recipient = Transaction(user_id=recipient.id, sender_id=current_user.id, amount=amount, type=type)
            
            db.session.add(transaction_sender)
            db.session.add(transaction_recipient)

        elif type == 'buy_dollars':
            cost = amount * rates['buy_rate']
            if current_user.balance_pesos < cost:
                flash('Fondos insuficientes para comprar dólares.', 'danger')
                return redirect(url_for('dashboard'))
            
            current_user.balance_pesos -= cost
            current_user.balance_dollars += amount
            transaction = Transaction(user_id=current_user.id, amount=amount, type=type)

        elif type == 'sell_dollars':
            if current_user.balance_dollars < amount:
                flash('Fondos insuficientes para vender dólares.', 'danger')
                return redirect(url_for('dashboard'))
            
            revenue = amount * rates['sell_rate']
            current_user.balance_dollars -= amount
            current_user.balance_pesos += revenue
            transaction = Transaction(user_id=current_user.id, amount=amount, type=type)

        elif type == 'buy_dollar_blue':
            cost = amount * rates['blue_buy_rate']
            if current_user.balance_pesos < cost:
                flash('Fondos insuficientes para comprar dólares blue.', 'danger')
                return redirect(url_for('dashboard'))
            
            current_user.balance_pesos -= cost
            current_user.balance_dollars += amount
            transaction = Transaction(user_id=current_user.id, amount=amount, type=type)

        elif type == 'sell_dollar_blue':
            if current_user.balance_dollars < amount:
                flash('Fondos insuficientes para vender dólares blue.', 'danger')
                return redirect(url_for('dashboard'))
            
            revenue = amount * rates['blue_sell_rate']
            current_user.balance_dollars -= amount
            current_user.balance_pesos += revenue
            transaction = Transaction(user_id=current_user.id, amount=amount, type=type)

        else:
            flash('Tipo de transacción no válida.', 'danger')
            return redirect(url_for('dashboard'))

        db.session.add(transaction)
        db.session.commit()
        flash('Transacción realizada con éxito', 'success')

    except SQLAlchemyError as e:
        db.session.rollback()
        flash(f'Error en la transacción: {str(e)}', 'danger')

    return redirect(url_for('dashboard'))

@app.route('/transactions')
@login_required
def transactions():
    rates = get_latest_dollar_rate()
    user_transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.timestamp.desc()).all()
    return render_template('transactions.html', transactions=user_transactions, buy_rate=rates['buy_rate'], sell_rate=rates['sell_rate'])

@app.route('/transfer_history')
@login_required
def transfer_history():
    rates = get_latest_dollar_rate()
    transfers = Transaction.query.filter_by(user_id=current_user.id, type='transfer').order_by(Transaction.timestamp.desc()).limit(5).all()
    return render_template('transfer_history.html', transfers=transfers, buy_rate=rates['buy_rate'], sell_rate=rates['sell_rate'])

if __name__ == '__main__':
    app.run(debug=True)
