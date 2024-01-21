import os, psycopg2.extras, re
import sys, hashlib
from passlib.hash import sha256_crypt

class Response:
    def __init__(self):
        self.data = None
        self.msg = ""
        self.msgType = ""

def getDbConnection():
    conn = psycopg2.connect(
        host=os.environ['DB_HOST'],
        database=os.environ['DB_NAME'],
        user=os.environ['DB_USERNAME'],
        password=os.environ['DB_PASSWORD'])
    return conn

def isNaN(num):
    return num != num

def tryQuery(query, method):
    conn = getDbConnection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    match method:
        case "select":
            cur.execute(f"SELECT {query['columns']} FROM {query['table']} {query['condition']}")
            returned = cur.fetchall()
        case "insert":
            returned = cur.execute(f"INSERT INTO {query['table']} VALUES({query['condition']})")
            conn.commit()
        case "update":
            print(f"UPDATE {query['table']} SET {query['condition']}", file=sys.stderr)
            returned = cur.execute(f"UPDATE {query['table']} SET {query['condition']}")
            conn.commit()
        case "delete":
            returned = cur.execute(f"DELETE FROM {query['table']} {query['condition']}")
            conn.commit()
        case _:
            returned = -1
    cur.close()
    conn.close()
    return returned

def getTrainers():
    ret = Response()
    query = {
        'table': 'users',
        'columns': 'login',
        'condition': 'WHERE type LIKE \'trainer\''
    }
    ret.data = tryQuery(query, 'select')
    return ret

def getUserTypes():
    ret = Response()
    query = {
        'table': 'user_types',
        'columns': '*',
        'condition': ''
    }
    ret.data = tryQuery(query, 'select')
    return ret

def getClubs():
    ret = Response()
    query = {
        'table': 'clubs',
        'columns': '*',
        'condition': ''
    }
    ret.data = tryQuery(query, 'select')
    return ret

def isMember(userLogin, clubShortname):
    query = {
        'table': 'club_user',
        'columns': '*',
        'condition': f'WHERE user_login LIKE \'{userLogin}\' AND club LIKE \'{clubShortname}\''
    }
    data = tryQuery(query, 'select')
    if len(data) == 1:
        return True
    else:
        return False
    
def getUserResults(userLogin):
    ret = Response()
    conn = getDbConnection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    query = f"""
        SELECT t.name, t.date, t.time, t.description, r.result, g.grade
        FROM trainings t
        LEFT JOIN results r
        ON t.id = r.training_id
        LEFT JOIN grades g
        ON t.id = g.training_id
        WHERE r.user_login LIKE \'{userLogin}\'
        AND g.user_login LIKE \'{userLogin}\';
    """
    cur.execute(query)
    ret.data = cur.fetchall()
    cur.close()
    conn.close()
    return ret
    
def getUserClubResults(userLogin, clubShortname):
    ret = Response()
    conn = getDbConnection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    query = f"""
        SELECT t.name, t.date, t.time, t.description, r.result, g.grade
        FROM trainings t
        LEFT JOIN results r
        ON t.id = r.training_id
        LEFT JOIN grades g
        ON t.id = g.training_id
        WHERE t.club LIKE \'{clubShortname}\'
        AND r.user_login LIKE \'{userLogin}\'
        AND g.user_login LIKE \'{userLogin}\';
    """
    cur.execute(query)
    ret.data = cur.fetchall()
    cur.close()
    conn.close()
    return ret

def getTrainings(userLogin, clubShortname):
    ret = Response()
    query = {
        'table': 'trainings',
        'columns': '*',
        'condition': f'WHERE trainer LIKE \'{userLogin}\' AND club LIKE \'{clubShortname}\' ORDER BY date, time ASC'
    }
    ret.data = tryQuery(query, 'select')
    return ret

def getTraining(id):
    ret = Response()
    query = {
        'table': 'trainings',
        'columns': '*',
        'condition': f'WHERE id = {id}'
    }
    ret.data = tryQuery(query, 'select')
    return ret

def getTrainingGrades(trainingId):
    ret = Response()
    conn = getDbConnection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    query = f"""
        SELECT COALESCE(r.user_login, g.user_login) AS user_login, COALESCE(r.training_id, g.training_id) AS training_id, r.result, g.grade
        FROM results r
        FULL OUTER JOIN grades g
        ON r.user_login = g.user_login AND r.training_id = g.training_id
        WHERE COALESCE(r.training_id, g.training_id) = {trainingId}
        ORDER BY user_login DESC;
    """
    cur.execute(query)
    ret.data = cur.fetchall()
    cur.close()
    conn.close()
    return ret
    
