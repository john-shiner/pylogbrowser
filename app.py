from flask import Flask
from redis import Redis, RedisError
import os 

from flask import render_template, session, redirect, url_for, Markup, request
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectMultipleField, SelectField
from wtforms.validators import DataRequired

from LogBrowser import LogBrowser as LB
from LogBrowser import redis
from LogBrowser import IndexMgr

app = Flask(__name__)
app.config['SECRET_KEY'] = 'hard to guess string'

bootstrap = Bootstrap(app)
moment = Moment(app)

TITLE = "Web Log Browser"
DESC = "Redis Modeling Demo"
status = "Status - so far so good"

lb = LB()

class IndexForm(FlaskForm):
    fieldChoices = []
    for i in LB.supportedIndices():
        fieldChoices.append((i, i))
    selectedIndex = SelectField("Select Index", choices=fieldChoices, validators=[DataRequired()])
    submit = SubmitField('Submit')

@app.route('/', methods=['GET', 'POST'])
@app.route('/field', methods=['GET', 'POST'])
def field():
    selectedIndex =  None
    status = "Select Field Value"
    form = IndexForm()
    DESC = "Browse by Field Values"
    if form.validate_on_submit():
        status = "Analysis for {}".format(form.selectedIndex.data)
        page_content = IndexMgr.indexValueManagers[form.selectedIndex.data].tab_content()

        form.selectedIndex.data = None

        # lb.createAllIndexValueMaps()
        return render_template('analysis.html', page_content= Markup(page_content), title=TITLE, desc=DESC, status=status)

    return render_template('admin.html', form=form, title=TITLE, desc=DESC, status=status)

@app.route('/browsefield/<indexfield>', methods=['GET'])
def browsefield(indexfield):
    print("indexfield = {}".format(indexfield))
    selectedIndex = indexfield
    print("selectedIndex = {}".format(selectedIndex))

    TITLE = "LogEntry Data"
    DESC = "Show Log Entry Details by ID"
    status = "Field values for field: {}".format(selectedIndex)


    DESC = "Distribution by {} Field Values".format(selectedIndex)

    page_content = IndexMgr.indexValueManagers[selectedIndex].tab_content()

    return render_template('analysis.html', page_content= Markup(page_content), title=TITLE, desc=DESC, status=status)


class LogFileForm(FlaskForm):    

    selectedFiles = SelectMultipleField(validators=[DataRequired()])
    submit = SubmitField('Submit')

@app.route('/loadfiles', methods=['GET', 'POST'])
def loadfiles():

    selectedFiles =  None
    status = "Select log files to analyze.  Already loaded: {}".format(LB.getLoadedFiles())
    form = LogFileForm()
    DESC = "Log File Management"
    try:
        form.selectedFiles.choices = []
        for file in sorted(os.listdir("./data")):

            if file.endswith(".log"):
                form.selectedFiles.choices.append((os.path.join("./data", file), file))
    except TypeError:
        pass

    if form.validate_on_submit():
        status = "Loading data - loadedLogFiles, if submitted is stored in a session variable"
        for i in form.selectedFiles.data:
            lb.loadLogFile(i)
        form.selectedFiles.data = None

        IndexMgr.createAllIndexValueMaps()
        return redirect(url_for('analysis'))

    return render_template('admin.html', form=form, \
        title=TITLE, desc=DESC, status=status)

@app.route('/analysis', methods=['GET'])
def analysis():

    DESC = "Summary Value Mappings across Log Entries"
    status = "Loaded LogEntries:  {}".format(LB.logEntryCount())

    # page_content = lb.printAllIndexValueMaps()

    page_content = lb.analysis_table_content()

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

class MapForm(FlaskForm):
    selectedIndex = SelectField("Select Index", validators=[DataRequired()])
    submit = SubmitField('Submit')

