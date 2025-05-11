from flask import Flask, request, jsonify, render_template, redirect, url_for, session
#from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os
import re
from datetime import datetime, timedelta
from typing import TypeVar, Type, List, Dict, Union, Any
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from bson import ObjectId 
import uuid


T = TypeVar('T')  # what is this ? -> TypeVar is a generic type that can be used to define a type that can be any type


# Database configuration
CAU_HINH_CSDL = {
    'may_chu': 'localhost\\SQLEXPRESS',
    'co_so_du_lieu': 'user_db', 
    'xac_thuc_windows': 'yes'  
}

# App initialization
app = Flask(__name__,
    template_folder='../../src',
    static_folder='../../src',
    static_url_path=''
)

# Basic configurations
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

# CORS configuration
CORS(app, supports_credentials=True) # Allow credentials in CORS requests


# Database setup
"""app.config['SQLALCHEMY_DATABASE_URI'] = f"mssql+pyodbc:///?odbc_connect=DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={CAU_HINH_CSDL['may_chu']};DATABASE={CAU_HINH_CSDL['co_so_du_lieu']};Trusted_Connection=yes"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
"""
Mongo_uri = "mongodb+srv://User_info:@@123456@@@cluster0.ppzjfeg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(Mongo_uri, ServerApi=ServerApi(1)) 
db = client["test"]
# collection -> if collectionn not exist
users_collection = db['users']
products_collection = db['products']
notifications_collection = db['notifications']
# 3 collection -> User, Product, Notification


"""# Models
class Notification(db.Model):  # type: ignore
    __tablename__ = 'notification'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=db.func.now())
    
    user = db.relationship('User', backref=db.backref('notifications', lazy=True))

class User(db.Model):  # type: ignore
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    name = db.Column(db.String(80), nullable=True)
    date_of_birth = db.Column(db.Date, nullable=True)
    address = db.Column(db.String(255), nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(15), nullable=True)  # Removed unique constraint from nullable field
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Product(db.Model):  # type: ignore
    __tablename__ = 'product'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    source = db.Column(db.String(255), nullable=True)
    category = db.Column(db.String(100), nullable=True)
    description = db.Column(db.Text, nullable=True)
    min_stock = db.Column(db.Integer, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())
    user = db.relationship('User', backref=db.backref('products', lazy=True))
"""

# Validation functions
def validate_username(username: str) -> tuple[bool, str]:
    if not username or len(username) < 3 or len(username) > 20:
        return False, 'Tên đăng nhập phải từ 3-20 ký tự'
    
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, 'Tên đăng nhập chỉ được chứa chữ cái, số và dấu gạch dưới'
    
    # old
    """if User.query.filter_by(username=username).first():  
        return False, 'Tên đăng nhập đã tồn tại' """    
    # new
    if users_collection.find_one({"username": username}):
        return False,'Tên đăng nhập đã tồn tại'

    return True, ''

def validate_email(email: str) -> tuple[bool, str]:
    if not email or len(email) > 120:
        return False, 'Email không được để trống và không quá 120 ký tự'
    
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        return False, 'Email không hợp lệ'
    #old
    """if User.query.filter_by(email=email).first():
        return False, 'Email đã được đăng ký'"""
    #new
    if users_collection.find_one({"email":email}):
        return False, 'Email đã được đăng ký'
    
    return True, ''

def validate_phone(phone: str) -> tuple[bool, str]:
    if not phone:
        return True, ''
        
    if not re.match(r'^[0-9]{10}$', phone):
        return False, 'Số điện thoại phải có 10 chữ số'
    # old
    """
    if User.query.filter_by(phone=phone).first():
        return False, 'Số điện thoại đã được đăng ký'"""
    # new
    if users_collection.find_one({"phone":phone}):
        return  False, 'Số điện thoại đã được đăng ký'

    return True, ''

# Decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        if 'user_id' not in session:
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

# what this ? -> decorator to check if user is admin
def admin_required(f):
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        if 'user_id' not in session or not session.get('is_admin'):
            return jsonify({'error': 'Admin access required'}), 403    # Admin -> add User['is_Admin'] in collection
        return f(*args, **kwargs)                                       # Session["is_Admin"]
    return decorated_function

# Auth Routes
@app.route('/')
def root():
    return redirect(url_for('login_page'))

