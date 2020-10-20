import os

from flask import Flask, abort, current_app, jsonify, redirect, request, url_for
from flask_dance.contrib.github import github, make_github_blueprint

SCOPES = ["user", "repo"]
FORWARDED_HEADERS = ["date", "content-type", "etag", "last-modified"]

app = Flask(__name__)

app.secret_key = os.environ.get("FLASK_SECRET_KEY")
app.config["GITHUB_OAUTH_CLIENT_ID"] = os.environ.get("GITHUB_OAUTH_CLIENT_ID")
app.config["GITHUB_OAUTH_CLIENT_SECRET"] = os.environ.get("GITHUB_OAUTH_CLIENT_SECRET")

app.config["DEBUG"] = os.environ.get("FLASK_DEBUG") == "true"

github_bp = make_github_blueprint(
    scope=",".join(sorted(SCOPES)),
    redirect_url=os.environ.get("GITHUB_OAUTH_REDIRECT_URL"),
)
app.register_blueprint(github_bp, url_prefix="/login")


def corsRequestHandler():
    if request.method == "OPTIONS":
        resp = current_app.make_default_options_response()
        resp.headers["Access-Control-Allow-Origin"] = os.environ.get("ALLOWED_ORIGINS")
        resp.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,OPTIONS"
        resp.headers["Access-Control-Allow-Credentials"] = "true"
        return resp


def corsResponseHandler(resp):
    resp.headers["Access-Control-Allow-Origin"] = os.environ.get("ALLOWED_ORIGINS")
    resp.headers["Access-Control-Allow-Credentials"] = "true"
    return resp


def to_flask_response(r):
    headers = dict(
        (k, v)
        for k, v in r.headers.items()
        if k.lower() in FORWARDED_HEADERS or k.lower().startswith("x-")
    )
    return r.content, r.status_code, headers.items()


app.before_request(corsRequestHandler)
app.after_request(corsResponseHandler)


@app.route("/user/starred/<string:user>/<string:repo>", methods=["PUT"])
def star(user, repo):
    if not github.authorized:
        return abort(401)
    r = github.put("/user/starred/{}/{}".format(user, repo), stream=True)
    return to_flask_response(r)


@app.route("/user/starred/<string:user>/<string:repo>", methods=["DELETE"])
def unstar(user, repo):
    if not github.authorized:
        return abort(401)
    r = github.delete("/user/starred/{}/{}".format(user, repo), stream=True)
    return to_flask_response(r)


@app.route("/user/starred/<string:user>/<string:repo>", methods=["GET"])
def starred(user, repo):
    if not github.authorized:
        return abort(401)
    r = github.get("/user/starred/{}/{}".format(user, repo), stream=True)
    return to_flask_response(r)


@app.route("/user", methods=["GET"])
def user():
    if not github.authorized:
        return abort(401)
    r = github.get("/user", stream=True)
    return to_flask_response(r)


@app.route("/login", methods=["GET"])
def login():
    if not github.authorized:
        return redirect(url_for("github.login"))
    return "<html><script>window.close()</script><body>You may now close this window.</body></html>"


@app.route("/logout", methods=["POST"])
def logout():
    try:
        del github_bp.token
    except KeyError:
        pass
    return redirect(url_for("index"))


@app.route("/")
def index():
    return jsonify(authorized=github.authorized)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5555)