@app.route("/mapfieldval/mapkey=<mapkey>", methods=['GET', 'POST'])
def mapfieldval(mapkey):
    # http://0.0.0.0:5000/mapfieldval/mapkey=map:soap_operation:grantOrgAward
    print("1) mapkey = {}".format(mapkey))
    keyval = request.args.get('mapkey', default='', type=str)

    # convert the mapkey value to match db key formatting
    # ^ was substituted for / to ease URL creation
    searchKey = mapkey.replace("^","/")

    redis.set("logmap", searchKey)

    if searchKey == None:
        print("MapForm-searchKey == None)")

        redirect(url_for('analysis'))
    idx = searchKey.split(":")[1]
    val = searchKey.split(":")[2]

     # form.fieldChoices = choices
    DESC = "LogEntries Index: {}  Value: {}".format(idx, val)
    status = "Map Key is {}".format(searchKey)
    form = MapForm()

    # Calculate dynamic field choices
    try:
        fieldChoices = []
        form.selectedIndex.choices = []
        if redis.exists("logmap"): 
            searchKey = redis.get("logmap")  
            print("2) get logmap == {}".format(searchKey))
            # print(redis.zrange(searchKey, "0", "-1"))    
            for i in redis.zrange(searchKey, "0", "-1"):
                form.selectedIndex.choices.append((i, i))

    except TypeError:
        pass

    if form.validate_on_submit():

        selectedLogKey = form.selectedIndex.data
        form.selectedIndex.data=""

        return redirect(url_for('browseLogEntry', logkey=selectedLogKey))

    return render_template('mapform.html', form=form, title=TITLE, desc=DESC, status=status)

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
        response_str = ""
        # print(redis.hgetall("logEntry:"+logEntryKey))
        response = redis.execute_command(cmd)
        if type(response) == list:
            response_str += "<ul>"
            for i in response:

                response_str += "<li>{}</li>".format(i)
            response_str += "</ul>"

        page_content +="<h4>{}</h4>".format("Command:  "+ cmd)
        page_content +="<div>"
        if type(response) == list:
            page_content += response_str
        else:
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
        DESC = "Log Entry Details by ID ({})".format(logEntryKey)
        page_content = ""
        # print(redis.hgetall("logEntry:"+logEntryKey))
        fieldValues = redis.hgetall("logEntry:"+logEntryKey)
        page_content +="<h4>{}</h4>".format("logEntry:"+logEntryKey)
        page_content +="<ul>"
        for i in sorted(fieldValues.keys()):
            # self.table_content += "<td><a href=\"/mapfieldval/mapkey=map:{}:{}\">map:{}:{}</a></td>".format(self.fieldName, index_value, self.fieldName, j)
            if i in LB.supportedIndices():
                indexlink = "<a href=\"/browsefield/{}\">{}</a>".format(i, i)
                index_value = fieldValues[i].replace("/","^")
                val = "<a href=\"/mapfieldval/mapkey=map:{}:{}\">map:{}</a>".format(i, index_value, fieldValues[i])
                page_content += "<li>{} : {}</li>".format(indexlink, val)
            else:
                page_content += "<li>{} : {}</li>".format(i, fieldValues[i])
        page_content +="</ul>"
        return render_template("admin.html", page_content = Markup(page_content), \
                                title=TITLE, form=form, desc=DESC, status=status)
    return render_template("admin.html", form=form, title=TITLE, desc=DESC, status=status)

@app.route('/browselogentry', methods=['GET'])
def browseLogEntry(logkey=""):
    if len(request.args['logkey']) > 0:
        logEntryKey = request.args['logkey']
    else:
        return

    TITLE = "LogEntry Data"
    DESC = "Log Entry Details by ID ({})".format(logEntryKey)
    status = "logEntry:{}".format(logEntryKey)
    page_content = ""
    # print(redis.hgetall("logEntry:"+logEntryKey))
    fieldValues = redis.hgetall("logEntry:"+logEntryKey)
    page_content +="<h4>{}</h4>".format("logEntry:"+logEntryKey)
    page_content +="<ul>"
    for i in sorted(fieldValues.keys()):
        # self.table_content += "<td><a href=\"/mapfieldval/mapkey=map:{}:{}\">map:{}:{}</a></td>".format(self.fieldName, index_value, self.fieldName, j)
        if i in LB.supportedIndices():
            indexlink = "<a href=\"/browsefield/{}\">{}</a>".format(i, i)
            index_value = fieldValues[i].replace("/","^")
            val = "<a href=\"/mapfieldval/mapkey=map:{}:{}\">map:{}</a>".format(i, index_value, fieldValues[i])
            page_content += "<li>{} : {}</li>".format(indexlink, val)
        else:
            page_content += "<li>{} : {}</li>".format(i, fieldValues[i])
    page_content +="</ul>"
    return render_template("base.html", page_content = Markup(page_content), \
                            title=TITLE, desc=DESC, status=status)

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
    # app.run(host="0.0.0.0", debug=True, use_reloader=False)