@app.route('/auth/signup', methods=['GET'])
def signup_page():
    if 'user_id' in session:
        if session.get('is_admin'): # session['is_admin'] = True -> session.get('is_admin') = True
            return redirect(url_for('admin_management'))
        return redirect(url_for('inventory_page'))
    return render_template('auth/signup/signup.html')

@app.route('/auth/signup', methods=['POST'])
def signup():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'Invalid JSON'}), 400

    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    phone = data.get('phone')

    if not username or not email or not password:
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400

    # Validate fields
    username_valid, username_error = validate_username(username)
    if not username_valid:
        return jsonify({'success': False, 'error': username_error}), 400

    email_valid, email_error = validate_email(email)
    if not email_valid:
        return jsonify({'success': False, 'error': email_error}), 400

    if phone:
        phone_valid, phone_error = validate_phone(phone)
        if not phone_valid:
            return jsonify({'success': False, 'error': phone_error}), 400

    try:
        # Create new user
        hashed_password = generate_password_hash(password)
        new_user = {
            "username": username,
            "email": email,
            "password": hashed_password,
            "phone": phone,
            "is_admin": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        """db.session.add(new_user)
        db.session.commit()"""
        # Insert into MongoDB
        users_collection.insert_one(new_user)

        # Notify admins about new registration
            #admins = User.query.filter_by(is_admin=True).all()
        admins = users_collection.find({"is_admin": True})
        if admins:
            for admin in admins:
                notification = {
                    "user_id": admin["_id"],
                    "title": 'Người dùng mới đăng ký',
                    "message": f'Tài khoản mới được tạo với tên đăng nhập: {username}',
                    "is_read": False,
                    "created_at": datetime.utcnow()
                }
                notifications_collection.insert_one(notification)
                """notification = Notification(
                    user_id=admin.id,
                    title='Người dùng mới đăng ký',
                    message=f'Tài khoản mới được tạo với tên đăng nhập: {username}'
                )
                db.session.add(notification)
            db.session.commit()
            print(f"Notification sent to {len(admins)} admins about new user: {username}")
"""             
                
        return jsonify({'success': True, 'message': 'Registration successful'})
    except Exception as e:
        #db.session.rollback()
        print(f"Error in signup: {str(e)}")
        return jsonify({'success': False, 'error': 'Registration failed'}), 500

@app.route('/auth/login', methods=['GET'])
def login_page():
    if 'user_id' in session:
        if session.get('is_admin'):
            return redirect(url_for('admin_management'))
        return redirect(url_for('inventory_page'))
    return render_template('auth/login/login.html')

@app.route('/auth/login', methods=['POST'])
def login_api():
    data = request.get_json() # get_json() -> get data from request
    if not data:
        return jsonify({'success': False, 'error': 'Invalid JSON'}), 400
        
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'success': False, 'error': 'Vui lòng điền đầy đủ thông tin!'}), 400

    #user = User.query.filter_by(username=username).first() 
    users_collection.find_one({"username": username}) # find_one() -> find one document in collection
    if not user or not check_password_hash(user.password, password):
        return jsonify({'success': False, 'error': 'Tên đăng nhập hoặc mật khẩu không đúng!'}), 401

    session['user_id'] = user.id
    session['is_admin'] = user.is_admin
    session['username'] = user.username
    
    if user.is_admin:
        # Admins should never be redirected to inventory
        return jsonify({'success': True, 'redirect': '/main/admin/management'}), 200
    return jsonify({'success': True, 'redirect': '/main/user/inventory'}), 200

@app.route('/auth/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

# Main routes
@app.route('/profile')
@login_required
def profile_page():
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('login_page'))
    
    user_data = {
        'username': user.username,
        'email': user.email,
        'name': user.name,
        'date_of_birth': user.date_of_birth.isoformat() if user.date_of_birth else None,
        'phone': user.phone,
        'address': user.address,
        'is_admin': user.is_admin
    }
    
    if request.headers.get('Accept') == 'application/json':
        return jsonify({'user': user_data})
    return render_template('profile/profile.html', user=user_data)

@app.route('/api/check-username/<username>', methods=['GET'])
def check_username_exists(username):
    if not username:
        return jsonify({'exists': False})
    
    existing_user = User.query.filter(
        User.username == username,
        User.id != session.get('user_id')  # Don't count current user
    ).first()
    
    return jsonify({'exists': existing_user is not None})

