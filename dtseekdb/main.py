import lxml
import pymysql
import requests
import bs4
import pyquery

def testdb():
    db = pymysql.connect(host='156.67.222.85', user='u894340352_spiders', password='1gmA#x4z', port=3306, db='u894340352_spiders')
    cursor = db.cursor()
    sql = 'CREATE TABLE IF NOT EXISTS students (id VARCHAR(255) NOT NULL, name VARCHAR(255) NOT NULL, age INT NOT NULL, PRIMARY KEY (id))'
    cursor.execute(sql)
    db.close()

def insertdb():
    id = '20120001'
    user = 'Bob'
    age = 20
    db = pymysql.connect(host='156.67.222.85', user='u894340352_spiders', password='1gmA#x4z', port=3306, db='u894340352_spiders')
    cursor = db.cursor()
    sql = 'INSERT INTO students(id, name, age) values(%s, %s, %s)'
    try:
        cursor.execute(sql, (id, user, age))
        db.commit()
    except:
        print('Exception occur')
        db.rollback()
    db.close()

def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press Ctrl+F8 to toggle the breakpoint.


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print_hi('PyCharm')
    testdb()
    insertdb()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
