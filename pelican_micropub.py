import requests
from flask import Flask, Response, render_template
from flask import request
from flask_indieauth import requires_indieauth
import datetime
import os
import base64
import json
import io
import time


WEBSITE = 'website'
WEBSITE_CONTENTS = 'https://api.github.com/repos/drivet/' + WEBSITE + '/contents'
WEBSITE_URL = 'https://desmondrivet.com'

app = Flask(__name__)


class Entry(object):
    def __init__(self, request_data):
        self.name = extract_value(request_data, 'name')
        self.content = extract_value(request_data, 'content')

        self.updated = extract_value(request_data, 'updated')
        self.category = extract_value(request_data, 'category', True)
        self.in_reply_to = extract_value(request_data, 'in-reply-to')
        self.like_of = extract_value(request_data, 'like-of')
        self.repost_of = extract_value(request_data, 'report-of')
        self.syndication = extract_value(request_data, 'syndication', True)
        self.mp_slug = extract_value(request_data, 'mp-slug')

        self.published = extract_value(request_data, 'published')
        if self.published is None:
            self.published = datetime.datetime.now().isoformat()
        self.published_date = datetime.datetime.strptime(self.published, '%Y-%m-%dT%H:%M:%S.%f')

    def __str__(self):
        return 'entry:' + self.content


# 1. a list of 1 is returned as a single value, unless force_multiple is True
# 2. a list with more than one value is always returned as a list
def extract_value(mdict, key, force_multiple=False):
    mkey = key + '[]'
    if mkey in mdict:
        val = mdict.getlist(mkey)
        if len(val) > 1:
            return val
        else:
            return val[0]
    elif key in mdict:
        if force_multiple:
            return [mdict[key]]
        else:
            return mdict[key]
    else:
        return None


# return a date string like YYYY-MM-DD HH:MM:SS
def extract_published(entry):
    return entry.published_date.strftime('%Y-%m-%d %H:%M:%S')


def write_meta(f, meta, data):
    f.write(meta + ': ' + data + '\n')


def extract_slug(entry):
    if entry.mp_slug:
        slug = entry.mp_slug
    else:
        slug = entry.published_date.strftime('%Y%m%d%H%M%S')
    return slug


def extract_permalink(entry):
    return WEBSITE_URL + entry.published_date.strftime('/%Y/%m/%d/') + extract_slug(entry)


def make_note(entry):
    with io.StringIO() as f:
        write_meta(f, 'date', extract_published(entry))
        if entry.category:
            write_meta(f, 'tags', ','.join(entry.category))
        f.write('\n')
        f.write(entry.content)
        r = commit_file('/content/notes/' + extract_slug(entry) + '.nd', f.getvalue())
        if r.status_code != 201:
            raise Exception('failed to post to github')
    permalink = extract_permalink(entry)
    created = wait_for_url(permalink)
    return permalink, created


def make_article(entry):
    with io.StringIO() as f:
        write_meta(f, 'title', entry.name)
        write_meta(f, 'date', extract_published(entry))
        if entry.category:
            write_meta(f, 'tags', ','.join(entry.category))
        f.write('\n')
        f.write(entry.content)
        r = commit_file('/content/blog/' + extract_slug(entry) + '.md', f.getvalue())
        if r.status_code != 201:
            raise Exception('failed to post to github')
    permalink = extract_permalink(entry)
    created = wait_for_url(permalink)
    return permalink, created


def commit_file(path, content):
    url = WEBSITE_CONTENTS + path
    return requests.put(url, auth=(os.environ['USERNAME'], os.environ['PASSWORD']),
                        data=json.dumps({'message': 'post to ' + path, 'content': b64(content)}))


def b64(s):
    return base64.b64encode(s.encode()).decode()


def wait_for_url(url):
    timeout_secs = 15
    wait_secs = 0.1
    started = time.time()

    done = False
    found = False
    while not done:
        r = requests.head(url)
        if r.status_code == 200:
            done = True
            found = True
        elif (time.time() - started) >= timeout_secs:
            done = True
            found = False
        else:
            time.sleep(wait_secs)
    return found


@app.route('/', methods=['GET', 'POST'], strict_slashes=False)
@requires_indieauth
def create():
    if 'h' not in request.form:
        return Response(status=400)
    if 'content' not in request.form:
        return Response(status=400)

    if request.form['h'] == 'entry':
        entry = Entry(request.form)
        if not entry.name:
            permalink, created = make_note(entry)
        else:
            permalink, created = make_article(entry)

        if created:
            resp = Response(status=201)
        else:
            resp = Response(status=202)
        resp.headers['Location'] = permalink
        return resp
    else:
        return Response(response='only entries supported', status=400)


@app.route('/test', methods=['GET'])
def test_form():
    return render_template('test_post.html')
