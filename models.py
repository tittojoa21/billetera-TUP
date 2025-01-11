from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import UserMixin, LoginManager
from datetime import datetime
from sqlalchemy import CheckConstraint

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()


TRANSACTION_DEPOSIT = 'deposit'
TRANSACTION_WITHDRAW = 'withdraw'
TRANSACTION_TRANSFER = 'transfer'
TRANSACTION_BUY_DOLLARS = 'buy_dollars'
TRANSACTION_SELL_DOLLARS = 'sell_dollars'
TRANSACTION_BUY_BLUE = 'buy_dollar_blue'
TRANSACTION_SELL_BLUE = 'sell_dollar_blue'

@login_manager.user_loader
def load_user(user_id):
    """Carga el usuario por ID para flask-login"""
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    """Modelo de Usuario: almacena datos del usuario y sus balances"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    balance_pesos = db.Column(db.Float, default=0.0, nullable=False)
    balance_dollars = db.Column(db.Float, default=0.0, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    
    cards = db.relationship('Card', backref='user', lazy=True, cascade="all, delete-orphan")
    transactions = db.relationship(
        'Transaction', 
        foreign_keys='Transaction.user_id', 
        backref='user', 
        lazy=True, 
        cascade="all, delete-orphan"
    )
    sent_transactions = db.relationship(
        'Transaction',
        foreign_keys='Transaction.sender_id',
        backref='sender',
        lazy=True
    )

    def set_password(self, password):
        """Hash y asigna la contraseña proporcionada"""
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        """Verifica la contraseña contra el hash almacenado"""
        return bcrypt.check_password_hash(self.password, password)

    def activate(self):
        """Activa el estado del usuario"""
        self.is_active = True

    def deactivate(self):
        """Desactiva el estado del usuario"""
        self.is_active = False

    def __repr__(self):
        return f'<User {self.username}, Balance Pesos: {self.balance_pesos:.2f}, Balance Dollars: {self.balance_dollars:.2f}>'

class Card(db.Model):
    """Modelo de Tarjeta asociado a un usuario"""
    __tablename__ = 'cards'
    
    id = db.Column(db.Integer, primary_key=True)
    card_number = db.Column(db.String(16), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<Card {self.card_number} for User {self.user_id}>'

class DollarRate(db.Model):
    """Modelo para almacenar la tasa de cambio de compra y venta del dólar"""
    __tablename__ = 'dollar_rate'
    
    id = db.Column(db.Integer, primary_key=True)
    buy_rate = db.Column(db.Float, nullable=False)      # Official buy rate
    sell_rate = db.Column(db.Float, nullable=False)     # Official sell rate
    blue_buy_rate = db.Column(db.Float, nullable=False)  # Blue buy rate
    blue_sell_rate = db.Column(db.Float, nullable=False) # Blue sell rate
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return (f'<DollarRate Official Buy: {self.buy_rate}, Sell: {self.sell_rate}, '
                f'Blue Buy: {self.blue_buy_rate}, Blue Sell: {self.blue_sell_rate}, Timestamp: {self.timestamp}>')

class Transaction(db.Model):
    """Modelo de Transacción que almacena la información de cada transacción realizada"""
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    amount = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(50), nullable=False)  
    destination = db.Column(db.String(150), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        CheckConstraint('amount > 0', name='amount_positive'),
    )

    def __repr__(self):
        return (
            f'<Transaction {self.type} of {self.amount} from {self.sender_id or "N/A"} '
            f'to User {self.user_id} at {self.timestamp}>'
        )