def login(userLogin, userPass):
    ret = Response()
    if userLogin == "":
        ret.msg = "login cannot be empty"
        ret.msgType = "error"
        return ret
    if userPass == "":
        ret.msgType = "error"
        ret.msg = "password cannot be empty"
        return ret
    hash_object = hashlib.sha256()
    hash_object.update(userPass.encode())
    hash_password = hash_object.hexdigest()
    print(userPass, file=sys.stderr)
    print(hash_password, file=sys.stderr)
    query = {
        'table': 'users',
        'columns': '*',
        'condition': f'WHERE login LIKE \'{userLogin}\' AND password LIKE \'{hash_password}\''
    }
    ret.data = tryQuery(query, 'select')
    return ret

def register(userLogin, userPass, userType, trainerLogin):
    ret = Response()
    conn = getDbConnection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
    if userPass == "" or userLogin == "":
        ret.msgType = "error"
        ret.msg = "all fields must be filled"
        return ret
    if not re.fullmatch(regex, userLogin):
        ret.msgType = "error"
        ret.msg = "email must be valid"
        return ret
    if userType == "student" and trainerLogin == "":
        ret.msgType = "error"
        ret.msg = "all fields must be filled"
        return ret
    hash_object = hashlib.sha256()
    hash_object.update(userPass.encode())
    hash_password = hash_object.hexdigest()
    try:
        cur.execute(f'INSERT INTO users (login, password, type) VALUES(\'{userLogin}\', \'{hash_password}\', \'{userType}\')')
    except:
        ret.msgType = "error"
        ret.msg = "user already exists"
        return ret
    if trainerLogin is not None:
        cur.execute(f'INSERT INTO user_trainer (user_login, trainer_login) VALUES(\'{userLogin}\', \'{trainerLogin}\')')
    ret.data = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()
    return ret

def deleteTraining(trainingId):
    ret = Response()
    query = {
        'table': 'trainings',
        'condition': f'WHERE id = {trainingId}'
    }
    ret.data = tryQuery(query, 'delete')
    return ret

def addTraining(name, date, time, description, trainerLogin, clubShortname):
    ret = Response()
    if name == "" or date is None or time is None or description == "":
        ret.msgType = "error"
        ret.msg = "all fields must be filled"
        return ret
    query = {
        'table': 'trainings',
        'condition': f'DEFAULT, \'{name}\', \'{date}\', \'{time}\', \'{description}\', \'{trainerLogin}\', \'{clubShortname}\''
    }
    ret.data = tryQuery(query, 'insert')
    return ret

def addGrade(trainingId, student, grade):
    ret = Response()
    if trainingId == "" or student == "" or grade is None:
        ret.msgType = "error"
        ret.msg = "all fields must be filled"
        return ret
    if int(grade) > 10 or int(grade) < 0:
        ret.msgType = "error"
        ret.msg = "grade is incorrect"
        return ret
    query = {
        'table': 'grades',
        'condition': f'\'{trainingId}\', \'{student}\', \'{grade}\''
    }
    ret.data = tryQuery(query, 'insert')
    return ret

def editGrade(trainingId, student, grade):
    conn = getDbConnection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    ret = Response()
    if grade is None:
        ret.msgType = "error"
        ret.msg = "grade must be filled"
        return ret
    if int(grade) > 10 or int(grade) < 0:
        ret.msgType = "error"
        ret.msg = "grade is incorrect"
        return ret
    cur.execute(f'UPDATE grades SET grade = {grade} WHERE user_login LIKE \'{student}\' AND training_id = {trainingId}')
    ret.data = cur.rowcount
    if ret.data != 1:
        cur.execute(f'INSERT INTO grades (training_id, user_login, grade) VALUES(\'{trainingId}\', \'{student}\', \'{grade}\')')
    ret.data = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()
    return ret

def deleteGrade(trainingId, student):
    ret = Response()
    query = {
        'table': 'grades',
        'condition': f'WHERE user_login LIKE \'{student}\' AND training_id = {trainingId}'
    }
    ret.data = tryQuery(query, 'delete')
    return ret