@app.route('/api/check-email/<email>', methods=['GET'])
def check_email_exists(email):
    if not email:
        return jsonify({'exists': False})
    
    existing_user = User.query.filter(
        User.email == email,
        User.id != session.get('user_id')  # Don't count current user
    ).first()
    
    return jsonify({'exists': existing_user is not None})

@app.route('/settings')
@login_required
def settings_page():
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('login_page'))
    
    user_data = {
        'username': user.username,
        'email': user.email,
        'name': user.name,
        'date_of_birth': user.date_of_birth.isoformat() if user.date_of_birth else None,
        'phone': user.phone,
        'address': user.address,
        'is_admin': user.is_admin
    }
    
    return render_template('settings/settings.html', user=user_data)

@app.route('/api/profile/update', methods=['POST'])
@login_required
def update_profile():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'Invalid JSON'}), 400

    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({'success': False, 'error': 'Người dùng không tồn tại'}), 404

    try:
        # Update fields if provided in data
        if 'email' in data:
            new_email = data['email'].strip()
            if new_email != user.email:
                is_valid, error = validate_email(new_email)
                if not is_valid:
                    return jsonify({'success': False, 'error': error}), 400
                user.email = new_email

        if 'name' in data:
            if len(data['name'].strip()) < 2:
                return jsonify({'success': False, 'error': 'Họ và tên phải có ít nhất 2 ký tự'}), 400
            user.name = data['name'].strip()

        if 'phone' in data:
            if data['phone']:
                is_valid, error = validate_phone(data['phone'])
                if not is_valid:
                    return jsonify({'success': False, 'error': error}), 400
            user.phone = data['phone']

        if 'address' in data:
            user.address = data['address'].strip()

        if 'date_of_birth' in data and data['date_of_birth']:
            try:
                birth_date = datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date()
                
                # Validate date range
                today = datetime.now().date()
                age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
                
                if age < 0:
                    return jsonify({'success': False, 'error': 'Ngày sinh không thể ở tương lai'}), 400
                if age > 120:
                    return jsonify({'success': False, 'error': 'Năm sinh không hợp lý'}), 400
                
                user.date_of_birth = birth_date
            except ValueError:
                return jsonify({'success': False, 'error': 'Ngày sinh không hợp lệ'}), 400

        # Auto-update the updated_at timestamp
        user.updated_at = datetime.utcnow()
        
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Cập nhật thông tin thành công',
            'user': {
                'username': user.username,
                'email': user.email,
                'name': user.name,
                'date_of_birth': user.date_of_birth.strftime('%d/%m/%Y') if user.date_of_birth else None,
                'phone': user.phone,
                'address': user.address,
                'is_admin': user.is_admin
            }
        })

    except Exception as e:
        db.session.rollback()
        print(f"Error updating profile: {str(e)}")
        return jsonify({'success': False, 'error': 'Có lỗi khi cập nhật thông tin'}), 500

@app.route('/main/user/inventory')
@login_required
def inventory_page():
    if session.get('is_admin'):    # if session indicate admin -> redirect to admin page
        return redirect(url_for('admin_management'))
    
    user = User.query.get(session['user_id'])   # else -> get user from database
    if not user:   # if user not exist -> clear session and redirect to login page
        session.clear()
        return redirect(url_for('login_page'))
    # if user exist -> render template with user data
    return render_template('main/user/inventory.html', is_admin=user.is_admin) # is_admis is passed to template -> FE can use it

# Product API endpoints
@app.route('/api/inventory/products', methods=['GET'])
@login_required
def get_products():
    if session.get('is_admin'):
        return jsonify({'error': 'Admins không có quyền truy cập kho hàng'}), 403
        
    user_id = session['user_id']
    products = Product.query.filter_by(user_id=user_id).all()
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'price': p.price,
        'quantity': p.quantity,
        'source': p.source,
        'category': p.category or '',
        'description': p.description or '',
        'minStock': p.min_stock,
        'created_at': p.created_at.isoformat() if p.created_at else None
    } for p in products])

