
from flask_mysqldb import MySQL
import MySQLdb.cursors
from flask import Flask

app  = Flask(__name__,
template_folder="../templates",
static_folder="../static")

app.secret_key = 'chave secreta'

# CONECTANDO AO BANCO
app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'cs0209012'
app.config['MYSQL_DB'] = 'DB_POWERHUB_HM'

# INICIALIZANDO O MYSQL
mysql = MySQL(app)
