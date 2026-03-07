from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import random
import string
import time

app = Flask(__name__)
app.secret_key = 'freedomain-secret-key-2024'

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///freedomain.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Login manager setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    domains = db.relationship('Domain', backref='owner', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Domain(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    registration_date = db.Column(db.DateTime, nullable=True)
    expiry_date = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='registered')

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    domain_name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, default=0.0)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Domain pricing data
DOMAIN_PRICING = {
    '.free': {'registration': 0, 'renewal': 0, 'transfer': 0},
    '.online': {'registration': 9.99, 'renewal': 9.99, 'transfer': 5.99},
    '.site': {'registration': 12.99, 'renewal': 12.99, 'transfer': 7.99},
    '.web': {'registration': 14.99, 'renewal': 14.99, 'transfer': 9.99},
    '.tech': {'registration': 19.99, 'renewal': 19.99, 'transfer': 12.99},
}

# Initialize database
with app.app_context():
    db.create_all()

# Base template for professional UI
BASE_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} - FreeDomain</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; background: #0a0a0f; color: #e5e5e5; min-height: 100vh; }
        :root {
            --primary: #6366f1;
            --primary-hover: #818cf8;
            --secondary: #22d3ee;
            --success: #10b981;
            --danger: #ef4444;
            --warning: #f59e0b;
            --dark: #0a0a0f;
            --card-bg: #18181b;
            --border: #27272a;
            --text-muted: #a1a1aa;
        }
        .navbar {
            background: rgba(24, 24, 27, 0.95);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid var(--border);
            padding: 1rem 2rem;
            position: sticky;
            top: 0;
            z-index: 100;
        }
        .navbar-content {
            max-width: 1400px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .logo {
            font-size: 1.5rem;
            font-weight: 700;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-decoration: none;
        }
        .nav-links {
            display: flex;
            gap: 2rem;
            align-items: center;
        }
        .nav-link {
            color: var(--text-muted);
            text-decoration: none;
            font-weight: 500;
            transition: color 0.2s;
        }
        .nav-link:hover, .nav-link.active { color: var(--primary); }
        .btn {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.625rem 1.25rem;
            border-radius: 0.5rem;
            font-weight: 500;
            font-size: 0.875rem;
            cursor: pointer;
            transition: all 0.2s;
            border: none;
            text-decoration: none;
        }
        .btn-primary {
            background: var(--primary);
            color: white;
        }
        .btn-primary:hover { background: var(--primary-hover); transform: translateY(-1px); }
        .btn-outline {
            background: transparent;
            border: 1px solid var(--border);
            color: var(--text-muted);
        }
        .btn-outline:hover { border-color: var(--primary); color: var(--primary); }
        .btn-danger { background: var(--danger); color: white; }
        .btn-success { background: var(--success); color: white; }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }
        .hero {
            text-align: center;
            padding: 4rem 0;
            position: relative;
            overflow: hidden;
        }
        .hero::before {
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 600px;
            height: 600px;
            background: radial-gradient(circle, rgba(99, 102, 241, 0.15) 0%, transparent 70%);
            pointer-events: none;
        }
        .hero h1 {
            font-size: 3.5rem;
            font-weight: 700;
            margin-bottom: 1rem;
            background: linear-gradient(135deg, #fff 0%, #a1a1aa 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .hero p {
            font-size: 1.25rem;
            color: var(--text-muted);
            margin-bottom: 2rem;
        }
        .search-box {
            max-width: 600px;
            margin: 0 auto;
            position: relative;
        }
        .search-input {
            width: 100%;
            padding: 1rem 1.5rem;
            padding-right: 8rem;
            font-size: 1rem;
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 1rem;
            color: white;
            outline: none;
            transition: border-color 0.2s;
        }
        .search-input:focus { border-color: var(--primary); }
        .search-btn {
            position: absolute;
            right: 0.5rem;
            top: 50%;
            transform: translateY(-50%);
        }
        .grid {
            display: grid;
            gap: 1.5rem;
        }
        .grid-3 { grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); }
        .grid-4 { grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); }
        .card {
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 1rem;
            padding: 1.5rem;
            transition: all 0.3s;
        }
        .card:hover { border-color: var(--primary); transform: translateY(-2px); }
        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
        }
        .card-title { font-size: 1.25rem; font-weight: 600; }
        .badge {
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
        }
        .badge-available { background: rgba(16, 185, 129, 0.2); color: var(--success); }
        .badge-taken { background: rgba(239, 68, 68, 0.2); color: var(--danger); }
        .badge-premium { background: rgba(245, 158, 11, 0.2); color: var(--warning); }
        .price { font-size: 1.5rem; font-weight: 700; color: var(--success); }
        .price-original { font-size: 1rem; text-decoration: line-through; color: var(--text-muted); }
        .form-group { margin-bottom: 1.5rem; }
        .form-label { display: block; margin-bottom: 0.5rem; font-weight: 500; color: var(--text-muted); }
        .form-input {
            width: 100%;
            padding: 0.75rem 1rem;
            font-size: 1rem;
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 0.5rem;
            color: white;
            outline: none;
            transition: border-color 0.2s;
        }
        .form-input:focus { border-color: var(--primary); }
        .alert {
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
        }
        .alert-success { background: rgba(16, 185, 129, 0.1); border: 1px solid var(--success); color: var(--success); }
        .alert-error { background: rgba(239, 68, 68, 0.1); border: 1px solid var(--danger); color: var(--danger); }
        .table { width: 100%; border-collapse: collapse; }
        .table th, .table td { padding: 1rem; text-align: left; border-bottom: 1px solid var(--border); }
        .table th { color: var(--text-muted); font-weight: 500; font-size: 0.875rem; }
        .table tr:hover { background: rgba(99, 102, 241, 0.05); }
        .cart-summary {
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 1rem;
            padding: 2rem;
        }
        .total-row {
            display: flex;
            justify-content: space-between;
            font-size: 1.25rem;
            font-weight: 600;
            padding-top: 1rem;
            border-top: 1px solid var(--border);
            margin-top: 1rem;
        }
        .features-section {
            padding: 4rem 0;
        }
        .feature-icon {
            width: 48px;
            height: 48px;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            border-radius: 1rem;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
            margin-bottom: 1rem;
        }
        .feature-card h3 { font-size: 1.25rem; margin-bottom: 0.5rem; }
        .feature-card p { color: var(--text-muted); }
        .pricing-card {
            text-align: center;
            padding: 2rem;
        }
        .pricing-card.featured { border: 2px solid var(--primary); position: relative; }
        .pricing-card.featured::before {
            content: 'MOST POPULAR';
            position: absolute;
            top: -12px;
            left: 50%;
            transform: translateX(-50%);
            background: var(--primary);
            padding: 0.25rem 1rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
        }
        .pricing-amount { font-size: 2.5rem; font-weight: 700; margin: 1rem 0; }
        .pricing-period { color: var(--text-muted); }
        .pricing-features { list-style: none; padding: 1rem 0; text-align: left; }
        .pricing-features li { padding: 0.5rem 0; color: var(--text-muted); }
        .pricing-features li::before { content: '✓'; color: var(--success); margin-right: 0.5rem; }
        .domain-ext { font-size: 2rem; font-weight: 700; color: var(--primary); }
        .domain-name { font-size: 1.25rem; color: var(--text-muted); }
        .footer {
            background: var(--card-bg);
            border-top: 1px solid var(--border);
            padding: 2rem;
            text-align: center;
            color: var(--text-muted);
            margin-top: 4rem;
        }
        .stats { display: flex; gap: 3rem; justify-content: center; padding: 2rem 0; }
        .stat-item { text-align: center; }
        .stat-value { font-size: 2rem; font-weight: 700; color: var(--primary); }
        .stat-label { color: var(--text-muted); font-size: 0.875rem; }
        .page-header { margin-bottom: 2rem; }
        .page-title { font-size: 2rem; font-weight: 700; margin-bottom: 0.5rem; }
        .page-subtitle { color: var(--text-muted); }
        .auth-container { max-width: 400px; margin: 4rem auto; }
        .auth-card { padding: 2rem; }
        .cart-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 1rem;
            border-bottom: 1px solid var(--border);
        }
        .cart-item:last-child { border-bottom: none; }
        .domain-tag {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            background: rgba(99, 102, 241, 0.2);
            border-radius: 0.25rem;
            font-family: monospace;
            color: var(--secondary);
        }
        .empty-state {
            text-align: center;
            padding: 4rem 2rem;
            color: var(--text-muted);
        }
        .empty-state-icon { font-size: 4rem; margin-bottom: 1rem; }
    </style>
