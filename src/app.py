# coding=utf-8

import hashlib
import sys

import flask

import db
import pagination
import settings

app = flask.Flask(__name__)
app.debug = True


@app.before_request
def before_request():
    flask.g.db = db.database
    flask.g.db.connect()

@app.after_request
def after_request(response):
    flask.g.db.close()
    return response

@app.context_processor
def inject_path():
    return {"current_path": flask.request.path}

@app.template_filter('irc_log_colorize')
def irc_log_colorize(text):
    # TODO
    text = flask.escape(text.strip())
    return u"<pre>{0}</pre>".format(text)

@app.template_filter('strftime')
def strftime(dt, format):
    return dt.strftime(format)

@app.route("/")
@app.route("/order/<order>/")
def list_entries(order="-votes_count"):
    if order not in ["-votes_count", "votes_count", "created", "-created"]:
        return flask.abort(404)
    entries = db.Entry.select().order_by(order)
    paginator = pagination.Paginator(entries, settings.PER_PAGE_LIMIT)
    try:
        page_num = int(flask.request.args.get('page'))
    except (TypeError, ValueError):
        page_num = 1
    if page_num < 1:
        page_num = 1
    page = paginator.page(page_num)
    return flask.render_template("list.html", entries_page=page)

@app.route("/add/", methods=['GET', 'POST'])
def add_entry():
    errors = {}
    if flask.request.method == 'POST':
        content = flask.request.form.get('content')
        if not errors:
            if not content:
                errors['content'] = u"Treść fortunki jest wymagana"
        if not errors:
            content = content.strip()
            if not content:
                errors['content'] = u"Fortunka nie może być pusta"
        if not errors:
            eid = hashlib.md5(content).hexdigest()
            db.Entry.create(content=content, id=eid)
            return flask.redirect(flask.url_for("list_entries"))

    return flask.render_template("add.html", errors=errors,
            form_data=flask.request.form)

@app.route("/vote/<entry_id>/toggle/")
def entry_vote_toggle(entry_id):
    userid = flask.request.cookies.get(settings.VOTE_COOKIE_KEY)
    if not userid:
        userid = db.random_id()

    try:
        entry = db.Entry.get(id=entry_id)
    except db.Entry.DoesNotExist:
        return flask.abort(404)

    try:
        vote = entry.votes.get(userid=userid)
        vote.delete_instance()
    except db.Vote.DoesNotExist:
        vote = db.Vote.create(entry=entry, userid=userid)

    entry.votes_count = entry.votes.count()
    entry.save()
    response = flask.redirect(flask.url_for('list_entries'))
    response.set_cookie(settings.VOTE_COOKIE_KEY, userid)
    return response


if __name__ == "__main__":
    host, port = '0.0.0.0', 5000
    if len(sys.argv) == 2:
        host, port = sys.argv[1].split(':')
    app.run(host=host, port=int(port))