# Admin Product API endpoints
@app.route('/api/admin/products', methods=['GET'])
@admin_required
def get_all_products_admin():
    try:
        products = Product.query.all()
        return jsonify([{
            'id': p.id,
            'name': p.name,
            'price': p.price,
            'quantity': p.quantity,
            'source': p.source,
            'category': p.category or '',
            'description': p.description or '',
            'minStock': p.min_stock,
            'created_at': p.created_at.isoformat() if p.created_at else None
        } for p in products])
    except Exception as e:
        print(f"Error fetching all products (admin): {str(e)}")
        return jsonify({'error': 'Có lỗi khi tải danh sách sản phẩm'}), 500

@app.route('/api/admin/products/<int:product_id>', methods=['GET'])
@admin_required
def get_product_admin(product_id: int):
    try:
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'error': 'Không tìm thấy sản phẩm'}), 404
        return jsonify({
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'quantity': product.quantity,
            'source': product.source,
            'category': product.category or '',
            'description': product.description or '',
            'minStock': product.min_stock,
            'created_at': product.created_at.isoformat() if product.created_at else None
        })
    except Exception as e:
        print(f"Error fetching product (admin): {str(e)}")
        return jsonify({'error': 'Có lỗi khi tải thông tin sản phẩm'}), 500


@app.route('/api/admin/products', methods=['POST'])
@admin_required
def add_product_admin():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400

    try:
        name = data.get('name')
        price = data.get('price')
        quantity = data.get('amount', 0) # Changed from 'quantity' to 'amount'
        description = data.get('description')
        source = data.get('source')
        category = data.get('category')
        min_stock = data.get('minStock', 0)

        if not name or price is None or quantity is None:
            return jsonify({'error': 'Tên, giá và số lượng sản phẩm là bắt buộc'}), 400

        try:
            price = float(price)
            quantity = int(quantity)
            min_stock = int(min_stock)
        except (ValueError, TypeError):
            return jsonify({'error': 'Giá, số lượng và tồn kho tối thiểu phải là số'}), 400

        if price < 0 or min_stock < 0: # Removed quantity < 0 check
            return jsonify({'error': 'Giá và tồn kho tối thiểu không được âm'}), 400

        # Assuming admin adds products, associate with the admin user
        admin_user_id = session.get('user_id')
        if not admin_user_id:
             return jsonify({'error': 'Admin user not found in session'}), 500 # Should not happen with @admin_required

        product = Product(
            name=name,
            price=price,
            quantity=quantity,
            source=source,
            category=category,
            description=description,
            min_stock=min_stock,
            user_id=admin_user_id # Associate with the admin user
        )
        db.session.add(product)
        db.session.commit()

        return jsonify({'message': 'Product added successfully', 'id': product.id}), 201
    except Exception as e:
        db.session.rollback()
        print(f"Error adding product (admin): {str(e)}")
        return jsonify({'error': 'Có lỗi khi thêm sản phẩm'}), 500


