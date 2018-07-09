import pymysql
import pymysql.cursors


class SQLConnector():
    def __init__(self, host='localhost',
                 pwd=None, db='db', user=None):
        self.connection = pymysql.connect(host=host,
                                          user=user,
                                          password=pwd,
                                          db=db,
                                          cursorclass=pymysql.cursors.DictCursor)

    def exec_sql(self, sql):
        with self.connection.cursor() as cursor:
            # Read a single record
            num_rows = cursor.execute(sql)
            result = []
            for i in range(num_rows):
                result.append(cursor.fetchone())
            return result
        return None