from flask import Flask
from redis import Redis, RedisError
import os 


from flask import render_template, session, redirect, url_for, Markup, request
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectMultipleField
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
    logFiles = []
    selectedFiles = []

    for file in os.listdir("./data"):
        if file.endswith(".log"):
            logFiles.append((os.path.join("./data", file), file))

    selectedFiles = SelectMultipleField(choices=sorted(logFiles), validators=[DataRequired()])
    submit = SubmitField('Submit')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    selectedFiles =  None
    status = "Select log files to analyze.  Already loaded: {}".format(lb.getLoadedFiles())
    form = AdminForm()
    DESC = "Log File Management"
    if form.validate_on_submit():
        status = "Loading data - loadedLogFiles, if submitted is stored in a session variable"
        for i in form.selectedFiles.data:
            lb.loadLogFile(i)
        lb.createAllIndexValueMaps()
        form.selectedFiles.data = None

        # lb.createAllIndexValueMaps()
        return redirect(url_for('analysis'))

    return render_template('admin.html', form=form, \
                           title=TITLE, desc=DESC, status=status)

@app.route('/analysis', methods=['GET'])
def analysis():

    DESC = "Summary Value Mappings across Log Entries"
    status = "Loaded LogEntries:  {}".format(lb.logEntryCount())

    # page_content = lb.printAllIndexValueMaps()

    page_content = lb.analysis_page_content()

    # print(page_content)
    return render_template("analysis.html", page_content = Markup(page_content),
                           title=TITLE, desc=DESC, status=status)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

@app.route('/counter')
def index():
    redis.incr('hits')
    status = "Redis 'hits' counter is incremented"
    return render_template("counter.html", hit_counts=redis.get('hits'),
                           title=TITLE, desc=DESC, status=status)

@app.route('/')
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

@app.route("/flushdb")
def flushdb():
    redis.flushdb()
    session['logEntryCount'] = 0
    lb._instance.le_Keys = set()
    lb._instance.indexValueMaps = {}
    return redirect(url_for('index'))

class ExecuteCmd(FlaskForm):

    cmd = StringField('Enter a command-line redis command ', validators=[DataRequired()])
    submit = SubmitField('Submit')

@app.route("/executeCmd", methods=['GET', 'POST'])
def executeCmd():
    # redis.execute_command()
    form=ExecuteCmd()
    cmd =  form.cmd.data 
    TITLE = "Redis Command Line Entry"
    DESC = "Executed Simple Redis Commands"
    status = "Ok"
    if form.validate_on_submit():
        status = "Command provided:{}".format(cmd)
        page_content = ""
        # print(redis.hgetall("logEntry:"+logEntryKey))
        response = redis.execute_command(cmd)
        page_content +="<h4>{}</h4>".format("Command:  "+ cmd)
        page_content +="<div>"
        page_content += "<p>{}</p>".format(response)
        page_content +="</div>"
        return render_template("analysis.html", page_content = Markup(page_content), \
                                title=TITLE, form=form, desc=DESC, status=status)
    return render_template("admin.html", form=form, title=TITLE, desc=DESC, status=status)


class LogEntryForm(FlaskForm):

    key = StringField('Enter the logEntryId (numeric index)  ', validators=[DataRequired()])
    submit = SubmitField('Submit')

@app.route('/logentry', methods=['GET', 'POST'])
def showLogEntry():
    form=LogEntryForm()
    logEntryKey =  form.key.data 
    TITLE = "LogEntry Data"
    DESC = "Show Log Entry Details by ID"
    status = "Provide logEntry ID"
    if form.validate_on_submit():
        status = "logEntry:{}".format(logEntryKey)
        page_content = ""
        # print(redis.hgetall("logEntry:"+logEntryKey))
        fieldValues = redis.hgetall("logEntry:"+logEntryKey)
        page_content +="<h4>{}</h4>".format("logEntry:"+logEntryKey)
        page_content +="<ul>"
        for i in sorted(fieldValues.keys()):
            page_content += "<li>{} : {}</li>".format(i, fieldValues[i])
        page_content +="</ul>"
        return render_template("admin.html", page_content = Markup(page_content), \
                                title=TITLE, form=form, desc=DESC, status=status)
    return render_template("admin.html", form=form, title=TITLE, desc=DESC, status=status)

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
    # app.run(debug=True,use_reloader=False)