</head>
<body>
    <nav class="navbar">
        <div class="navbar-content">
            <a href="/" class="logo">FreeDomain</a>
            <div class="nav-links">
                <a href="/" class="nav-link {{ 'active' if request.path == '/' else '' }}">Home</a>
                <a href="/domains" class="nav-link {{ 'active' if request.path == '/domains' else '' }}">Domains</a>
                <a href="/search" class="nav-link {{ 'active' if request.path == '/search' else '' }}">Search</a>
                <a href="/pricing" class="nav-link {{ 'active' if request.path == '/pricing' else '' }}">Pricing</a>
                {% if current_user.is_authenticated %}
                    <a href="/dashboard" class="nav-link {{ 'active' if request.path == '/dashboard' else '' }}">Dashboard</a>
                    <a href="/cart" class="nav-link {{ 'active' if request.path == '/cart' else '' }}">Cart ({{ cart_count }})</a>
                    <span style="color: var(--text-muted);">{{ current_user.username }}</span>
                    <a href="/logout" class="btn btn-outline">Logout</a>
                {% else %}
                    <a href="/login" class="btn btn-outline">Login</a>
                    <a href="/register" class="btn btn-primary">Get Started</a>
                {% endif %}
            </div>
        </div>
    </nav>

    {% block content %}{% endblock %}

    <footer class="footer">
        <p>&copy; 2024 FreeDomain - DigitalPlat. All rights reserved.</p>
    </footer>
