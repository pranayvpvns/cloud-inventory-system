from flask import Flask,jsonify

app=Flask(__name__)

@app.route("/")
def home():
    return "Cloud inventory running"

@app.route("/first")
def first():
    return jsonify({
        "status":"UP",
        "message":"It is working fine"
    })
if "__main__"==__name__:
    app.run(debug=True)