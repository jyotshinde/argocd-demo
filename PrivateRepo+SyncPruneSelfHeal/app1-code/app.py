from flask import Flask, jsonify
app = Flask(__name__)

@app.get("/")
def hello():
    return jsonify(
        message="🚀 Argo CD: Basics to Production",
        context="GitOps-managed Flask application",
        deployment="Deployed to Kubernetes via Argo CD"
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
