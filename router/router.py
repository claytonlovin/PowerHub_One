from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from setting.config import *
import MySQLdb.cursors
from datetime import datetime
now = datetime.now()


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
        print(tb_usuario)
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
                    0, DS_NOME, DS_NUMERO_TEL, DS_EMAIL, DS_USUARIO, DS_SENHA, 1, 0,
                    0, 0, 0, 0))
                mysql.connection.commit()
                msg = 'Usuário criado com sucesso'

        elif request.method == 'POST':
            msg = 'Por favor, preencha o formulário!'
        
        return render_template('register.html', msg=msg)

    except Exception as e:
        return render_template('error.html', error=str(e))


# LISTAS OS GRUPOS DO USUARIO
@app.route('/powerhub/home', methods=['GET', 'POST', 'PUT', 'DELETE'])
def home():
    if 'loggedin' in session:
        # LISTA OS GRUPOS DO USUARIO
        if request.method == 'GET':
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT GPU.ID_GRUPO, GPU.ID_USUARIO, GP.NOME_DO_GRUPO FROM TB_GRUPO_USUARIO GPU JOIN TB_GRUPO GP ON GPU.ID_GRUPO = GP.ID_GRUPO WHERE GPU.ID_USUARIO = %s', (session['ID_USUARIO'], ))
            grupos_usuario = cursor.fetchall()
            list_grupo_usuario =[]
            for row in grupos_usuario:
                list_grupo_usuario.append(row)
            cursor.close()
            
        # CRIAR NOVO GRUPO 
        criacao_grupo = ''
        if request.method == 'POST' and 'grupo' in request.form:
            DS_NOVO_GRUPO = request.form['grupo']
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM TB_GRUPO WHERE NOME_DO_GRUPO = %s', (DS_NOVO_GRUPO, ))
            grupo = cursor.fetchone()
            data = now.strftime('%Y-%m-%d %H:%M:%S')
                
            if grupo:
                criacao_grupo = 'Já existe um grupo com o mesmo nome!'
            else:
                cursor.callproc('sp_create_grupo', (0, DS_NOVO_GRUPO, data, 1, session['ID_ORGANIZACAO'], 0, 0, session['ID_USUARIO'], session['ID_ORGANIZACAO']))
                mysql.connection.commit()
                criacao_grupo = 'Grupo criado com sucesso!'
            return redirect(url_for('home'))

        return render_template('home.html', list_grupos_usuario=list_grupo_usuario, criacao_grupo=criacao_grupo)
    else:
        return redirect(url_for('login'))


# LISTA RELATORIOS DO GRUPO
@app.route('/powerhub/listar_relatorios/<int:id_grupo>', methods=['GET', 'POST', 'DELETE'])
def listar_relatorios(id_grupo):
    if 'loggedin' in session:
        if request.method == 'GET':
            try:
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute('SELECT GPU.ID_GRUPO, GP.NOME_DO_GRUPO FROM TB_GRUPO_USUARIO GPU JOIN TB_GRUPO GP ON GPU.ID_GRUPO = GP.ID_GRUPO WHERE GPU.ID_GRUPO = %s', (id_grupo,))
                id_grupo_g = cursor.fetchall()
                cursor.close()

                queryRelatorio = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                queryRelatorio.execute('SELECT DISTINCT RL.ID_RELATORIO, RL.ID_GRUPO,  RL.DS_NOME_RELATORIO FROM TB_RELATORIO RL JOIN TB_GRUPO_USUARIO GPU ON GPU.ID_GRUPO = RL.ID_GRUPO WHERE GPU.ID_GRUPO = %s', (id_grupo,))
                nome_relatorio = queryRelatorio.fetchall()
                queryRelatorio.close()

                return render_template('listar_relatorios.html', NOME_RELATORIO_GRUPO=nome_relatorio)
            except:
                return render_template('error.html')        
        # INSERIR RELATORIO
        
        if request.method == 'POST' and 'nome_relatorio' in request.form and 'link_relatorio' in request.form:
            DS_NOME_RELATORIO = request.form['nome_relatorio']
            DS_LINK_RELATORIO = request.form['link_relatorio']
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM TB_RELATORIO WHERE DS_LINK_RELATORIO = %s', (DS_LINK_RELATORIO,))
            relatorio = cursor.fetchone()
            msg = ''
            if relatorio:
                msg = 'Já existe um relatório com o mesmo link!'
            else:
                cursor.callproc('sp_create_relatorio', (0, DS_NOME_RELATORIO, DS_LINK_RELATORIO, id_grupo))
                mysql.connection.commit()
                msg = 'Relatório criado com sucesso!'
            return redirect(url_for('listar_relatorios', id_grupo=id_grupo))
    
    else:
        return render_template('error.html')

# LISTA RELATORIOS
@app.route('/powerhub/visualizar_relatorio/<int:id_relatorio>', methods=['GET', 'POST'])
def visualizar_relatorio(id_relatorio):
    if 'loggedin' in session:
        try:
            if request.method == 'GET':
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute('SELECT * FROM TB_RELATORIO WHERE ID_RELATORIO = %s', (id_relatorio,))
                visualizar_relatorio = cursor.fetchone()
                cursor.close()
                print(visualizar_relatorio['DS_LINK_RELATORIO']) # DEBUG
                
        except:
            return render_template('error.html', visualizar_relatorio=visualizar_relatorio)
        return render_template('visualizar_relatorio.html', visualizar_relatorio=visualizar_relatorio)
    return redirect(url_for('login'))