@app.route('/api/admin/products/<int:product_id>', methods=['PUT'])
@admin_required
def update_product_admin(product_id: int):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Không tìm thấy sản phẩm'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400

    try:
        # Update fields if provided in data
        if 'name' in data:
            product.name = data['name']
        if 'price' in data:
            try:
                product.price = float(data['price'])
                if product.price < 0:
                     return jsonify({'error': 'Giá sản phẩm không được âm'}), 400
            except (ValueError, TypeError):
                 return jsonify({'error': 'Giá sản phẩm phải là số'}), 400
        if 'quantity' in data:
            try:
                product.quantity = int(data['quantity'])
                if product.quantity < 0:
                     return jsonify({'error': 'Số lượng sản phẩm không được âm'}), 400
            except (ValueError, TypeError):
                 return jsonify({'error': 'Số lượng sản phẩm phải là số nguyên'}), 400
        if 'description' in data:
            product.description = data['description']
        if 'source' in data:
            product.source = data['source']
        if 'category' in data:
            product.category = data['category']
        if 'minStock' in data:
             try:
                product.min_stock = int(data['minStock'])
                if product.min_stock < 0:
                     return jsonify({'error': 'Tồn kho tối thiểu không được âm'}), 400
             except (ValueError, TypeError):
                 return jsonify({'error': 'Tồn kho tối thiểu phải là số nguyên'}), 400

        db.session.commit()
        # Notify admins about the product update by an admin
        admin_username = session.get('username', 'Admin không xác định')
        notify_admins('Sản phẩm đã được cập nhật (Admin)', f'Sản phẩm "{product.name}" (ID: {product_id}) đã được cập nhật bởi admin {admin_username}.')
        return jsonify({'message': 'Product updated successfully'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error updating product (admin): {str(e)}")
        return jsonify({'error': 'Có lỗi khi cập nhật sản phẩm'}), 500

@app.route('/api/admin/products/<int:product_id>', methods=['DELETE'])
@admin_required
def delete_product_admin(product_id: int):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Không tìm thấy sản phẩm'}), 404

    try:
        db.session.delete(product)
        db.session.commit()
        # Notify admins about the product deletion by an admin
        admin_username = session.get('username', 'Admin không xác định')
        notify_admins('Sản phẩm đã bị xóa (Admin)', f'Sản phẩm (ID: {product_id}) đã bị xóa bởi admin {admin_username}.')
        return jsonify({'message': 'Product deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting product (admin): {str(e)}")
        return jsonify({'error': 'Có lỗi khi xóa sản phẩm'}), 500


@app.route('/api/inventory/products', methods=['POST'])
@login_required
def add_product():
    if not session.get('user_id'):
        return jsonify({'error': 'Authentication required'}), 401
        
    user_id = session['user_id']
    if session.get('is_admin'):
        return jsonify({'error': 'Admins không có quyền thêm sản phẩm'}), 403
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400
        
    try:
        name = data.get('name')
        price = data.get('price')
        quantity = data.get('quantity', 0)
        
        if not name or not price:
            return jsonify({'error': 'Tên và giá sản phẩm là bắt buộc'}), 400
            
        try:
            price = float(price)
            quantity = int(quantity)
            min_stock = int(data.get('minStock', 0))
        except (ValueError, TypeError):
            return jsonify({'error': 'Giá, số lượng và tồn kho tối thiểu phải là số'}), 400
            
        if price < 0 or quantity < 0 or min_stock < 0:
            return jsonify({'error': 'Giá, số lượng và tồn kho tối thiểu không được âm'}), 400
            
        product = Product(
            name=name,
            price=price,
            quantity=quantity,
            source=data.get('source'),
            category=data.get('category'),
            description=data.get('description'),
            min_stock=min_stock,
            user_id=user_id
        )
        db.session.add(product)
        db.session.commit()

        # Notify admins about new product
        notify_admins(
            'Sản phẩm mới được thêm',
            f'Người dùng {session["username"]} đã thêm sản phẩm mới: {product.name}'
        )

        return jsonify({'message': 'Product added successfully', 'id': product.id})
    except Exception as e:
        db.session.rollback()
        print(f"Error creating product: {str(e)}")
        return jsonify({'error': 'Có lỗi khi thêm sản phẩm'}), 500

@app.route('/api/inventory/products/<int:product_id>', methods=['PUT'])
@login_required
def update_product(product_id: int):
    if session.get('is_admin'):
        return jsonify({'error': 'Admins không có quyền cập nhật sản phẩm'}), 403
        
    user_id = session['user_id']
    product = Product.query.filter_by(id=product_id, user_id=user_id).first()
    if not product:
        return jsonify({'error': 'Không tìm thấy sản phẩm'}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400
        
    try:
        product.name = data.get('name', product.name)
        product.price = data.get('price', product.price)
        product.quantity = data.get('quantity', product.quantity)
        product.source = data.get('source', product.source)
        product.category = data.get('category', product.category)
        product.description = data.get('description', product.description)
        product.min_stock = data.get('minStock', product.min_stock)
        
        db.session.commit()

        # Check if quantity is below min_stock after update
        if product.quantity <= product.min_stock:
            # Notify product owner about low stock
            create_notification(
                user_id,
                'Cảnh báo: Hàng sắp hết',
                f'Sản phẩm {product.name} sắp hết hàng (Còn lại: {product.quantity})'
            )

            # Notify admins about low stock products
            notify_admins(
                'Cảnh báo: Sản phẩm sắp hết hàng',
                f'Sản phẩm {product.name} của người dùng {session["username"]} sắp hết hàng (Còn lại: {product.quantity})'
            )

        # Notify admins about the product update
        username = session.get('username', 'Người dùng không xác định')
        notify_admins('Sản phẩm đã được cập nhật', f'Sản phẩm "{product.name}" (ID: {product_id}) đã được cập nhật bởi {username}.')
        # Notify admins about the product update
        username = session.get('username', 'Người dùng không xác định')
        notify_admins('Sản phẩm đã được cập nhật', f'Sản phẩm "{product.name}" (ID: {product_id}) đã được cập nhật bởi {username}.')
        return jsonify({'message': 'Product updated successfully'})
    except Exception as e:
        db.session.rollback()
        print(f"Error updating product: {str(e)}")
        return jsonify({'error': 'Có lỗi khi cập nhật sản phẩm'}), 500

@app.route('/api/inventory/products/<int:product_id>', methods=['DELETE'])
@login_required
def delete_product(product_id: int):
    if session.get('is_admin'):
        return jsonify({'error': 'Admins không có quyền xóa sản phẩm'}), 403
        
    user_id = session['user_id']
    product = Product.query.filter_by(id=product_id, user_id=user_id).first()
    if not product:
        return jsonify({'error': 'Không tìm thấy sản phẩm'}), 404
    
    try:
        db.session.delete(product)
        db.session.commit()
        # Notify admins about the product deletion
        username = session.get('username', 'Người dùng không xác định')
        notify_admins('Sản phẩm đã bị xóa', f'Sản phẩm (ID: {product_id}) đã bị xóa bởi {username}.')
        return jsonify({'message': 'Product deleted successfully'})
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting product: {str(e)}")
        return jsonify({'error': 'Có lỗi khi xóa sản phẩm'}), 500

# Admin routes
@app.route('/main/admin/management')
@login_required
@admin_required
def admin_management():
    return render_template('main/admin/management.html')

@app.route('/api/admin/users', methods=['GET'])
@login_required
@admin_required
def get_all_users():
    try:
        users = User.query.all()
        return jsonify([{
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'phone': user.phone,
            'is_admin': user.is_admin
        } for user in users])
    except Exception as e:
        print(f"Error fetching users: {str(e)}")
        return jsonify({'error': 'Có lỗi khi tải danh sách người dùng'}), 500

@app.route('/api/admin/users/<int:user_id>', methods=['PUT'])
@login_required
@admin_required
def update_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'Không tìm thấy người dùng'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dữ liệu không hợp lệ'}), 400

    try:
        # Only allow password and admin status changes
        if 'password' in data and data['password']:
            user.password = generate_password_hash(data['password'])

        # Update admin status
        if 'is_admin' in data:
            # Prevent removing admin status from last admin
            if not data['is_admin'] and user.is_admin:
                admin_count = User.query.filter_by(is_admin=True).count()
                if admin_count <= 1:
                    return jsonify({'error': 'Không thể xóa quyền admin của người dùng cuối cùng'}), 400
            user.is_admin = data['is_admin']

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Cập nhật thông tin thành công',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'phone': user.phone,
                'is_admin': user.is_admin
            }
        })

    except Exception as e:
        db.session.rollback()
        print(f"Error updating user: {str(e)}")
        return jsonify({'error': 'Có lỗi khi cập nhật thông tin'}), 500

@app.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'Không tìm thấy người dùng'}), 404

    # Prevent deleting the last admin
    if user.is_admin:
        admin_count = User.query.filter_by(is_admin=True).count()
        if admin_count <= 1:
            return jsonify({'error': 'Không thể xóa admin cuối cùng'}), 400

    # Prevent self-deletion
    if user_id == session['user_id']:
        return jsonify({'error': 'Không thể tự xóa tài khoản của mình'}), 400

    try:
        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': 'Xóa người dùng thành công'})
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting user: {str(e)}")
        return jsonify({'error': 'Có lỗi khi xóa người dùng'}), 500

