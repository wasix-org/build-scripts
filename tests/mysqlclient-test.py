# docker run -p 3306:3306 --rm -it --name some-mysql -e MYSQL_ROOT_PASSWORD=password  mysql:latest

from MySQLdb import _mysql
db=_mysql.connect(host="127.0.0.1",port=3306,user="root",password="password")

db.query("SELECT VERSION()")

result = db.use_result()
row = result.fetch_row()

print("MySQL Server Version:", row[0][0])