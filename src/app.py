# coding=utf-8

import flask

import db
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

@app.route("/")
def list_entries():
    offset = 0
    entries = db.Entry.select()
    entries = entries.paginate(offset, offset + settings.PER_PAGE_LIMIT)
    return flask.render_template("list.html", entries=entries)

@app.template_filter('irc_log_colorize')
def irc_log_colorize(text):
    # TODO
    return u"<pre>{0}</pre>".format(text.strip())

@app.template_filter('strftime')
def strftime(dt, format):
    return dt.strftime(format)

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
            db.Entry.create(content=content, id=db.random_id())
            return flask.redirect(flask.url_for("list_entries"))

    return flask.render_template("add.html", errors=errors,
            form_data=flask.request.form)

@app.route("/vote/<entry_id>/toggle/")
def entry_vote_toggle(entry_id):
    try:
        entry = db.Entry.get(id=entry_id)
    except db.Entry.DoesNotExist:
        return flask.abort(404)
    entry.votes += 1
    entry.save()
    return str(entry.id)


if __name__ == "__main__":
    app.run()
