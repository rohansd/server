import pymysql.cursors

connection = pymysql.connect(host='database-1.czxn7uvkflod.us-west-2.rds.amazonaws.com',
                             user='admin',
                             password='SJSUSJSU7',
                             database='Masters_Project',
                             cursorclass=pymysql.cursors.DictCursor)

# with connection:
#     with connection.cursor() as cursor:
#         # Read a single record
#         sql = "Select * from Problems"
#         cursor.execute(sql)
#         result = cursor.fetchone()
#         print(result)