</body>
</html>
"""

@app.context_processor
def inject_cart_count():
    cart_count = 0
    if current_user.is_authenticated:
        cart_count = Cart.query.filter_by(user_id=current_user.id).count()
    return dict(cart_count=cart_count)

# Routes
@app.route('/')
def home():
    html = BASE_TEMPLATE.replace('{% block content %}{% endblock %}', '''
    <div class="container">
        <div class="hero">
            <h1>Find Your Perfect Domain</h1>
            <p>Start your online presence with a free domain. Simple, fast, and secure.</p>
            <div class="search-box">
                <form action="/search" method="GET">
                    <input type="text" name="domain" class="search-input" placeholder="Search for your domain..." required>
                    <button type="submit" class="btn btn-primary search-btn">Search</button>
                </form>
            </div>
        </div>

        <div class="stats">
            <div class="stat-item">
                <div class="stat-value">10K+</div>
                <div class="stat-label">Domains Registered</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">5K+</div>
                <div class="stat-label">Happy Users</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">99.9%</div>
                <div class="stat-label">Uptime</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">24/7</div>
                <div class="stat-label">Support</div>
            </div>
        </div>

        <div class="features-section">
            <h2 style="text-align: center; margin-bottom: 2rem; font-size: 2rem;">Why Choose FreeDomain?</h2>
            <div class="grid grid-3">
                <div class="card feature-card">
                    <div class="feature-icon">🚀</div>
                    <h3>Instant Setup</h3>
                    <p>Get your domain up and running in seconds. No waiting, no hassle.</p>
                </div>
                <div class="card feature-card">
                    <div class="feature-icon">🔒</div>
                    <h3>Secure & Reliable</h3>
                    <p>Enterprise-grade security with 99.9% uptime guarantee.</p>
                </div>
                <div class="card feature-card">
                    <div class="feature-icon">💰</div>
                    <h3>Free & Premium</h3>
                    <p>Start with free domains, upgrade to premium when you need more.</p>
                </div>
                <div class="card feature-card">
                    <div class="feature-icon">📱</div>
                    <h3>Easy Management</h3>
                    <p>Simple dashboard to manage all your domains in one place.</p>
                </div>
                <div class="card feature-card">
                    <div class="feature-icon">🌍</div>
                    <h3>Global DNS</h3>
                    <p>Fast global DNS servers ensure your site loads everywhere.</p>
                </div>
                <div class="card feature-card">
                    <div class="feature-icon">💁</div>
                    <h3>24/7 Support</h3>
                    <p>Our team is always here to help you with any questions.</p>
                </div>
            </div>
        </div>
    </div>
    ''')
    return render_template_string(html, title='Home')

@app.route('/domains')
def domains():
    all_domains = Domain.query.all()
    premium_extensions = ['.online', '.site', '.web', '.tech']

    domains_data = []
    for d in all_domains:
        ext = '.' + d.name.split('.')[-1] if '.' in d.name else ''
        domains_data.append({
            'name': d.name,
            'status': 'taken' if d.user_id else 'available',
            'price': 'FREE' if ext == '.free' else f'${DOMAIN_PRICING.get(ext, {}).get("registration", 0)}',
            'premium': ext in premium_extensions
        })

    # Add some sample available domains
    sample_domains = [
        {'name': 'hello.free', 'status': 'available', 'price': 'FREE', 'premium': False},
        {'name': 'awesome.free', 'status': 'available', 'price': 'FREE', 'premium': False},
        {'name': 'mysite.online', 'status': 'available', 'price': '$9.99', 'premium': True},
        {'name': 'blog.site', 'status': 'available', 'price': '$12.99', 'premium': True},
    ]

    for sd in sample_domains:
        if not any(d['name'] == sd['name'] for d in domains_data):
            domains_data.append(sd)

    html = BASE_TEMPLATE.replace('{% block content %}{% endblock %}', '''
    <div class="container">
        <div class="page-header">
            <h1 class="page-title">Available Domains</h1>
            <p class="page-subtitle">Browse our collection of premium and free domains</p>
        </div>

        <div class="grid grid-4">
            {% for domain in domains %}
            <div class="card">
                <div class="card-header">
                    <span class="domain-tag">{{ domain.name }}</span>
                    <span class="badge badge-{{ domain.status }}">{{ domain.status }}</span>
                </div>
                <div class="price">{{ domain.price }}</div>
                {% if domain.premium %}
                <span class="badge badge-premium" style="margin-top: 0.5rem;">Premium</span>
                {% endif %}
                {% if domain.status == 'available' %}
                <form action="/cart/add" method="POST" style="margin-top: 1rem;">
                    <input type="hidden" name="domain_name" value="{{ domain.name }}">
                    <input type="hidden" name="price" value="{{ domain.price }}">
                    <button type="submit" class="btn btn-primary" style="width: 100%;">Add to Cart</button>
                </form>
                {% endif %}
            </div>
            {% endfor %}
        </div>
    </div>
    ''')
    return render_template_string(html, title='Domains', domains=domains_data)

@app.route('/search')
def search():
    query = request.args.get('domain', '')
    results = []

    if query:
        # Simulate domain availability check
        time.sleep(0.3)  # Simulate API delay
        extensions = ['.free', '.online', '.site', '.web', '.tech']

        for ext in extensions:
            domain_name = f"{query}{ext}"
            # Randomly mark some as taken for simulation
            is_available = random.choice([True, True, True, False])
            price = 'FREE' if ext == '.free' else f'${DOMAIN_PRICING.get(ext, {}).get("registration", 0)}'

            # Check if domain exists in database
            existing = Domain.query.filter_by(name=domain_name).first()
            if existing:
                is_available = False

            results.append({
                'name': domain_name,
                'available': is_available,
                'price': price,
                'premium': ext != '.free'
            })

    html = BASE_TEMPLATE.replace('{% block content %}{% endblock %}', '''
    <div class="container">
        <div class="page-header">
            <h1 class="page-title">Domain Search</h1>
            <p class="page-subtitle">Find the perfect domain for your project</p>
        </div>

        <div class="search-box" style="margin-bottom: 2rem;">
            <form action="/search" method="GET">
                <input type="text" name="domain" class="search-input" placeholder="Enter domain name..." value="{{ query }}" required>
                <button type="submit" class="btn btn-primary search-btn">Search</button>
            </form>
        </div>

        {% if results %}
        <div class="grid grid-3">
            {% for result in results %}
            <div class="card">
                <div class="card-header">
                    <span class="domain-tag">{{ result.name }}</span>
                    <span class="badge badge-{{ 'available' if result.available else 'taken' }}">
                        {{ 'Available' if result.available else 'Taken' }}
                    </span>
                </div>
                <div class="price">{{ result.price }}</div>
                {% if result.premium %}<span class="badge badge-premium">Premium</span>{% endif %}
                {% if result.available %}
                <form action="/cart/add" method="POST" style="margin-top: 1rem;">
                    <input type="hidden" name="domain_name" value="{{ result.name }}">
                    <input type="hidden" name="price" value="{{ result.price }}">
                    <button type="submit" class="btn btn-primary" style="width: 100%;">Add to Cart</button>
                </form>
                {% endif %}
            </div>
            {% endfor %}
        </div>
        {% endif %}
    </div>
    ''')
    return render_template_string(html, title='Search', query=query, results=results)

@app.route('/pricing')
def pricing():
    pricing_plans = [
        {
            'name': 'Free',
            'price': 0,
            'features': ['.free domain', 'Basic DNS management', 'Email support', '1 domain'],
            'featured': False
        },
        {
            'name': 'Starter',
            'price': 4.99,
            'features': ['.online domain', 'Advanced DNS', 'Priority support', '5 domains', 'DNS forwarding'],
            'featured': True
        },
        {
            'name': 'Pro',
            'price': 9.99,
            'features': ['.site/.web domain', 'Premium DNS', '24/7 support', 'Unlimited domains', 'Domain forwarding', 'WHOIS privacy'],
            'featured': False
        },
        {
            'name': 'Business',
            'price': 19.99,
            'features': ['.tech domain', 'Enterprise DNS', 'Dedicated support', 'Unlimited domains', 'All features', 'SSL certificate setup', 'Priority'],
            'featured': False
        }
    ]

    html = BASE_TEMPLATE.replace('{% block content %}{% endblock %}', '''
    <div class="container">
        <div class="page-header" style="text-align: center;">
            <h1 class="page-title">Simple, Transparent Pricing</h1>
            <p class="page-subtitle">Choose the plan that's right for you</p>
        </div>

        <div class="grid grid-4">
            {% for plan in plans %}
            <div class="card pricing-card {{ 'featured' if plan.featured else '' }}">
                <h3>{{ plan.name }}</h3>
                <div class="pricing-amount">
                    ${{ plan.price }}<span class="pricing-period">/month</span>
                </div>
                <ul class="pricing-features">
                    {% for feature in plan.features %}
                    <li>{{ feature }}</li>
                    {% endfor %}
                </ul>
                <a href="/register" class="btn {{ 'btn-primary' if plan.featured else 'btn-outline' }}" style="width: 100%;">Get Started</a>
            </div>
            {% endfor %}
        </div>

        <div style="margin-top: 4rem;">
            <h2 style="text-align: center; margin-bottom: 2rem;">Domain Extension Prices</h2>
            <div class="card">
                <table class="table">
                    <thead>
                        <tr>
                            <th>Extension</th>
                            <th>Registration</th>
                            <th>Renewal</th>
                            <th>Transfer</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for ext, prices in pricing.items() %}
                        <tr>
                            <td><span class="domain-tag">{{ ext }}</span></td>
                            <td>{% if prices.registration == 0 %}FREE{% else %}${{ prices.registration }}{% endif %}</td>
                            <td>{% if prices.renewal == 0 %}FREE{% else %}${{ prices.renewal }}{% endif %}</td>
                            <td>{% if prices.transfer == 0 %}FREE{% else %}${{ prices.transfer }}{% endif %}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    ''')
    return render_template_string(html, title='Pricing', plans=pricing_plans, pricing=DOMAIN_PRICING)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash('Passwords do not match!', 'error')
        elif User.query.filter_by(username=username).first():
            flash('Username already exists!', 'error')
        elif User.query.filter_by(email=email).first():
            flash('Email already exists!', 'error')
        else:
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))

    html = BASE_TEMPLATE.replace('{% block content %}{% endblock %}', '''
    <div class="container">
        <div class="auth-container">
            <div class="card auth-card">
                <h2 style="text-align: center; margin-bottom: 2rem;">Create Account</h2>

                {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                {% for category, message in messages %}
                <div class="alert alert-{{ category }}">{{ message }}</div>
                {% endfor %}
                {% endif %}
                {% endwith %}

                <form method="POST">
                    <div class="form-group">
                        <label class="form-label">Username</label>
                        <input type="text" name="username" class="form-input" required>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Email</label>
                        <input type="email" name="email" class="form-input" required>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Password</label>
                        <input type="password" name="password" class="form-input" required>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Confirm Password</label>
                        <input type="password" name="confirm_password" class="form-input" required>
                    </div>
                    <button type="submit" class="btn btn-primary" style="width: 100%;">Create Account</button>
                </form>
                <p style="text-align: center; margin-top: 1rem; color: var(--text-muted);">
                    Already have an account? <a href="/login" style="color: var(--primary);">Login</a>
                </p>
            </div>
        </div>
    </div>
    ''')
    return render_template_string(html, title='Register')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            flash('Welcome back!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password!', 'error')

    html = BASE_TEMPLATE.replace('{% block content %}{% endblock %}', '''
    <div class="container">
        <div class="auth-container">
            <div class="card auth-card">
                <h2 style="text-align: center; margin-bottom: 2rem;">Welcome Back</h2>

                {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                {% for category, message in messages %}
                <div class="alert alert-{{ category }}">{{ message }}</div>
                {% endfor %}
                {% endif %}
                {% endwith %}

                <form method="POST">
                    <div class="form-group">
                        <label class="form-label">Username</label>
                        <input type="text" name="username" class="form-input" required>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Password</label>
                        <input type="password" name="password" class="form-input" required>
                    </div>
                    <button type="submit" class="btn btn-primary" style="width: 100%;">Login</button>
                </form>
                <p style="text-align: center; margin-top: 1rem; color: var(--text-muted);">
                    Don't have an account? <a href="/register" style="color: var(--primary);">Register</a>
                </p>
            </div>
        </div>
    </div>
    ''')
    return render_template_string(html, title='Login')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))

@app.route('/dashboard')
@login_required
def dashboard():
    user_domains = Domain.query.filter_by(user_id=current_user.id).all()

    html = BASE_TEMPLATE.replace('{% block content %}{% endblock %}', '''
    <div class="container">
        <div class="page-header">
            <h1 class="page-title">Dashboard</h1>
            <p class="page-subtitle">Manage your domains</p>
        </div>

        <div class="stats" style="justify-content: flex-start; gap: 2rem;">
            <div class="stat-item">
                <div class="stat-value">{{ domains|length }}</div>
                <div class="stat-label">Total Domains</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{{ domains|selectattr('status', 'equalto', 'active')|list|length }}</div>
                <div class="stat-label">Active</div>
            </div>
        </div>

        {% if domains %}
        <div class="card">
            <table class="table">
                <thead>
                    <tr>
                        <th>Domain</th>
                        <th>Status</th>
                        <th>Registered</th>
                        <th>Expires</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {% for domain in domains %}
                    <tr>
                        <td><span class="domain-tag">{{ domain.name }}</span></td>
                        <td><span class="badge badge-available">{{ domain.status }}</span></td>
                        <td>{{ domain.registration_date.strftime('%Y-%m-%d') if domain.registration_date else 'N/A' }}</td>
                        <td>{{ domain.expiry_date.strftime('%Y-%m-%d') if domain.expiry_date else 'N/A' }}</td>
                        <td>
                            <button class="btn btn-outline" style="padding: 0.25rem 0.75rem;">Manage</button>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% else %}
        <div class="empty-state">
            <div class="empty-state-icon">📦</div>
            <h3>No domains yet</h3>
            <p>Start by searching for your perfect domain</p>
            <a href="/search" class="btn btn-primary" style="margin-top: 1rem;">Search Domains</a>
        </div>
        {% endif %}
    </div>
    ''')
    return render_template_string(html, title='Dashboard', domains=user_domains)

@app.route('/cart')
def cart():
    cart_items = []
    total = 0

    if current_user.is_authenticated:
        cart_items = Cart.query.filter_by(user_id=current_user.id).all()
        total = sum(item.price for item in cart_items)

    html = BASE_TEMPLATE.replace('{% block content %}{% endblock %}', '''
    <div class="container">
        <div class="page-header">
            <h1 class="page-title">Shopping Cart</h1>
            <p class="page-subtitle">Review your domain registrations</p>
        </div>

        {% if cart_items %}
        <div style="display: grid; grid-template-columns: 1fr 300px; gap: 2rem;">
            <div class="card">
                {% for item in cart_items %}
                <div class="cart-item">
                    <div>
                        <span class="domain-tag">{{ item.domain_name }}</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 1rem;">
                        <span class="price" style="font-size: 1rem;">{% if item.price == 0 %}FREE{% else %}${{ item.price }}{% endif %}</span>
                        <form action="/cart/remove/{{ item.id }}" method="POST">
                            <button type="submit" class="btn btn-danger" style="padding: 0.25rem 0.5rem;">×</button>
                        </form>
                    </div>
                </div>
                {% endfor %}
            </div>

            <div class="cart-summary">
                <h3>Order Summary</h3>
                <div class="total-row">
                    <span>Total</span>
                    <span>{% if total == 0 %}FREE{% else %}${{ total }}{% endif %}</span>
                </div>
                {% if current_user.is_authenticated %}
                <form action="/cart/checkout" method="POST" style="margin-top: 1rem;">
                    <button type="submit" class="btn btn-success" style="width: 100%;">Complete Registration</button>
                </form>
                {% else %}
                <a href="/login" class="btn btn-primary" style="width: 100%; margin-top: 1rem;">Login to Checkout</a>
                {% endif %}
            </div>
        </div>
        {% else %}
        <div class="empty-state">
            <div class="empty-state-icon">🛒</div>
            <h3>Your cart is empty</h3>
            <p>Search for domains to add them to your cart</p>
            <a href="/search" class="btn btn-primary" style="margin-top: 1rem;">Search Domains</a>
        </div>
        {% endif %}
    </div>
    ''')
    return render_template_string(html, title='Cart', cart_items=cart_items, total=total)

@app.route('/cart/add', methods=['POST'])
def cart_add():
    if not current_user.is_authenticated:
        flash('Please login to add items to cart', 'error')
        return redirect(url_for('login'))

    domain_name = request.form.get('domain_name')
    price_str = request.form.get('price', 'FREE')

    # Parse price
    if price_str == 'FREE':
        price = 0.0
    else:
        try:
            price = float(price_str.replace('$', ''))
        except:
            price = 0.0

    # Check if already in cart
    existing = Cart.query.filter_by(user_id=current_user.id, domain_name=domain_name).first()
    if existing:
        flash('Domain already in cart!', 'error')
        return redirect(url_for('search'))

    # Check if domain already taken
    domain = Domain.query.filter_by(name=domain_name).first()
    if domain and domain.user_id:
        flash('Domain is no longer available!', 'error')
        return redirect(url_for('search'))

    cart_item = Cart(user_id=current_user.id, domain_name=domain_name, price=price)
    db.session.add(cart_item)
    db.session.commit()
    flash(f'{domain_name} added to cart!', 'success')
    return redirect(url_for('cart'))

@app.route('/cart/remove/<int:cart_id>', methods=['POST'])
@login_required
def cart_remove(cart_id):
    cart_item = Cart.query.filter_by(id=cart_id, user_id=current_user.id).first()
    if cart_item:
        db.session.delete(cart_item)
        db.session.commit()
        flash('Item removed from cart', 'success')
    return redirect(url_for('cart'))

@app.route('/cart/checkout', methods=['POST'])
@login_required
def cart_checkout():
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()

    if not cart_items:
        flash('Your cart is empty!', 'error')
        return redirect(url_for('cart'))

    from datetime import datetime, timedelta

    for item in cart_items:
        # Check if domain exists
        domain = Domain.query.filter_by(name=item.domain_name).first()
        if not domain:
            domain = Domain(name=item.domain_name)

        domain.user_id = current_user.id
        domain.registration_date = datetime.utcnow()
        domain.expiry_date = datetime.utcnow() + timedelta(days=365)
        domain.status = 'active'
        db.session.add(domain)

        db.session.delete(item)

    db.session.commit()
    flash('Domains registered successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/api/domains')
def api_domains():
    domains = Domain.query.all()
    return jsonify({
        "success": True,
        "data": [{"name": d.name, "status": "registered" if d.user_id else "available"} for d in domains],
        "total": len(domains)
    })

@app.route('/api/search')
def api_search():
    query = request.args.get('domain', '')
    results = []

    if query:
        extensions = ['.free', '.online', '.site', '.web', '.tech']
        for ext in extensions:
            domain_name = f"{query}{ext}"
            existing = Domain.query.filter_by(name=domain_name).first()
            results.append({
                "name": domain_name,
                "available": not existing
            })

    return jsonify({
        "success": True,
        "query": query,
        "results": results
    })

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
