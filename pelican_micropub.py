from flask import Flask, Response, render_template
from flask import request
from flask_indieauth import requires_indieauth

app = Flask(__name__)


class Entry(object):
    def __init__(self, request_data):
        self.name = extract_value(request_data, 'name')
        self.content = extract_value(request_data, 'content')
        self.published = extract_value(request_data, 'published')
        self.updated = extract_value(request_data, 'updated')
        self.category = extract_value(request_data, 'category')
        self.in_reply_to = extract_value(request_data, 'in-reply-to')
        self.like_of = extract_value(request_data, 'like-of')
        self.repost_of = extract_value(request_data, 'report-of')
        self.syndication = extract_value(request_data, 'syndication')

    def __str__(self):
        return 'entry:' + self.content


def extract_value(mdict, key):
    mkey = key + '[]'
    if mkey in mdict:
        return mdict.getlist(mkey)
    elif key in mdict:
        return [mdict[key]]
    else:
        return None


@app.route('/', methods=['POST'])
@requires_indieauth
def create():
    if 'h' not in request.form:
        return Response(status=400)
    if 'content' not in request.form:
        return Response(status=400)

    if request.form['h'] == 'entry':
        entry = Entry(request.form)
        print(entry)
        return Response(status=202)
    else:
        return Response(response='only entries supported', status=400)


@app.route('/test', methods=['GET'])
def test_form():
    return render_template('test_post.html')