def create_notification(user_id, title, message):
    """Helper function to create notifications"""
    if not User.query.get(user_id):
        print(f"User {user_id} not found")
        return False
        
    try:
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message
        )
        db.session.add(notification)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Error creating notification: {str(e)}")
        return False

# Helper function to notify admins
def notify_admins(title, message):
    try:
        admins = User.query.filter_by(is_admin=True).all()
        if not admins:
            print("No admin users found")
            return
            
        for admin in admins:
            create_notification(admin.id, title, message)
        db.session.commit()
        print(f"Notification sent to {len(admins)} admins: {title}")
    except Exception as e:
        db.session.rollback()
        print(f"Error in notify_admins: {str(e)}")

# Helper function to notify specific users
def notify_users(user_ids, title, message):
    for user_id in user_ids:
        create_notification(user_id, title, message)

# Notification endpoints
@app.route('/api/admin/notifications/send', methods=['POST'])
@login_required
@admin_required
def send_notification():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400
    
    try:
        title = data.get('title')
        message = data.get('message')
        recipient_type = data.get('recipient_type')
        recipient_ids = data.get('recipient_ids')

        if not title or not message or not recipient_type:
            return jsonify({'error': 'Missing required fields'}), 400

        if recipient_type == 'all':
            users = User.query.filter_by(is_admin=False).all()
            for user in users:
                create_notification(user.id, title, message)
        elif recipient_type == 'select' and recipient_ids:
            for user_id in recipient_ids:
                create_notification(user_id, title, message)
        else:
            return jsonify({'error': 'Invalid recipient type or missing recipient IDs'}), 400

        return jsonify({'message': 'Notifications sent successfully'})
    except Exception as e:
        print(f"Error sending notifications: {str(e)}")
        return jsonify({'error': 'Failed to send notifications'}), 500

