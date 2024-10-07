from flask import Flask, request, jsonify
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)

# Configure SQLite database
SQLALCHEMY_DATABASE_URI = 'sqlite:///finance_tracker.db'
engine = create_engine(SQLALCHEMY_DATABASE_URI)
Session = sessionmaker(bind=engine)

Base = declarative_base()

# Define the User model
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, nullable=False)

# Define the Category model
class Category(Base):
    __tablename__ = 'categories'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)

# Define the Transaction model
class Transaction(Base):
    __tablename__ = 'transactions'
    id = Column(Integer, primary_key=True)
    amount = Column(Float, nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=False)
    category = relationship('Category', backref='transactions')
    date = Column(DateTime, default=datetime.utcnow)
    description = Column(String(200))

# Define the Budget model
class Budget(Base):
    __tablename__ = 'budgets'
    id = Column(Integer, primary_key=True)
    amount = Column(Float, nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=False)
    category = relationship('Category', backref='budgets')

# Create the database tables
Base.metadata.create_all(engine)

# Home route
@app.route('/')
def home():
    return "Welcome to the Personal Finance Tracker!"

# Create a new Category (POST)
@app.route('/api/category', methods=['POST'])
def create_category():
    session = Session()
    try:
        data = request.get_json()
        category_name = data.get('name')

        if not category_name:
            return jsonify({"error": "Category name is required"}), 400

        existing_category = session.query(Category).filter_by(name=category_name).first()
        if existing_category:
            return jsonify({"error": "Category already exists"}), 400

        new_category = Category(name=category_name)
        session.add(new_category)
        session.commit()

        return jsonify({"message": f"Category '{category_name}' created successfully!"}), 201
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

# Retrieve all transactions (GET)
@app.route('/api/transactions', methods=['GET'])
def get_transactions():
    session = Session()
    try:
        transactions = session.query(Transaction).all()
        transactions_data = []
        for transaction in transactions:
            transactions_data.append({
                "id": transaction.id,
                "amount": transaction.amount,
                "category": transaction.category.name,
                "date": transaction.date.strftime("%Y-%m-%d %H:%M:%S"),
                "description": transaction.description
            })

        return jsonify(transactions_data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

if __name__ == '__main__':
    app.run(debug=True)