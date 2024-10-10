from flask import Flask, request, jsonify, render_template
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
from sqlalchemy import func
app = Flask(__name__)

SQLALCHEMY_DATABASE_URI = 'sqlite:///finance_tracker.db'
engine = create_engine(SQLALCHEMY_DATABASE_URI)
Session = sessionmaker(bind=engine)

Base = declarative_base()


class Category(Base):
    __tablename__ = 'categories'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)


class Transaction(Base):
    __tablename__ = 'transactions'
    id = Column(Integer, primary_key=True)
    amount = Column(Float, nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=False)
    category = relationship('Category', backref='transactions')
    date = Column(DateTime, default=datetime.utcnow)
    description = Column(String(200))


class Budget(Base):
    __tablename__ = 'budgets'
    id = Column(Integer, primary_key=True)
    amount = Column(Float, nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=False)
    category = relationship('Category', backref='budgets')


Base.metadata.create_all(engine)


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/api/transactions', methods=['GET', 'POST'])
def transactions():
    db_session = Session()
    if request.method == 'GET':
        try:
            transactions = db_session.query(Transaction).all()
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
            db_session.close()
    elif request.method == 'POST':
        try:
            data = request.get_json()
            amount = data.get('amount')
            category_name = data.get('category')
            description = data.get('description', '')
            date_str = data.get('date')
            date = datetime.strptime(date_str, '%Y-%m-%dT%H:%M') if date_str else datetime.utcnow()

            category = db_session.query(Category).filter_by(name=category_name).first()
            if not category:
                category = Category(name=category_name)
                db_session.add(category)
                db_session.commit()

            new_transaction = Transaction(amount=amount, category=category, description=description, date=date)
            db_session.add(new_transaction)
            db_session.commit()

            return jsonify({"message": "Transaction added successfully"}), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        finally:
            db_session.close()


@app.route('/api/budgets', methods=['GET', 'POST'])
def budgets():
    db_session = Session()
    if request.method == 'GET':
        try:
            budgets = db_session.query(Budget).all()
            budgets_data = []
            for budget in budgets:
                total_spent = db_session.query(func.sum(Transaction.amount)).filter_by(category_id=budget.category_id).scalar() or 0

                budgets_data.append({
                    "id": budget.id,
                    "amount": budget.amount,
                    "category": budget.category.name,
                    "total_spent": total_spent,
                    "remaining": budget.amount - total_spent  # Calculate remaining amount
                })
            return jsonify(budgets_data), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        finally:
            db_session.close()

    elif request.method == 'POST':
        try:
            data = request.get_json()
            amount = data.get('amount')
            category_name = data.get('category')

            category = db_session.query(Category).filter_by(name=category_name).first()
            if not category:
                category = Category(name=category_name)
                db_session.add(category)
                db_session.commit()

            new_budget = Budget(amount=amount, category=category)
            db_session.add(new_budget)
            db_session.commit()

            return jsonify({"message": "Budget added successfully"}), 201
        except Exception as e:
            db_session.rollback()
            return jsonify({"error": str(e)}), 500
        finally:
            db_session.close()


if __name__ == '__main__':
    app.run(debug=True)
