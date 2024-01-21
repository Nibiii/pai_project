from flask import Blueprint, request, render_template, redirect, url_for, session
import src.llib as llib
import sys, base64

blueprint = Blueprint('users', __name__)

@blueprint.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == "POST":
        ret = llib.login(request.form.get('login'), request.form.get('password'))
        if ret.data is None or ret.data == []:
            return render_template('users/login.html', msg="Wrong credentials", msgType="error", back=url_for('main'))
        session['user'] = ret.data[0]['login']
        session['userType'] = ret.data[0]['type']
        session['loggedIn'] = True
        return redirect(url_for('main'))
    else:
        return render_template('users/login.html', back=url_for('main'), msg=None)


@blueprint.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == "POST":
        ret = llib.register(request.form.get('login'), request.form.get('password'), request.form.get('userType'), request.form.get('trainer'))
        if ret.data != 1:
            return render_template('users/register.html', msg=ret.msg, msgType=ret.msgType, back=url_for('main'))
        session['user'] = request.form.get('login')
        session['userType'] = request.form.get('userType')
        session['loggedIn'] = True
        return redirect(url_for('main'))
    else:
        ret = llib.getUserTypes()
        ret2 = llib.getTrainers()
        return render_template('users/register.html', back=url_for('main'), userTypes=ret.data, trainers=ret2.data, msg=None)
    
@blueprint.route('/logout')
def logout():
    session.pop("loggedIn", None)
    session.pop("user", None)
    session.pop("userType", None)
    return redirect(url_for('main'))

@blueprint.route('/user/<user>')
@blueprint.route('/user')
def profile(user=None):
    if user is not None and session['userType'] == "trainer" and user != session['user']:
        ret = llib.getTrainerAthletes(session['user'])
        print(user, file=sys.stderr)
        print(ret.data[0], file=sys.stderr)
        if {'user_login': user} in ret.data:
            ret = llib.getUserResults(user)
            return render_template('users/profile.html', back=url_for('main'), results=ret.data, user=user, msg=None)
        else:
            return redirect(url_for('main'))
    else:
        print("elo", file=sys.stderr)
        ret = llib.getUserResults(session['user'])
        ret2 = llib.getPicture(session['user'])
        print(ret2.data, file=sys.stderr)
        return render_template('users/profile.html', back=url_for('main'), results=ret.data, user=session['user'], picture=ret2.data, msg=None)
    
@blueprint.route('/user/addPicture', methods=['POST', 'GET'])
def addPicture():
    if request.method == "POST":
        picture = request.files['picture']
        picture = 'data:image/png;base64,{}'.format(base64.b64encode(picture.read()))
        llib.addPicture(session['user'], picture)
        return redirect(url_for('users.profile'))
    else:
        return render_template('users/pictureAdd.html', back=url_for('main'))
    
@blueprint.route('/user/editPicture', methods=['POST', 'GET'])
def editPicture():
    if request.method == "POST":
        picture = request.files['file']
        picture = 'data:image/png;base64,{}'.format(base64.b64encode(picture.stream))
        llib.addPicture(session['user'], picture)
        return redirect(url_for('users.profile'))
    else:
        return render_template('users/pictureAdd.html', back=url_for('main'))
    
@blueprint.route('/users', methods=['GET'])
def listAthletes():
    ret = llib.getTrainerAthletes(session['user'])
    return render_template('users/listAthletes.html', back=url_for('main'), athletes=ret.data)