
from flask_mysqldb import MySQL
import MySQLdb.cursors
from flask import Flask

app  = Flask(__name__,
template_folder="../templates",
static_folder="../static")

app.secret_key = 'chave secreta'

# CONECTANDO AO BANCO
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'clayton'
app.config['MYSQL_PASSWORD'] = '****'
app.config['MYSQL_DB'] = 'DB_POWERHUB_HM'

# INICIALIZANDO O MYSQL
mysql = MySQL(app)