@app.route('/api/notifications', methods=['GET'])
@login_required
def get_notifications():
    try:
        user_id = session['user_id']
        notifications = Notification.query.filter_by(user_id=user_id).order_by(Notification.created_at.desc()).all()
        
        if not notifications:
            return jsonify([])
            
        return jsonify([{
            'id': n.id,
            'title': n.title,
            'message': n.message,
            'is_read': n.is_read,
            'created_at': n.created_at.isoformat()
        } for n in notifications])
    except Exception as e:
        print(f"Error fetching notifications: {str(e)}")
        return jsonify({'error': 'Failed to fetch notifications'}), 500

@app.route('/api/notifications/mark-read', methods=['POST'])
@login_required
def mark_notifications_read():
    try:
        user_id = session['user_id']
        Notification.query.filter_by(user_id=user_id).update({'is_read': True})
        db.session.commit()
        return jsonify({'message': 'Notifications marked as read'})
    except Exception as e:
        db.session.rollback()
        print(f"Error marking notifications as read: {str(e)}")
        return jsonify({'error': 'Có lỗi khi cập nhật thông báo'}), 500

@app.route('/api/notifications/<int:notification_id>/mark-read', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    try:
        user_id = session['user_id']
        notification = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
        if notification:
            notification.is_read = True
            db.session.commit()
            return jsonify({'message': 'Notification marked as read'})
        return jsonify({'error': 'Không tìm thấy thông báo'}), 404
    except Exception as e:
        db.session.rollback()
        print(f"Error marking notification as read: {str(e)}")
        return jsonify({'error': 'Có lỗi khi cập nhật thông báo'}), 500

if __name__ == '__main__':
    # Add validation endpoints
    @app.route('/api/check-username', methods=['POST'])
    def check_username():
        data = request.get_json()
        if not data or 'username' not in data:
            return jsonify({'valid': False, 'error': 'Missing username'}), 400

        username = data['username']
        is_valid, error = validate_username(username)
        return jsonify({'valid': is_valid, 'error': error})

    @app.route('/api/check-email', methods=['POST'])
    def check_email():
        data = request.get_json()
        if not data or 'email' not in data:
            return jsonify({'valid': False, 'error': 'Missing email'}), 400

        email = data['email']
        is_valid, error = validate_email(email)
        return jsonify({'valid': is_valid, 'error': error})

    with app.app_context():
        try:
            db.create_all()
            print("Database connected successfully")

            # Check both username and email for admin account
            admin = User.query.filter(
                (User.username == 'admin123') | 
                (User.email == 'admin@example.com')
            ).first()
            
            if not admin:
                admin = User(
                    username='admin123',
                    email='admin@example.com',
                    password=generate_password_hash('k051205'),
                    is_admin=True
                )
                db.session.add(admin)
                db.session.commit()
                print("Admin account created successfully")
            else:
                print("Admin account already exists")
                
        except Exception as e:
            print(f"Database error: {str(e)}")
            exit(1)
    
    app.run(debug=True)