def addResult(trainingId, student, result):
    ret = Response()
    if trainingId == "" or student == "" or result is None:
        ret.msgType = "error"
        ret.msg = "all fields must be filled"
        return ret
    if result == "":
        ret.msgType = "error"
        ret.msg = "result is incorrect"
        return ret
    query = {
        'table': 'results',
        'condition': f'\'{trainingId}\', \'{student}\', \'{result}\''
    }
    ret.data = tryQuery(query, 'insert')
    return ret

def editResult(trainingId, student, result):
    conn = getDbConnection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    ret = Response()
    if result is None:
        ret.msgType = "error"
        ret.msg = "result must be filled"
        return ret
    if result == "":
        ret.msgType = "error"
        ret.msg = "result is incorrect"
        return ret
    cur.execute(f'UPDATE results SET result = {result} WHERE user_login LIKE \'{student}\' AND training_id = {trainingId}')
    ret.data = cur.rowcount
    if ret.data != 1:
        cur.execute(f'INSERT INTO results (training_id, user_login, result) VALUES(\'{trainingId}\', \'{student}\', \'{result}\')')
    ret.data = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()
    return ret

def deleteResult(trainingId, student):
    ret = Response()
    query = {
        'table': 'results',
        'condition': f'WHERE user_login LIKE \'{student}\' AND training_id = {trainingId}'
    }
    ret.data = tryQuery(query, 'delete')
    return ret

def enroll(student, club):
    ret = Response()
    query = {
        'table': 'club_user',
        'condition': f'\'{student}\', \'{club}\''
    }
    ret.data = tryQuery(query, 'insert')
    return ret

def leave(student, club):
    ret = Response()
    query = {
        'table': 'club_user',
        'condition': f'WHERE user_login LIKE \'{student}\' AND club LIKE \'{club}\''
    }
    ret.data = tryQuery(query, 'delete')
    return ret

def getTrainerAthletes(trainer):
    ret = Response()
    query = {
        'table': 'user_trainer',
        'columns': 'user_login',
        'condition': f'WHERE trainer_login LIKE \'{trainer}\' ORDER BY user_login DESC'
    }
    ret.data = tryQuery(query, 'select')
    return ret

def getTrainerClubAthletes(trainer, club):
    ret = Response()
    conn = getDbConnection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    query = f"""
        SELECT ut.user_login
        FROM user_trainer ut
        JOIN club_user cu
        ON ut.user_login = cu.user_login
        WHERE cu.club LIKE \'{club}\' AND ut.trainer_login LIKE \'{trainer}\'
        ORDER BY ut.user_login DESC
    """
    cur.execute(query)
    ret.data = cur.fetchall()
    cur.close()
    conn.close()
    return ret

def getTrainerClubAthletesWithoutGrade(trainer, club, trainingId):
    ret = Response()
    conn = getDbConnection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    query = f"""
        SELECT ut.user_login
        FROM user_trainer ut
        JOIN club_user cu
        ON ut.user_login = cu.user_login
        WHERE cu.club LIKE \'{club}\' AND ut.trainer_login LIKE \'{trainer}\' AND ut.user_login NOT IN (
            SELECT user_login
            FROM grades
            WHERE training_id = {trainingId}
        )
        ORDER BY ut.user_login DESC
    """
    print(query, file=sys.stderr)
    cur.execute(query)
    ret.data = cur.fetchall()
    print(ret.data, file=sys.stderr)
    cur.close()
    conn.close()
    return ret

def getTrainerClubAthletesWithoutResult(trainer, club, trainingId):
    ret = Response()
    conn = getDbConnection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    query = f"""
        SELECT ut.user_login
        FROM user_trainer ut
        JOIN club_user cu
        ON ut.user_login = cu.user_login
        WHERE cu.club LIKE \'{club}\' AND ut.trainer_login LIKE \'{trainer}\' AND ut.user_login NOT IN (
            SELECT user_login
            FROM results
            WHERE training_id = {trainingId}
        )
        ORDER BY ut.user_login DESC
    """
    cur.execute(query)
    ret.data = cur.fetchall()
    cur.close()
    conn.close()
    return ret

def addPicture(user, picture):
    ret = Response()
    conn = getDbConnection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    picture = picture.replace('\'', '\'\'')
    cur.execute(f"UPDATE users set picture = \'{picture}\' WHERE login LIKE \'{user}\';")
    ret.data = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()
    return ret

def getPicture(user):
    ret = Response()
    query = {
        'table': 'users',
        'columns': 'picture',
        'condition': f'WHERE login LIKE \'{user}\''
    }
    ret.data = tryQuery(query, 'select')
    return ret