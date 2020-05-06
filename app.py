from flask import Flask
from redis import Redis, RedisError



from flask import render_template, session, redirect, url_for, Markup
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

from LogBrowser import LogBrowser as LB
from LogBrowser import redis

# menu()
# createAllIndexValueMaps()
# printIndexValueMap("target_basepath")
# printIndexValueLogEntries("target_basepath")
# printIndexValueMap("target_basepath")
# printAllIndexValueMaps()

# loadLogFile()


app = Flask(__name__)
app.config['SECRET_KEY'] = 'hard to guess string'

bootstrap = Bootstrap(app)
moment = Moment(app)

TITLE = "Web Log Browser"
DESC = "Redis Modeling Demo"
status = "Status - so far so good"

# redis = LB.redis

lb = LB()
# lb.loadLogFile()

class AdminForm(FlaskForm):
    # name = StringField('What is your name?', validators=[DataRequired()])
    submit = SubmitField('Submit')


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


@app.route('/')
@app.route('/counter')
def index():
    redis.incr('hits')
    status = "Redis 'hits' counter is incremented"
    return render_template("counter.html", hit_counts=redis.get('hits'),
                           title=TITLE, desc=DESC, status=status)


@app.route('/analysis', methods=['GET', 'POST'])
def analysis():

    DESC = "Summary Value Mappings across Log Entries"
    status = "Ok"

    # page_content = lb.printAllIndexValueMaps()
    page_content = ""
    for i in lb.indexValueMaps.keys():
        page_content +="<h3>{}</h3>".format(i)
        page_content +="<UL>"
        for j in lb.indexValueMaps[i].valueSet:
            page_content += "<li>Value '{}' mapped to {} logEntries</li>".format(j, len(lb.indexValueMaps[i].valueMap))
        page_content +="</UL>"

    # print(page_content)
    return render_template("analysis.html", page_content = Markup(page_content),
                           title=TITLE, desc=DESC, status=status)

@app.route("/db/info")
def dbinfo():
    # View constants
    TITLE = "Database Info"
    DESC = "Redis Server Instance Information"
    items = []

    try:
        result = redis.info()
        for k in result:
            item = {}
            item["key"] = k
            item["value"] = result[k]
            items.append(item)
        return render_template('dbinfo.html', title=TITLE, desc=DESC,
                               items=items, status="Success")
    except RedisError as err:
        return render_template('dbinfo.html', title=TITLE,
                               desc=DESC, error=err)

@app.route("/db/test")
def dbtest():
    # View constants
    TITLE = "Redis Connectivity Check"
    DESC = "Testing database connectivity ..."
    try:
        redis.set("_app:db:test", "Database connectivity works as expected!")
        status = redis.get("_app:db:test")
        return render_template('dbtest.html', title=TITLE,
                               desc=DESC, status=status)
    except RedisError as err:
        return render_template('dbtest.html', title=TITLE,
                               desc=DESC, error=err)

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