# LISTAR USUARIOS DO SISTEMA
@app.route('/powerhub/user')
def list_user():
    if 'loggedin' in session:
        try:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.callproc('sp_list_user', (session['ID_ORGANIZACAO'],))
            account = cursor.fetchall()
           # print(account['ID_USUARIO']) # DEBUG
            return render_template('usuarios.html', contas=account)
        except:
            return render_template('error.html')
    return redirect(url_for('login'))

# CRIAR USUARIO
@app.route('/powerhub/criar_usuario', methods=['GET', 'POST'])
def criar_usuario():
    if 'loggedin' in session:
        try:
            msg = ''
            if request.method == 'POST' and 'nome' in request.form and 'login' in request.form and 'telefone' in request.form and 'email' in request.form and 'senha' in request.form and 'confirmar_senha' in request.form:
                nome = request.form['nome']
                login = request.form['login']
                telefone = request.form['telefone']
                email = request.form['email']
                senha = request.form['senha']
                confirmar_senha = request.form['confirmar_senha']
                
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute('SELECT * FROM TB_USUARIO WHERE DS_EMAIL = %s', (email,))
                account = cursor.fetchone()
                if account:
                    msg = 'Já existe uma conta com esse e-mail!'
                elif not nome or not email or not senha or not confirmar_senha:
                    msg = 'Por favor, preencha todos os campos!'
                elif senha != confirmar_senha:
                    msg = 'As senhas não conferem!'
                else:
                    cursor.execute('INSERT INTO TB_USUARIO VALUES(%s, %s, %s, %s, %s, %s, %s, %s)', (0, nome, telefone, email, login, senha, 0, session['ID_ORGANIZACAO'], ))
                    mysql.connection.commit()
                    msg = 'Conta criada com sucesso!'
                    return redirect(url_for('list_user'))            
            return render_template('criar_usuario.html', msg=msg)
        except:
            return render_template('error.html')

# EDITAR USUARIO
@app.route('/powerhub/editar_usuario/<int:id_usuario>', methods=['GET', 'POST'])
def editar_usuario(id_usuario):
    if 'loggedin' in session:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM TB_USUARIO WHERE ID_USUARIO = %s', (id_usuario,))
            account = cursor.fetchone()
            if request.method == 'POST' and 'nome' in request.form and 'login' in request.form and 'telefone' in request.form and 'email' in request.form and 'senha' in request.form and 'confirmar_senha' in request.form:
                nome = request.form['nome']
                login = request.form['login']
                telefone = request.form['telefone']
                email = request.form['email']
                senha = request.form['senha']
                confirmar_senha = request.form['confirmar_senha']
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute('SELECT * FROM TB_USUARIO WHERE DS_EMAIL = %s', (email,))
                account = cursor.fetchone()
                if not nome or not email or not senha or not confirmar_senha:
                    msg = 'Por favor, preencha todos os campos!'
                elif senha != confirmar_senha:
                    msg = 'As senhas não conferem!'
                else:
                    cursor.execute('UPDATE TB_USUARIO SET NOME_USUARIO = %s, DS_TELEFONE = %s, DS_EMAIL = %s, DS_LOGIN = %s, DS_SENHA = %s WHERE ID_USUARIO = %s', (nome, telefone, email, login, senha, id_usuario,))
                    mysql.connection.commit()
                    msg = 'Conta atualizada com sucesso!'
                    return redirect(url_for('list_user'))            
            return render_template('v_editar_usuario.html', account=account) 
        

#  LISTAR GRUPOS ERROR
@app.route('/powerhub/grupos')
def Grupos():
    if 'loggedin' in session:
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT DISTINCT GP.NOME_DO_GRUPO, GP.ID_GRUPO FROM TB_GRUPO_USUARIO GPU JOIN TB_GRUPO GP ON GPU.ID_GRUPO = GP.ID_GRUPO WHERE GPU.ID_ORGANIZACAO = (%s)', (session['ID_ORGANIZACAO'],))
        grupos = cursor.fetchall()
        cursor.close()
        return render_template('v_grupos.html', grupos=grupos) 
        
# VINCULAR USUARIO AO GRUPO
@app.route('/powerhub/vincular_usuario/<int:id_grupo>', methods=['GET', 'POST'])
def vincular_usuario(id_grupo):
    if 'loggedin' in session:
            if request.method == 'GET':
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute('SELECT * FROM TB_USUARIO US JOIN TB_GRUPO_USUARIO GPU ON US.ID_USUARIO = GPU.ID_USUARIO WHERE GPU.ID_GRUPO = (%s)', (id_grupo,))
                usuarios = cursor.fetchall()
                cursor.close()
                
                # TODOS OS USUARIOS
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute('SELECT distinct GPU.ID_GRUPO, us.* FROM TB_USUARIO US JOIN TB_GRUPO_USUARIO GPU ON US.ID_USUARIO <> GPU.ID_USUARIO JOIN TB_GRUPO GP ON GPU.ID_GRUPO <> GP.ID_GRUPO WHERE  US.ID_ORGANIZACAO = (%s) AND GPU.ID_GRUPO = (%s)', (session['ID_ORGANIZACAO'], id_grupo,))
                usuarios_nao_vinculados = cursor.fetchall()
                cursor.close()
                
                

            if request.method == 'POST' and 'id_usuario' in request.form:
                id_usuario = request.form['id_usuario']
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute('INSERT INTO TB_GRUPO_USUARIO VALUES(%s, %s, %s)', (0, id_grupo, id_usuario, session['ID_ORGANIZACAO'],))
                mysql.connection.commit()
                cursor.close()
                return redirect(url_for('Grupos'))
            
            return render_template('v_vincular_grupo.html', usuarios=usuarios, usuarios_nao_vinculados=usuarios_nao_vinculados)
