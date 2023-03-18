
from flask_mysqldb import MySQL
import MySQLdb.cursors
from flask import Flask

app  = Flask(__name__,
template_folder="../templates",
static_folder="../static")

app.secret_key = 'chave secreta'

# CONECTANDO AO BANCO
app.config['MYSQL_HOST'] = 'containers-us-west-160.railway.app'
app.config['MYSQL_PORT'] = 7260
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'xe2A1MBtBgrtAOoiTeTx'
app.config['MYSQL_DB'] = 'railway'

# INICIALIZANDO O MYSQL
mysql = MySQL(app)
