from flask import Blueprint, request, render_template, redirect, url_for, session
import src.llib as llib
import sys

blueprint = Blueprint('clubs', __name__)

@blueprint.route('/club/<shortname>', methods=['GET'])
def main(shortname):
    ret = llib.Response()
    if shortname is None:
        return redirect(url_for('main', msg=None))
    if session['userType'] == "athlete":
        isMember = llib.isMember(session['user'], shortname)
        print(isMember, file=sys.stderr)
        if isMember:
            ret = llib.getUserClubResults(session['user'], shortname)
        return render_template('clubs/index.html', back=url_for('main'), member=isMember, results=ret.data, shortname=shortname, msg=None)
    else:
        ret = llib.getTrainings(session['user'], shortname)
        return render_template('clubs/index_trainer.html', back=url_for('main'), results=ret.data, shortname=shortname, msg=None)

@blueprint.route('/club/enroll/<shortname>', methods=['GET'])
def enroll(shortname):
    ret = llib.enroll(session['user'], shortname)
    if ret.data != 1:
        return redirect(url_for('main'))
    return redirect(url_for('clubs.main', shortname=shortname))
    
@blueprint.route('/club/leave/<shortname>', methods=['GET'])
def leave(shortname):
    ret = llib.leave(session['user'], shortname)
    if ret.data != 1:
        return redirect(url_for('main'))
    return redirect(url_for('clubs.main', shortname=shortname))

@blueprint.route('/clubs/<shortname>/insert', methods=['POST'])
def insert(shortname):
    ret = llib.addTraining(request.form.get('name'), request.form.get('date'), request.form.get('time'), request.form.get('description'), session['user'], shortname)
    return redirect(url_for('clubs.main', shortname=shortname))

@blueprint.route('/clubs/<shortname>/new', methods=['GET'])
def new(shortname):
    return render_template('trainings/new.html', back=url_for('clubs.main', shortname=shortname), msg=None, shortname=shortname)

@blueprint.route('/clubs/<shortname>/describe/<id>', methods=['GET'])
def describe(shortname, id):
    training = llib.getTraining(id)
    grades = llib.getTrainingGrades(id)
    numbers = {
        'resultAvg': 0,
        'resultCount': 0,
        'gradeAvg': 0,
        'gradeCount': 0
    }
    for line in grades.data:
        if line['result'] is not None:
            numbers['resultCount'] = numbers['resultCount'] + 1
            numbers['resultAvg'] = numbers['resultAvg'] + int(line['result'])
        if line['grade'] is not None:
            numbers['gradeCount'] = numbers['gradeCount'] + 1
            numbers['gradeAvg'] = numbers['gradeAvg'] + int(line['grade'])
    if numbers['resultCount'] == 0:
        numbers['resultAvg'] = "Inf"
    else:
        numbers['resultAvg'] = numbers['resultAvg']/numbers['resultCount']
    if numbers['gradeCount'] == 0:
        numbers['gradeAvg'] = "Inf"
    else:
        numbers['gradeAvg'] = numbers['gradeAvg']/numbers['gradeCount']
        
    return render_template('trainings/index.html', back=url_for('clubs.main', shortname=shortname), msg=None, shortname=shortname, training=training.data[0], grades=grades.data, numbers=numbers)
    
@blueprint.route('/clubs/<shortname>/delete/<id>', methods=['GET'])
def delete(shortname, id):
    ret = llib.deleteTraining(id)
    return redirect(url_for('clubs.main', shortname=shortname))

@blueprint.route('/grade/<shortname>/<id>', methods=['POST', 'GET'])
def grade(id, shortname):
    if request.method == "POST":
        ret = llib.addGrade(id, request.form.get('athlete'), request.form.get('grade'))
        return redirect(url_for('clubs.describe', id=id, shortname=shortname))
    else:
        athletes = llib.getTrainerClubAthletesWithoutGrade(session['user'], shortname, id)
        return render_template('results/grade.html', back=url_for('clubs.describe', id=id, shortname=shortname), id=id, shortname=shortname, athletes=athletes.data, msg=None)
    
@blueprint.route('/result/<shortname>/<id>', methods=['POST', 'GET'])
def result(id, shortname):
    if request.method == "POST":
        ret = llib.addResult(id, request.form.get('athlete'), request.form.get('result'))
        return redirect(url_for('clubs.describe', id=id, shortname=shortname))
    else:
        athletes = llib.getTrainerClubAthletesWithoutResult(session['user'], shortname, id)
        return render_template('results/result.html', back=url_for('clubs.describe', id=id, shortname=shortname), id=id, shortname=shortname, athletes=athletes.data, msg=None)
    
@blueprint.route('/editGrade/<user>/<shortname>/<id>', methods=['GET'])
@blueprint.route('/editGrade/<shortname>/<id>', methods=['POST'])
def editGrade(shortname, id, user=None):
    if request.method == "POST":
        ret = llib.editGrade(id, request.form.get('athlete'), request.form.get('grade'))
        return redirect(url_for('clubs.describe', id=id, shortname=shortname))
    else:
        return render_template('results/editGrade.html', back=url_for('clubs.describe', id=id, shortname=shortname), id=id, shortname=shortname, user=user, msg=None)
    
@blueprint.route('/deleteGrade/<shortname>/<id>/<user>')
def deleteGrade(shortname, id, user):
    ret = llib.deleteGrade(id, user)
    return redirect(url_for('clubs.describe', id=id, shortname=shortname))

@blueprint.route('/editResult/<user>/<shortname>/<id>', methods=['GET'])
@blueprint.route('/editResult/<shortname>/<id>', methods=['POST'])
def editResult(shortname, id, user=None):
    if request.method == "POST":
        ret = llib.editResult(id, request.form.get('athlete'), request.form.get('result'))
        return redirect(url_for('clubs.describe', id=id, shortname=shortname))
    else:
        return render_template('results/editResult.html', back=url_for('clubs.describe', id=id, shortname=shortname), id=id, shortname=shortname, user=user, msg=None)
    
@blueprint.route('/deleteResult/<shortname>/<id>/<user>')
def deleteResult(shortname, id, user):
    ret = llib.deleteResult(id, user)
    return redirect(url_for('clubs.describe', id=id, shortname=shortname))