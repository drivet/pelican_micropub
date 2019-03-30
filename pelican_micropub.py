from flask import Flask, Response, render_template
from flask import request
from flask_indieauth import requires_indieauth
import datetime


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
            self.published = [datetime.datetime.now().isoformat()]
        self.published_date = datetime.datetime.strptime(self.published[0], '%Y-%m-%dT%H:%M:%S.%f')

    def __str__(self):
        return 'entry:' + self.content[0]


def extract_value(mdict, key, multiple=False):
    mkey = key + '[]'
    if mkey in mdict:
        return mdict.getlist(mkey)
    elif key in mdict:
        return [mdict[key]]
    else:
        return None


# return a date string like YYYY-MM-DD HH:MM:SS
def extract_published(entry):
    return entry.published_date.strftime('%Y-%m-%d %H:%M:%S')


def extract_permalink(entry):
    if entry.mp_slug:
        slug = entry.mp_slug[0]
    else:
        slug = entry.published_date.strftime('%Y%m%d%H%M%S')
    return entry.published_date.strftime('https://desmondrivet.com/%Y/%m/%d/') + slug


def make_note(entry):
    with open('/tmp/note.nd', 'w') as f:
        f.write('date: ' + extract_published(entry) + '\n')
        f.write('\n')
        f.write(entry.content[0])
    return extract_permalink(entry)


def make_article(entry):
    with open('/tmp/article.md', 'w') as f:
        f.write('title: ' + entry.name[0] + '\n')
        f.write('date: ' + extract_published(entry) + '\n')
        f.write('\n')
        f.write(entry.content[0])
    return extract_permalink(entry)


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
            permalink = make_note(entry)
        else:
            permalink = make_article(entry)

        resp = Response(status=202)
        resp.headers['Location'] = permalink
        return resp
    else:
        return Response(response='only entries supported', status=400)


@app.route('/test', methods=['GET'])
def test_form():
    return render_template('test_post.html')
