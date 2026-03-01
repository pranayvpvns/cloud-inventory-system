from flask import Flask,jsonify,request,session, redirect, url_for
from db_config import db_connection
from mongo_config import get_mongo_connection
from flask import render_template
from extensions import db
from models import User, Product, Order, OrderItem
app=Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:root@localhost/cloud_inventory'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = "supersecretkey"
db.init_app(app)
@app.route("/orm-users", methods=["get"])
def orm_users():
    users = User.query.all()
    result = []
    for user in users:
        result.append({
            "id": user.id,
            "name": user.name,
            "email": user.email
        })
    return jsonify(result)

@app.route("/")
def home():
    if "user_id" in session:
        return redirect("/dashboard")
    return render_template("index.html")

@app.route("/register", methods=["post"])
def register():
    name = request.form.get("name")
    email = request.form.get("email")
    con = db_connection()
    cur = con.cursor()
    cur.execute(
        "insert into users (name, email) values (%s, %s)",
        (name, email)
    )
    con.commit()
    cur.close()
    con.close()
    return redirect("/login-page")

@app.route("/register-page")
def register_page():
    return render_template("register.html")

@app.route("/first")
def first():
    return jsonify({
        "status":"UP",
        "message":"It is working fine"
    })

@app.route("/users", methods=["GET", "POST"])
def users():

    con = db_connection()
    cur = con.cursor(dictionary=True)
    if request.method == "GET":
        cur.execute("select * from users")
        users = cur.fetchall()
        cur.close()
        con.close()
        return jsonify(users)
    elif request.method == "POST":
        if request.is_json:
            data = request.json
            name = data.get("name")
            email = data.get("email")
        else:
            name = request.form.get("name")
            email = request.form.get("email")
        query = "insert into users (name, email) values (%s, %s)"
        cur.execute(query, (name, email))
        con.commit()
        cur.close()
        con.close()
        return "user created successfully"
@app.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    con = db_connection()
    cur = con.cursor()
    cur.execute("select * from users where id = %s", (user_id,))
    user = cur.fetchone()
    cur.close()
    con.close()
    return jsonify(user)

