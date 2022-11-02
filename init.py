
from tkinter import Entry
from traceback import print_tb
from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re

app = Flask(__name__)


app.secret_key = 'chave secreta'

# CONECTANDO AO BANCO
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'clayton'
app.config['MYSQL_PASSWORD'] = '0209012'
app.config['MYSQL_DB'] = 'DB_POWERHUB_HM'

# INICIALIZANDO O MYSQL
mysql = MySQL(app)


# LANDPAGE
@app.route('/', methods=['GET', 'POST'])
def site():

    return render_template('login.html')
# LOGIN
@app.route('/powerhub/', methods=['GET', 'POST'])
def login():
    msg = ''
    # Verifique se existem solicitações POST "username" e "password" (formulário enviado pelo usuário)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.callproc('sp_autenticaUsuario', (username, password))
        tb_usuario = cursor.fetchone()

        if tb_usuario:
           # CRIANDO DADOS DE SESSÃO
            session['loggedin'] = True
            session['NOME_USUARIO']  = tb_usuario['NOME_USUARIO']
            session['ID_USUARIO']   = tb_usuario['ID_USUARIO']
            session['ID_GRUPO']  = tb_usuario['ID_GRUPO']
            session['DS_SENHA'] = tb_usuario['DS_SENHA']
            session['ID_ORGANIZACAO'] = tb_usuario['ID_ORGANIZACAO']
            session['NOME_ORGANIZACAO'] = tb_usuario['NOME_ORGANIZACAO']
            session['FL_ADMINISTRADOR'] = tb_usuario['FL_ADMINISTRADOR']
            # REDIRECIONAR
            
            print(session['ID_ORGANIZACAO'])
            return redirect(url_for('home'))
        else:
            # VERIFICA SE O LOGIN ESTÁ CORRETO
            msg = 'Usuário e senha incorretos!'
        
    return render_template('login.html', msg=msg)

# LOGOUT
@app.route('/powerhub/logout')
def logout():
    # REMOVE A SESSÃO
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('username', None)
   return redirect(url_for('login'))

# ROTA DE REGISTRO
@app.route('/powerhub/register', methods=['GET', 'POST'])
def register():
    try:
        msg = ''
        if request.method == 'POST' and 'organizacao' in request.form and 'email' in request.form and 'telefone' in request.form and 'name' in request.form and 'username' in request.form and 'password' in request.form:
            DS_ORGANIZACAO = request.form['organizacao']
            DS_EMAIL = request.form['email']
            DS_NUMERO_TEL = request.form['telefone']
            DS_USUARIO = request.form['username']
            DS_NOME = request.form['name']
            DS_SENHA = request.form['password']
            

            # VERIFICA SE O USUARIO EXISTE NO BANCO
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM TB_USUARIO WHERE DS_LOGIN = %s OR DS_SENHA = %s', (DS_USUARIO, DS_SENHA), ) # VERIFICA SE O USUARIO EXISTE NO BANCO
            account = cursor.fetchone()

            # VERIFICA SE O USUARIO EXISTE NO BANCO
            if account:
                msg = 'Alguém está utilizando esse mesmo login ou senha!'
            # VERIFICA SE O CAMPO ESTÁ VAZIO
            if not DS_ORGANIZACAO or not DS_NOME or not DS_EMAIL or not DS_NUMERO_TEL or not DS_USUARIO or not DS_SENHA:
                msg = 'Por favor, preencha o formulário!'
            # VERIFICANDO SE O EMAIL É VALIDO
            elif not re.match(r'[^@]+@[^@]+\.[^@]+', DS_EMAIL):
                msg = 'E-mail inválido!'
            # VERIFICA SE O NOME DO USUARIO É VALIDO
            elif not re.match(r'[A-Za-z0-9]+', DS_USUARIO):
                msg = 'O nome de usuário deve conter apenas caracteres e números!'
            
            else:
                cursor.callproc('sp_create_organizacao_and_user', (
                    0, DS_ORGANIZACAO, 0, 1,
                    0, 'PW Grupo', 0, 1, 0,
                    0, DS_NOME, 0, DS_NUMERO_TEL, DS_EMAIL, DS_USUARIO, DS_SENHA, 1,
                    0, 0, 0, 0))
                mysql.connection.commit()
                msg = 'Usuário criado com sucesso'

        elif request.method == 'POST':
            msg = 'Por favor, preencha o formulário!'
        
        return render_template('register.html', msg=msg)

    except Exception as e:
        return render_template('error.html', error=str(e))


