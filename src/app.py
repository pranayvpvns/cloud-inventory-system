from flask import Flask,jsonify,request,session, redirect, url_for
from db_config import db_connection
from mongo_config import get_mongo_connection
from flask import render_template
from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
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
    password = request.form.get("password")
    hashed_password = generate_password_hash(password)
    con = db_connection()
    cur = con.cursor()
    cur.execute(
        "insert into users (name, email, password) values (%s, %s, %s)",
        (name, email, hashed_password)
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

    if session.get("role") == "admin":
        return "admins cannot create orders"

    con = db_connection()
    cur = con.cursor()

    try:

        if request.is_json:
            data = request.json
            user_id = data.get("user_id")
            items = data.get("items")
        else:
            user_id = request.form.get("user_id")
            selected_products = request.form.getlist("product_id")

            if not selected_products:
                return "no products selected"

            items = []
            for product_id in selected_products:
                quantity = int(request.form.get(f"quantity_{product_id}"))
                items.append({
                    "product_id": int(product_id),
                    "quantity": quantity
                })

        if not items:
            return "no products provided", 400

        total_amount = 0

        for item in items:
            product_id = item["product_id"]
            quantity = int(item["quantity"])

            cur.execute("select price from products where id=%s", (product_id,))
            product = cur.fetchone()
            if not product:
                return f"product {product_id} not found", 404

            price = float(product[0])

            cur.execute("select stock_quantity from inventory where product_id=%s", (product_id,))
            stock = cur.fetchone()
            if not stock or stock[0] < quantity:
                return f"insufficient stock for product {product_id}", 400

            total_amount += price * quantity

        cur.execute(
            "insert into orders (user_id, total_amount) values (%s, %s)",
            (user_id, total_amount)
        )
        order_id = cur.lastrowid

        for item in items:
            product_id = item["product_id"]
            quantity = int(item["quantity"])

            cur.execute(
                "insert into order_items (order_id, product_id, quantity) values (%s, %s, %s)",
                (order_id, product_id, quantity)
            )

            cur.execute(
                "update inventory set stock_quantity = stock_quantity - %s where product_id=%s",
                (quantity, product_id)
            )

        con.commit()

        # 🔥 Enhanced Mongo Log
        cur.execute("select name from users where id=%s", (user_id,))
        user_name = cur.fetchone()[0]

        product_details = []
        for item in items:
            cur.execute("select name from products where id=%s", (item["product_id"],))
            product_name = cur.fetchone()[0]

            product_details.append({
                "product_name": product_name,
                "quantity": item["quantity"]
            })

        log_activity("order_created", {
            "order_id": order_id,
            "user_name": user_name,
            "products": product_details,
            "total_amount": total_amount
        })

        if request.is_json:
            return jsonify({
                "message": "order created successfully",
                "order_id": order_id,
                "total_amount": total_amount
            }), 201

        return f"order created successfully! total amount: ₹{total_amount}"

    except Exception as e:
        con.rollback()
        return str(e), 500

    finally:
        cur.close()
        con.close()
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

    if session.get("role") != "admin":
        return "access denied"
    con = db_connection()
    cur = con.cursor(dictionary=True)
    cur.execute("select id, name, email, role from users")
    users = cur.fetchall()
    cur.close()
    con.close()
    return render_template("users.html", users=users)

@app.route("/products-page")
def products_page():

    if session.get("role") != "admin":
        return "access denied"
    con = db_connection()
    cur = con.cursor(dictionary=True)
    cur.execute("select * from products")
    products = cur.fetchall()
    cur.close()
    con.close()
    return render_template("products.html", products=products)

@app.route("/orders-page")
def orders_page():

    con = db_connection()
    cur = con.cursor(dictionary=True)

    # 👑 If Admin → Show Orders List
    if session.get("role") == "admin":

        cur.execute("""
            select 
                o.id as order_id,
                u.name as user_name,
                o.total_amount
            from orders o
            join users u on o.user_id = u.id
            order by o.id desc
        """)
        orders = cur.fetchall()

        cur.close()
        con.close()

        return render_template("admin_orders.html", orders=orders)

    # 👤 If Normal User → Show Order Creation Page
    else:

        cur.execute("select * from users")
        users = cur.fetchall()

        cur.execute("""
            select p.id, p.name, p.price, i.stock_quantity
            from products p
            left join inventory i on p.id = i.product_id
        """)
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
    password = request.form.get("password")

    con = db_connection()
    cur = con.cursor(dictionary=True)

    cur.execute("select * from users where email=%s", (email,))
    user = cur.fetchone()

    cur.close()
    con.close()

    if user and check_password_hash(user["password"], password):
        session["user_id"] = user["id"]
        session["role"] = user["role"]   
        return redirect("/dashboard")
    else:
        return "invalid credentials"

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

    # 🔒 Allow only admin
    if session.get("role") != "admin":
        return "access denied"

    data = request.json
    product_id = data.get("product_id")
    stock_quantity = int(data.get("stock_quantity"))

    con = db_connection()
    cur = con.cursor()

    # 🔍 Check if inventory already exists
    cur.execute("select * from inventory where product_id=%s", (product_id,))
    existing = cur.fetchone()

    if existing:
        # ✅ Increase stock
        cur.execute(
            "update inventory set stock_quantity = stock_quantity + %s where product_id=%s",
            (stock_quantity, product_id)
        )
    else:
        # ✅ Insert new inventory
        cur.execute(
            "insert into inventory (product_id, stock_quantity) values (%s, %s)",
            (product_id, stock_quantity)
        )

    con.commit()
    cur.close()
    con.close()

    return jsonify({"message": "inventory updated successfully"}), 200
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

@app.route("/inventory-page")
def inventory_page():

    if session.get("role") != "admin":
        return "access denied"

    con = db_connection()
    cur = con.cursor(dictionary=True)

    cur.execute("""
        select p.id, p.name, p.price, i.stock_quantity
        from products p
        left join inventory i on p.id = i.product_id
    """)

    products = cur.fetchall()

    cur.close()
    con.close()

    return render_template("inventory.html", products=products)

@app.route("/inventory-ui", methods=["post"])
def inventory_ui():

    if session.get("role") != "admin":
        return "access denied"

    product_id = request.form.get("product_id")
    stock_quantity = int(request.form.get("stock_quantity"))

    con = db_connection()
    cur = con.cursor()

    # check existing
    cur.execute("select * from inventory where product_id=%s", (product_id,))
    existing = cur.fetchone()

    if existing:
        cur.execute(
            "update inventory set stock_quantity = stock_quantity + %s where product_id=%s",
            (stock_quantity, product_id)
        )
    else:
        cur.execute(
            "insert into inventory (product_id, stock_quantity) values (%s, %s)",
            (product_id, stock_quantity)
        )

    con.commit()
    cur.close()
    con.close()

    return redirect("/inventory-page")

@app.route("/delete-user", methods=["post"])
def delete_user_ui():

    if session.get("role") != "admin":
        return "access denied"

    user_id = request.form.get("user_id")

    con = db_connection()
    cur = con.cursor()

    cur.execute("delete from users where id=%s", (user_id,))
    con.commit()

    cur.close()
    con.close()

    return redirect("/users-page")

@app.route("/delete-product", methods=["post"])
def delete_product_ui():

    if session.get("role") != "admin":
        return "access denied"

    product_id = request.form.get("product_id")

    con = db_connection()
    cur = con.cursor()

    cur.execute("delete from products where id=%s", (product_id,))
    con.commit()

    cur.close()
    con.close()

    return redirect("/products-page")


if __name__ == "__main__":
    app.run(app.run(host="0.0.0.0", port=5000, debug=True))