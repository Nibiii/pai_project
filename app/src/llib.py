import os, psycopg2.extras, re
from passlib.hash import sha256_crypt

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
    query = {
        'table': 'users',
        'columns': 'login',
        'condition': 'WHERE type LIKE \'trainer\''
    }
    trainers = tryQuery(query, 'select')
    return trainers

def getUserTypes():
    query = {
        'table': 'user_types',
        'columns': 'type'
    }
    types = tryQuery(query, 'select')
    return types

def getClubs():
    query = {
        'table': 'clubs',
        'columns': '*'
    }
    clubs = tryQuery(query, 'select')
    return clubs

def isMember(userLogin, clubShortname):
    query = {
        'table': 'club_student',
        'columns': '*',
        'condition': f'WHERE user_login LIKE \'{userLogin}\' AND club_shortname LIKE \'{clubShortname}\''
    }
    data = tryQuery(query, 'select')
    if len(data) == 1:
        return True
    else:
        return False
    
def getUserResults(userLogin, clubShortname):
    conn = getDbConnection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    query = f"""
        SELECT t.name, t.date, t.time, t.description, r.result, g.grade
        FROM trainings t
        LEFT JOIN results r
        ON t.id = r.id
        LEFT JOIN grades g
        ON t.id = g.id
        WHERE t.club_shortname LIKE \'{clubShortname}\'
        AND r.user_login LIKE \'{userLogin}\'
        AND g.user_login LIKE \'{userLogin}\';
    """
    cur.execute(query)
    results = cur.fetchall()
    cur.close()
    conn.close()
    return results

def getTrainings(userLogin, clubShortname):
    query = {
        'table': 'trainings',
        'columns': '*',
        'condition': f'WHERE user_login LIKE \'{userLogin}\' AND club_shortname LIKE \'{clubShortname}\''
    }
    trainings = tryQuery(query, 'select')
    return trainings

def getTrainingDetails(trainingId):
    conn = getDbConnection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    query = f"""
        SELECT r.user_login, r.result, g.grade
        FROM results r
        JOIN grades g
        ON r.user_login = g.user_login
        WHERE training_id = {trainingId};
    """
    cur.execute(query)
    trainings = cur.fetchall()
    cur.close()
    conn.close()
    return trainings
    
def login(userLogin, userPass):
    if userLogin == "":
        return "login cannot be empty"
    if userPass == "":
        return "password cannot be empty"
    query = {
        'table': 'users',
        'columns': '*',
        'condition': f'WHERE login LIKE \'{userLogin}\' AND password LIKE \'{sha256_crypt.encrypt(userPass)}\''
    }
    user = tryQuery(query, 'select')
    return user

def register(userLogin, userPass, userType, trainerLogin):
    conn = getDbConnection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
    if userPass == "" or userLogin == "":
        return "all fields must be filled"
    if not re.fullmatch(regex, userLogin):
        return "email must be valid"
    if userType == "student" and trainerLogin == "":
        return "all fields must be filled"
    try:
        cur.execute(f'INSERT INTO users (login, password, type) VALUES(\'{userLogin}\', \'{sha256_crypt.encrypt(userPass)}\', \'{userType}\');')
    except:
        return "user already exists"
    cur.execute(f'INSERT INTO user_trainer (user_login, trainer_login) VALUES(\'{userLogin}\', \'{trainerLogin}\');')
    conn.commit()
    cur.close()
    conn.close()
    return None

def deleteTraining(trainingId):
    query = {
        'table': 'trainings',
        'condition': f'WHERE id = {trainingId}'
    }
    return tryQuery(query, 'delete')

def addTraining(name, datetime, description, trainerLogin, clubShortname):
    if name == "" or datetime is None or description == "":
        return "all fields must be filled"
    query = {
        'table': 'trainings',
        'condition': f'\'{name}\', \'{datetime}\', \'{description}\', \'{trainerLogin}\', \'{clubShortname}\''
    }
    return tryQuery(query, 'insert')

def addGrade(trainingId, student, grade):
    if trainingId == "" or student == "" or grade is None:
        return "all fields must be filled"
    if grade > 10 or grade < 0:
        return "grade is incorrect"
    query = {
        'table': 'grades',
        'condition': f'\'{student}\', \'{trainingId}\', \'{grade}\''
    }
    return tryQuery(query, 'insert')

def editGrade()
 
# Make a regular expression
# for validating an Email