# LISTAS OS GRUPOS DO USUARIO
@app.route('/powerhub/home')
def home():
    if 'loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT GPU.ID_GRUPO, GPU.ID_USUARIO, GP.NOME_DO_GRUPO FROM TB_GRUPO_USUARIO GPU JOIN TB_GRUPO GP ON GPU.ID_GRUPO = GP.ID_GRUPO WHERE GPU.ID_USUARIO = %s', (session['ID_USUARIO'], ))
        grupos_usuario = cursor.fetchall()
        list_grupo_usuario =[]

        for row in grupos_usuario:
            list_grupo_usuario.append(row)
        cursor.close()

        return render_template('home.html', list_grupos_usuario=list_grupo_usuario)

    # CRIAR NOVO GRUPO
    if request.method == 'POST' and 'organizacao' in request.form and 'email' in request.form:
        if request.method == 'POST' and 'grupo' in request.form:
            DS_NOVO_GRUPO = request.form['grupo']
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM TB_GRUPO WHERE NOME_DO_GRUPO = %s', (DS_NOVO_GRUPO, ))
            grupo = cursor.fetchone()
            if grupo:
                msg = 'Já existe um grupo com o mesmo nome!'
            else:
                cursor.callproc('sp_create_grupo', (0, DS_NOVO_GRUPO, 1))
                mysql.connection.commit()
                msg = 'Grupo criado com sucesso!'
            return redirect(url_for('home'))
   
    return redirect(url_for('login'))


# LISTA RELATORIOS DO GRUPO
@app.route('/powerhub/listar_relatorios/<int:id_grupo>')
def listar_relatorios(id_grupo):
    if 'loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT GPU.ID_GRUPO, GP.NOME_DO_GRUPO FROM TB_GRUPO_USUARIO GPU JOIN TB_GRUPO GP ON GPU.ID_GRUPO = GP.ID_GRUPO WHERE GPU.ID_GRUPO = %s', (id_grupo,))
        id_grupo_g = cursor.fetchall()
        cursor.close()

        queryRelatorio = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        queryRelatorio.execute('SELECT DISTINCT RL.ID_RELATORIO, RL.DS_NOME_RELATORIO FROM TB_RELATORIO RL JOIN TB_GRUPO_USUARIO GPU ON GPU.ID_GRUPO = RL.ID_GRUPO WHERE GPU.ID_GRUPO = %s', (id_grupo,))
        NOME_RELATORIO = queryRelatorio.fetchall()

        return render_template('listar_relatorios.html', NOME_RELATORIO=NOME_RELATORIO)

    else:
        return redirect(url_for('home'))


#  LISTAR GRUPOS ERROR
@app.route('/powerhub/grupos')
def Grupos():
    if 'loggedin' in session:
        try:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT GP.NOME_DO_GRUPO, GP.ID_GRUPO FROM TB_GRUPO GP JOIN TB_GRUPO_USUARIO GPU ON GPU.ID_GRUPO = GP.ID_GRUPO WHERE GPU.ID_ORGANIZACAO = (%s)', (30,))
            grupos = cursor.fetchall()
            cursor.close()
            return render_template('grupos.html', grupos=grupos)
        except:
            return render_template('error.html', grupos=grupos)
    return redirect(url_for('login'))


# LISTA RELATORIOS
@app.route('/powerhub/visualizar_relatorio/<int:id_relatorio>')
def visualizar_relatorio(id_relatorio):
    if 'loggedin' in session:
        try:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM TB_RELATORIO WHERE ID_RELATORIO = %s', (id_relatorio,))
            visualizar_relatorio = cursor.fetchone()
            cursor.close()
            print(visualizar_relatorio['DS_LINK_RELATORIO']) # DEBUG
            return render_template('visualizar_relatorio.html', visualizar_relatorio=visualizar_relatorio)
        except:
            return render_template('error.html', visualizar_relatorio=visualizar_relatorio)
    return redirect(url_for('login'))


# LISTAR USUARIOS DO SISTEMA
@app.route('/powerhub/profile')
def profile():
    if 'loggedin' in session:
        try:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM TB_USUARIO WHERE NOME_USUARIO = %s', (session['NOME_USUARIO'],))
            account = cursor.fetchone()
            return render_template('usuarios.html', account=account)
        except:
            return render_template('error.html', account=account)
    return redirect(url_for('login'))



if __name__ == '__main__':
    app.run(debug=True)

