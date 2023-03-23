"""
Routes and views for the bottle application.
"""
import os
from random import getrandbits

import pypandoc
from bottle import route, view, request, response, redirect
from datetime import datetime
import sqlite3

SECRET = "ABOBA"
preview_path = "./preview"


@route('/')
@route('/editor')
@view('editor')
def editor():
    """Renders the home page."""
    secret = request.get_cookie("secret", secret=SECRET)
    print(secret)
    if secret is None:
        return dict(
            year=datetime.now().year,
            filecontent=""
        )
    else:
        conn = sqlite3.connect("info.db")
        cur = conn.cursor()
        try:
            file = cur.execute("""SELECT file_path FROM files WHERE user_uid = ?""", (secret,)).fetchone()[0]
        except TypeError:
            return dict(
                year=datetime.now().year,
                filecontent=""
            )

        with open(file, "r", encoding="utf-8") as f:
            return dict(
                year=datetime.now().year,
                filecontent=f.read()
            )


@route('/contact')
@view('contact')
def contact():
    """Renders the contact page."""
    return dict(
        title='Contact',
        year=datetime.now().year
    )


@route('/about')
@view('about')
def about():
    """Renders the about page."""
    return dict(
        title='About us',
        message='Here you can see the possibilities of our site',
        year=datetime.now().year,
        functions='At this site you could:',
        func1='share reports',
        func2='watch reports',
        func3='download reports',
        func4='change report format'
    )


@route('/upload', method='POST')
@view("editor")
def do_upload():
    upload = request.files.get('inputFile')
    print(upload)

    temp_path = "./tmp"
    save_path = "./save"

    if not os.path.exists(temp_path):
        os.makedirs(temp_path)

    if not os.path.exists(save_path):
        os.makedirs(save_path)

    if not os.path.exists(preview_path):
        os.makedirs(preview_path)

    file_path = f"{temp_path}/{upload.filename}"
    upload.save(file_path)
    output = pypandoc.convert_file(file_path, 'org')
    random_bits = getrandbits(128)
    file_hash = "%032x" % random_bits
    hash_path = f"{save_path}/{file_hash}.org"
    with open(hash_path, "w", encoding="utf-8") as f:
        f.write(output)
    os.remove(file_path)
    conn = sqlite3.connect("info.db")
    cur = conn.cursor()
    random_bits = getrandbits(128)
    hash = "%032x" % random_bits
    client_ip = request.environ.get('REMOTE_ADDR')
    cur.execute("""INSERT INTO users VALUES (?, ?)""", (hash, client_ip))
    cur.execute("""INSERT INTO files VALUES (?, ?)""", (hash, hash_path))
    conn.commit()
    cur.close()
    conn.close()
    preview_html = pypandoc.convert_file(hash_path, 'html')
    print(hash)
    with open(f"{preview_path}/{hash}", "w", encoding="utf-8") as f:
        f.write(preview_html)
    response.set_cookie("secret", hash, secret=SECRET)

    redirect("/editor")

    # return "File successfully saved to '{0}'.".format(f"{save_path}/{hash}.org")


@route('/preview')
@view("preview")
def preview():
    secret = request.get_cookie("secret", secret=SECRET)
    with open(f"{preview_path}/{secret}", "r", encoding="utf-8") as f:
        return dict(
            previewContent=f.read()
        )


@route("/preview_reload", method='POST')
def preview_reload():
    secret = request.get_cookie("secret", secret=SECRET)
    with open(f"{preview_path}/{secret}", "w", encoding="utf-8") as f:
        f.write(pypandoc.convert_text(request.json['data'], 'html', format="org"))
    conn = sqlite3.connect("info.db")
    cur = conn.cursor()
    file = cur.execute("""SELECT file_path FROM files WHERE user_uid = ?""", (secret,)).fetchone()[0]
    with open(f"{file}", "w", encoding="utf-8") as f:
        f.write(request.json['data'])
