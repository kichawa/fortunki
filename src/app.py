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
    text = text.strip()
    chunks = []

    nick_map = {}
    for line in text.split('\n'):
        line = line.strip()
        if line.startswith("<"):
            nick, msg = [flask.escape(p) for p in line.split(" ", 1)]
            nick = nick[4:-4]
            if nick not in nick_map:
                nick_map[nick] = len(nick_map) + 1
            line = u'<span class="irc-nick irc-nick-{0}">{1}:</span>'\
                   ' <span class="message">{2}</span>'\
                   .format(nick_map[nick], nick, msg)

        if line.startswith("*"):
            _, nick, msg = [flask.escape(p) for p in line.split(" ", 2)]
            line = u'<span class="irc-nick-me">{0}</span>'\
                    '<span class="irc-message-me">{1}</span>'\
                    .format(nick, msg)

        if line.startswith("-"):
            line = u'<span class="irc-status">{0}</span>'.format(line)

        chunks.append(line)

    return u"<pre>{0}</pre>".format("\n".join(chunks))

@app.template_filter('strftime')
def strftime(dt, format):
    return dt.strftime(format)

@app.route("/")
@app.route("/order/<order>/")
@app.route("/order/<order>/<export_as>/")
@app.route("/<export_as>/")
def entry_list(order="-votes_count", export_as=None):
    if order not in ["-votes_count", "votes_count", "created", "-created"]:
        return flask.abort(404)
    if export_as not in [None, "json"]:
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
    if export_as == "json":
        meta = {
            'page': {
                'number':page.number,
                'has_next': page.has_next(),
                'has_previous': page.has_previous(),
            },
            'order': order,
            'total_count': paginator.count(),
        }
        return flask.jsonify(meta=meta,
                objects=[o.json_ready() for o in page.objects_list])
    return flask.render_template("list.html", entries_page=page)

@app.route("/details/<entry_id>/")
def entry_details(entry_id):
    "Just to be able to point to that direct entry..."
    try:
        entry = db.Entry.select().where(id=entry_id)
    except db.Entry.DoesNotExist:
        return flask.abort(404)
    page = pagination.Paginator(entry, settings.PER_PAGE_LIMIT).page(1)
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
            entry = db.Entry.get_or_create(content=content, id=eid)
            return flask.redirect(flask.url_for("entry_details", entry_id=entry.id))

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
    # flask is using 'Referer' instead of 'HTTP_REFERRER'
    url = flask.request.headers.get('Referer', flask.url_for('entry_list'))
    response = flask.redirect(url)
    response.set_cookie(settings.VOTE_COOKIE_KEY, userid)
    return response


if __name__ == "__main__":
    host, port = '0.0.0.0', 5000
    if len(sys.argv) == 2:
        host, port = sys.argv[1].split(':')
    app.run(host=host, port=int(port))
