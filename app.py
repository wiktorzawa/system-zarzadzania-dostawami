from flask import Flask, render_template, request

app = Flask(__name__)

@app.route("/")
@app.route("/index")
def index():
	return render_template("main/index.html")

@app.route("/login_admin", methods=['GET', 'POST'])
def login_admin():
	if request.method == 'POST':
		# Tu dodamy logikę logowania
		pass
	return render_template("admin/login_admin.html")

@app.route("/login_staff", methods=['GET', 'POST'])
def login_staff():
	if request.method == 'POST':
		# Tu dodamy logikę logowania
		pass
	return render_template("staff/login_staff.html")

@app.route("/login_supplier", methods=['GET', 'POST'])
def login_supplier():
	if request.method == 'POST':
		# Tu dodamy logikę logowania
		pass
	return render_template("supplier/login_supplier.html")


if __name__ == '__main__':
	app.run(debug=True)