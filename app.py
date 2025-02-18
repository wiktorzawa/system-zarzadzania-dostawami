from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
from dotenv import load_dotenv
import os
import hashlib
import bcrypt

load_dotenv()

def verify_password(password_hash, password):
	"""Weryfikuje hasło z uwzględnieniem różnych formatów haszowania."""
	try:
		if password_hash.startswith('$2'):
			# Format bcrypt
			return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
		else:
			# Próba weryfikacji z użyciem domyślnego algorytmu
			return check_password_hash(password_hash, password)
	except Exception as e:
		print(f"Błąd weryfikacji hasła: {e}")
		return False

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'default-secret-key')

# Konfiguracja bazy danych
db_config = {
	'host': os.getenv('DB_HOST'),
	'user': os.getenv('DB_USER'),
	'password': os.getenv('DB_PASSWORD'),
	'database': os.getenv('DB_NAME'),
	'port': os.getenv('DB_PORT', 3306)
}

print("Konfiguracja bazy danych:", {k: v for k, v in db_config.items() if k != 'password'})

@app.route("/")
@app.route("/index")
def index():
	return render_template("MAIN/index.html")

@app.route("/login_admin", methods=['GET', 'POST'])
def login_admin():
	if request.method == 'POST':
		email = request.form.get('email')
		password = request.form.get('password')
		
		try:
			print(f"Próba połączenia z bazą danych jako {email}")
			conn = mysql.connector.connect(**db_config)
			cursor = conn.cursor(dictionary=True)
			
			# Sprawdź czy istnieje użytkownik o podanym emailu i roli admin
			cursor.execute("""
				SELECT id, email, password_hash, role 
				FROM login_data 
				WHERE email = %s AND role = 'admin'
			""", (email,))
			
			user = cursor.fetchone()
			
			if user and verify_password(user['password_hash'], password):
				# Zapisz dane użytkownika w sesji
				session['user_id'] = user['id']
				session['role'] = user['role']
				session['email'] = user['email']
				
				print(f"Użytkownik {email} zalogowany pomyślnie")
				# Przekieruj na dashboard
				return redirect(url_for('admin_dashboard'))
			else:
				print(f"Błędne dane logowania dla {email}")
				flash('Nieprawidłowy email lub hasło', 'error')
				
		except mysql.connector.Error as err:
			print(f"Błąd MySQL: {err}")
			if err.errno == mysql.connector.errorcode.ER_ACCESS_DENIED_ERROR:
				flash('Błędne dane dostępowe do bazy danych', 'error')
			elif err.errno == mysql.connector.errorcode.ER_BAD_DB_ERROR:
				flash('Baza danych nie istnieje', 'error')
			else:
				flash(f'Błąd połączenia z bazą danych: {err}', 'error')
		finally:
			if 'cursor' in locals():
				cursor.close()
			if 'conn' in locals():
				conn.close()
				
	return render_template("admin/login_admin.html")

@app.route("/login_staff", methods=['GET', 'POST'])
def login_staff():
	if request.method == 'POST':
		email = request.form.get('email')
		password = request.form.get('password')
		
		try:
			conn = mysql.connector.connect(**db_config)
			cursor = conn.cursor(dictionary=True)
			
			cursor.execute("""
				SELECT id, email, password_hash, role 
				FROM login_data 
				WHERE email = %s AND role = 'staff'
			""", (email,))
			
			user = cursor.fetchone()
			
			if user and verify_password(user['password_hash'], password):
				session['user_id'] = user['id']
				session['role'] = user['role']
				session['email'] = user['email']
				return redirect(url_for('staff_dashboard'))
			else:
				flash('Nieprawidłowy email lub hasło', 'error')
				
		except mysql.connector.Error as err:
			flash('Błąd połączenia z bazą danych', 'error')
		finally:
			if 'cursor' in locals():
				cursor.close()
			if 'conn' in locals():
				conn.close()
				
	return render_template("staff/login_staff.html")

@app.route("/login_supplier", methods=['GET', 'POST'])
def login_supplier():
	if request.method == 'POST':
		email = request.form.get('email')
		password = request.form.get('password')
		
		try:
			conn = mysql.connector.connect(**db_config)
			cursor = conn.cursor(dictionary=True)
			
			cursor.execute("""
				SELECT id, email, password_hash, role 
				FROM login_data 
				WHERE email = %s AND role = 'supplier'
			""", (email,))
			
			user = cursor.fetchone()
			
			if user and verify_password(user['password_hash'], password):
				session['user_id'] = user['id']
				session['role'] = user['role']
				session['email'] = user['email']
				return redirect(url_for('supplier_dashboard'))
			else:
				flash('Nieprawidłowy email lub hasło', 'error')
				
		except mysql.connector.Error as err:
			flash('Błąd połączenia z bazą danych', 'error')
		finally:
			if 'cursor' in locals():
				cursor.close()
			if 'conn' in locals():
				conn.close()
				
	return render_template("supplier/login_supplier.html")

@app.route("/admin/dashboard")
def admin_dashboard():
	if 'user_id' not in session or session['role'] != 'admin':
		return redirect(url_for('login_admin'))
	return render_template("admin/admin_dashboard.html")

@app.route("/staff/dashboard")
def staff_dashboard():
	if 'user_id' not in session or session['role'] != 'staff':
		return redirect(url_for('login_staff'))
	return render_template("staff/staff_dashboard.html")

@app.route("/supplier/dashboard")
def supplier_dashboard():
	if 'user_id' not in session or session['role'] != 'supplier':
		return redirect(url_for('login_supplier'))
	return render_template("supplier/supplier_dashboard.html")

@app.route("/supplier/nowa_dostawa", methods=['GET', 'POST'])
def supplier_nowa_dostawa():
	if 'user_id' not in session or session['role'] != 'supplier':
		return redirect(url_for('login_supplier'))
	
	if request.method == 'POST':
		# Pobieranie danych z formularza
		delivery_date = request.form.get('delivery_date')
		delivery_time = request.form.get('delivery_time')
		vehicle_type = request.form.get('vehicle_type')
		packages_count = request.form.get('packages_count')
		total_weight = request.form.get('total_weight')
		special_requirements = request.form.get('special_requirements')
		notes = request.form.get('notes')
		
		# TODO: Dodać zapis do bazy danych
		
		flash('Dostawa została pomyślnie zarejestrowana', 'success')
		return redirect(url_for('supplier_dashboard'))
		
	return render_template("supplier/supplier_nowa_dostawa.html")

@app.route("/supplier/dostawy_weryfikacja")
def supplier_dostawy_weryfikacja():
	if 'user_id' not in session or session['role'] != 'supplier':
		return redirect(url_for('login_supplier'))
	return render_template("supplier/supplier_dostawy_weryfikacja.html")

@app.route("/supplier/negocjacje")
def supplier_negocjacje():
	if 'user_id' not in session or session['role'] != 'supplier':
		return redirect(url_for('login_supplier'))
	return render_template("supplier/supplier_negocjacje.html")

@app.route("/supplier/rozliczenia")
def supplier_rozliczenia():
	if 'user_id' not in session or session['role'] != 'supplier':
		return redirect(url_for('login_supplier'))
	return render_template("supplier/supplier_rozliczenia.html")

@app.route("/supplier/profil")
def supplier_profil():
	if 'user_id' not in session or session['role'] != 'supplier':
		return redirect(url_for('login_supplier'))
	return render_template("supplier/supplier_profil.html")

@app.route("/logout")
def logout():
	session.clear()
	return redirect(url_for('index'))

if __name__ == '__main__':
	app.run(debug=True)