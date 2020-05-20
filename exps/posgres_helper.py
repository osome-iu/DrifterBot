import psycopg2 as psql
import pandas as pd

def loadPubKey(path='<key>'):
    with open(path) as key:
        return key.read().strip()

def getDataframeFromQuery(conn=None, sql=""):
    try:
        if (not conn) or conn.closed:
            conn = connect_db()
        cur = conn.cursor()
        cur.execute(sql)
        res = cur.fetchall()
        return pd.DataFrame(res, columns=[desc[0] for desc in cur.description])
    except Exception as e:
        print(e)
        conn.rollback()
    finally:
        if cur:
            cur.close()
            conn.close()
        
def addRecordToDatabase(conn, sql, param_lst):
    result=True
    try:
        cur = conn.cursor()
        cur.execute(sql, param_lst)
        conn.commit()
    except Exception as e:
        result=False
        print(e)
        conn.rollback()
    finally:
        if cur:
            cur.close()
        return result
    
def connect_db(host='<host>', database='<database>', user='<user>', password=loadPubKey()):
    return psql.connect(host=host, database=database, user=user, password=password)
        