@app.route("/users/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    data = request.json
    name = data.get("name")
    email = data.get("email")
    con = db_connection()
    cur = con.cursor()
    query = "update users set name=%s, email=%s WHERE id=%s"
    cur.execute(query, (name, email, user_id))
    con.commit()
    cur.close()
    con.close()
    return jsonify({"message": "User updated successfully"})

@app.route("/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    con = db_connection()
    cur = con.cursor()
    cur.execute("delete from users WHERE id=%s", (user_id,))
    con.commit()
    cur.close()
    con.close()
    return jsonify({"message": "User deleted successfully"})

@app.route("/products", methods=["get", "post"])
def products():
    con = db_connection()
    cur = con.cursor(dictionary=True)
    if request.method == "GET":
        cur.execute("select * from products")
        products = cur.fetchall()
        cur.close()
        con.close()
        return jsonify(products)
    elif request.method == "POST":
        if request.is_json:
            data = request.json
            name = data.get("name")
            price = data.get("price")
        else:
            name = request.form.get("name")
            price = request.form.get("price")
        query = "insert into products (name, price) values (%s, %s)"
        cur.execute(query, (name, price))
        con.commit()
        cur.close()
        con.close()
        return "product created"


@app.route("/products/<int:product_id>", methods=["GET"])
def get_product(product_id):
    con = db_connection()
    cur = con.cursor(dictionary=True)
    cur.execute("select * from products where id=%s", (product_id,))
    product = cur.fetchone()
    cur.close()
    con.close()
    return jsonify(product)

@app.route("/products/<int:product_id>", methods=["DELETE"])
def delete_product(product_id):
    con = db_connection()
    cur = con.cursor()
    cur.execute("delete from products where id=%s", (product_id,))
    con.commit()
    cur.close()
    con.close()
    return jsonify({"message": "Product deleted successfully"})

@app.route("/orders", methods=["post"])
def create_order():
    if request.is_json:
        data = request.json
        user_id = data.get("user_id")
        total_amount = data.get("total_amount")
        con = db_connection()
        cur = con.cursor()
        query = "insert into orders (user_id, total_amount) values (%s, %s)"
        cur.execute(query, (user_id, total_amount))
        con.commit()
        order_id = cur.lastrowid
        log_activity("order_created", {
            "order_id": order_id,
            "user_id": user_id,
            "total_amount": total_amount
        })
        cur.close()
        con.close()
        return jsonify({
            "message": "order created",
            "order_id": order_id
        }), 201
    else:
        user_id = request.form.get("user_id")
        product_id = request.form.get("product_id")
        quantity = request.form.get("quantity")
        con = db_connection()
        cur = con.cursor()
        cur.execute("insert into orders (user_id, total_amount) values (%s, %s)",(user_id, 0))
        con.commit()
        order_id = cur.lastrowid
        cur.execute("insert into order_items (order_id, product_id, quantity) values (%s, %s, %s)",(order_id, product_id, quantity))
        con.commit()
        log_activity("order_created", {
            "order_id": order_id,
            "user_id": user_id
        })
        cur.close()
        con.close()
        return "order created successfully"

@app.route("/order-items", methods=["post"])
def add_order_item():
    data = request.json
    order_id = data.get("order_id")
    product_id = data.get("product_id")
    quantity = data.get("quantity")
    con = db_connection()
    cur = con.cursor()
    query = "insert into order_items (order_id, product_id, quantity) values (%s, %s, %s)"
    cur.execute(query, (order_id, product_id, quantity))
    con.commit()
    cur.close()
    con.close()
    return jsonify({"message": "order item added"}), 201

@app.route("/orders/<int:order_id>", methods=["get"])
def get_order_details(order_id):
    con = db_connection()
    cur = con.cursor(dictionary=True)
    query = """
    select 
        o.id as order_id,
        u.name as customer_name,
        p.name as product_name,
        oi.quantity,
        o.total_amount
    from orders o
    join users u on o.user_id = u.id
    join order_items oi on o.id = oi.order_id
    join products p on oi.product_id = p.id
    where o.id = %s
    """
    cur.execute(query, (order_id,))
    result = cur.fetchall()
    cur.close()
    con.close()
    return jsonify(result)

def log_activity(action, details):
    db = get_mongo_connection()
    logs = db["activity_logs"]
    log_data = {
        "action": action,
        "details": details
    }
    logs.insert_one(log_data)

@app.route("/users-page")
def users_page():
    return render_template("users.html")

@app.route("/products-page")
def products_page():
    return render_template("products.html")

@app.route("/orders-page")
def orders_page():

    con = db_connection()
    cur = con.cursor(dictionary=True)
    cur.execute("select * from users")
    users = cur.fetchall()
    cur.execute("select * from products")
    products = cur.fetchall()
    cur.close()
    con.close()

    return render_template("orders.html", users=users, products=products)

@app.route("/login-page")
def login_page():
    return render_template("login.html")

@app.route("/login", methods=["post"])
def login():
    email = request.form.get("email")
    con = db_connection()
    cur = con.cursor(dictionary=True)
    cur.execute("select * from users where email=%s", (email,))
    user = cur.fetchone()
    cur.close()
    con.close()
    if user:
        session["user_id"] = user["id"]
        return redirect("/dashboard")
    else:
        return "user not found"

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/")

    return render_template("dashboard.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/inventory", methods=["get"])
def get_inventory():
    con = db_connection()
    cur = con.cursor(dictionary=True)

    cur.execute("""
        select i.id, p.name as product_name, i.stock_quantity
        from inventory i
        join products p on i.product_id = p.id
    """)
    data = cur.fetchall()
    cur.close()
    con.close()
    return jsonify(data)

@app.route("/inventory", methods=["post"])
def add_inventory():
    data = request.json
    product_id = data.get("product_id")
    stock_quantity = data.get("stock_quantity")
    con = db_connection()
    cur = con.cursor(dictionary=True)
    cur.execute("select * from inventory where product_id=%s", (product_id,))
    existing = cur.fetchone()
    cur.close()
    cur = con.cursor()
    if existing:
        cur.execute(
            "update inventory set stock_quantity=%s where product_id=%s",
            (stock_quantity, product_id)
        )
        message = "inventory updated"
    else:
        cur.execute(
            "insert into inventory (product_id, stock_quantity) values (%s, %s)",
            (product_id, stock_quantity)
        )
        message = "inventory added"
    con.commit()
    cur.close()
    con.close()

    return jsonify({"message": message}), 200
@app.route("/inventory/<int:inventory_id>", methods=["put"])
def update_inventory(inventory_id):
    data = request.json
    stock_quantity = data.get("stock_quantity")
    con = db_connection()
    cur = con.cursor()
    query = "update inventory set stock_quantity=%s where id=%s"
    cur.execute(query, (stock_quantity, inventory_id))
    con.commit()
    cur.close()
    con.close()
    return jsonify({"message": "stock updated"})

@app.route("/inventory/<int:inventory_id>", methods=["delete"])
def delete_inventory(inventory_id):
    con = db_connection()
    cur = con.cursor()
    cur.execute("delete from inventory where id=%s", (inventory_id,))
    con.commit()
    cur.close()
    con.close()
    return jsonify({"message": "inventory deleted"})

if __name__ == "__main__":
    app.run(app.run(host="0.0.0.0", port=5000, debug=True))