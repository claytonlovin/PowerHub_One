from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from setting.config import *
import MySQLdb.cursors
from datetime import datetime
now = datetime.now()
import hashlib
import re
import sys

# LANDPAGE
@app.route('/', methods=['GET', 'POST'])
def site():
    return render_template('/headers/index.html')
# LOGIN
@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.callproc('sp_autenticaUsuario', (email,))
        tb_usuario = cursor.fetchone()
       
        if tb_usuario:
            # Criptografia da senha digitada pelo usuário
            password_criptografada = hashlib.sha256(password.encode()).hexdigest()
            # Verifica se a senha criptografada é igual a senha armazenada no banco de dados
            if password_criptografada == tb_usuario['DS_SENHA']:
                # CRIANDO DADOS DE SESSÃO
                session['loggedin'] = True
                session['NOME_USUARIO']  = tb_usuario['NOME_USUARIO']
                session['ID_USUARIO']   = tb_usuario['ID_USUARIO']
                session['FL_PROPRIETARIO_CONTA'] = tb_usuario['FL_PROPRIETARIO_CONTA']
                session['DS_SENHA'] = tb_usuario['DS_SENHA']
                session['ID_ORGANIZACAO'] = tb_usuario['ID_ORGANIZACAO']
                session['NOME_ORGANIZACAO'] = tb_usuario['NOME_ORGANIZACAO']
                session['FL_ADMINISTRADOR'] = tb_usuario['FL_ADMINISTRADOR']
                session['PREMIUM'] = tb_usuario['PREMIUM']
                # REDIRECIONAR
                return redirect(url_for('home'))
            else:
                flash('Senha incorreta!', 'danger')
        else:
            flash('Usuário não encontrado!', 'danger')
        
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
@app.route('/register', methods=['GET', 'POST'])
def register():
        if request.method == 'POST' and 'organizacao' in request.form and 'email' in request.form and 'telefone' in request.form and 'name' in request.form and 'username' in request.form and 'password' in request.form:
            DS_ORGANIZACAO = request.form['organizacao']
            DS_EMAIL = request.form['email']
            DS_NUMERO_TEL = request.form['telefone']
            DS_USUARIO = request.form['username']
            DS_NOME = request.form['name']
            DS_SENHA = request.form['password']

            # Criptografar a senha
            senha_criptografada = hashlib.sha256(DS_SENHA.encode()).hexdigest()
                        
            data = now.strftime('%Y-%m-%d %H:%M:%S')
            # VERIFICA SE O USUARIO EXISTE NO BANCO
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM TB_USUARIO WHERE DS_LOGIN = %s OR DS_SENHA = %s', (DS_USUARIO, DS_SENHA), ) # VERIFICA SE O USUARIO EXISTE NO BANCO
            account = cursor.fetchone()

            # VERIFICA SE O USUARIO EXISTE NO BANCO
            if account:
                flash('Alguém está utilizando esse mesmo login ou senha!')
            # VERIFICA SE O CAMPO ESTÁ VAZIO
            if not DS_ORGANIZACAO or not DS_NOME or not DS_EMAIL or not DS_NUMERO_TEL or not DS_USUARIO or not DS_SENHA:
                flash('Por favor, preencha o formulário!', 'info')
            # VERIFICANDO SE O EMAIL É VALIDO
            elif not re.match(r'[^@]+@[^@]+\.[^@]+', DS_EMAIL):
                flash('E-mail inválido!', 'danger')
            # VERIFICANDO SE O TELEFONE É VALIDO
            elif not re.match(r'[0-9]{2}[0-9]{5}[0-9]{4}', DS_NUMERO_TEL):
                flash('Telefone inválido!')
            # VERIFICA SE O NOME DO USUARIO É VALIDO
            elif not re.match(r'[A-Za-z0-9]+', DS_USUARIO):
                flash('O nome de usuário deve conter apenas caracteres e números!', 'danger')
            
            else:
                cursor.callproc('sp_create_organizacao_and_user', (
                    0, DS_ORGANIZACAO, data, 1,0,
                    0, 'PW Grupo', data, 1, 0,
                    0, DS_NOME, DS_NUMERO_TEL, DS_EMAIL, DS_USUARIO, senha_criptografada, 1, 0, 1,
                    0, 0, 0, 0))
                mysql.connection.commit()
                flash('Organizacao criada com sucesso', 'success')

        elif request.method == 'POST':
            flash('Por favor, preencha o formulário!', 'danger')
        
        return render_template('register.html')

   


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
        if request.method == 'POST' and 'grupo' in request.form:
            DS_NOVO_GRUPO = request.form['grupo']
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM TB_GRUPO WHERE NOME_DO_GRUPO = %s', (DS_NOVO_GRUPO, ))
            grupo = cursor.fetchone()
            data = now.strftime('%Y-%m-%d %H:%M:%S')
                
            if grupo:
                flash('Já existe um grupo com o mesmo nome!', 'danger')
            else:
                cursor.callproc('sp_create_grupo', (0, DS_NOVO_GRUPO, data, 1, session['ID_ORGANIZACAO'], 0, 0, session['ID_USUARIO'], session['ID_ORGANIZACAO']))
                mysql.connection.commit()
                flash('Grupo criado com sucesso!', 'success')
            return redirect(url_for('home'))
        
        return render_template('home.html', list_grupos_usuario=list_grupo_usuario)
    else:
        return redirect(url_for('login'))



# EDITAR GRUPOS
@app.route('/powerhub/editar-grupo/<int:id>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def editar_grupo(id):
    if 'loggedin' in session:
        if request.method == 'GET':
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM TB_GRUPO WHERE ID_GRUPO = %s', (id, ))
            grupo = cursor.fetchone()
            cursor.close()
            return render_template('grupos/editar-grupo.html', grupo=grupo)
        if request.method == 'POST' and 'grupo' in request.form:
            DS_GRUPO = request.form['grupo']
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM TB_GRUPO WHERE NOME_DO_GRUPO = %s', (DS_GRUPO, ))
            grupo = cursor.fetchone()
            data = now.strftime('%Y-%m-%d %H:%M:%S')
            if grupo:
                flash('Já existe um grupo com o mesmo nome!', 'danger')
            else:
                cursor.execute('UPDATE TB_GRUPO SET NOME_DO_GRUPO = %s WHERE ID_GRUPO = %s', (DS_GRUPO, id))
                #cursor.callproc('sp_update_grupo', (id, DS_GRUPO, data, 1, session['ID_ORGANIZACAO'], 0, 0, session['ID_USUARIO'], session['ID_ORGANIZACAO']))
                mysql.connection.commit()
                flash('Grupo atualizado com sucesso!', 'success')
            return redirect(url_for('home'))
        
        elif request.method == 'put':
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM TB_GRUPO_USUARIO WHERE ID_GRUPO = %s', (id, ))
            grupo = cursor.fetchone()
            if grupo:
                flash('Não é possível excluir um grupo que possui um ou mais usuários!')
            return redirect(url_for('home'))
    else:
        return redirect(url_for('login'))

# DELETAR GRUPO
@app.route('/powerhub/deletar-grupo/<int:id>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def deletar_grupo(id):
    if 'loggedin' in session:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM TB_RELATORIO WHERE ID_GRUPO = %s', (id, ))
            grupo = cursor.fetchone()
            if grupo:
                flash('Não é possível excluir um grupo que possui um ou mais relatórios!', 'danger')
            
            else:
                cursor.execute('DELETE FROM TB_GRUPO_USUARIO WHERE ID_GRUPO = %s', (id, ),)
                cursor.execute('DELETE FROM TB_GRUPO WHERE ID_GRUPO = %s', (id, ))
                mysql.connection.commit()
                flash('Grupo excluído com sucesso!', 'success')
            return redirect(url_for('home'))
    else:
        return redirect(url_for('login'))
# LISTA RELATORIOS DO GRUPO
@app.route('/powerhub/listar_relatorios/<int:id_grupo>', methods=['GET', 'POST', 'DELETE'])
def listar_relatorios(id_grupo):
    if 'loggedin' in session:
        if request.method == 'GET':
            try:
                """""cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute('SELECT GPU.ID_GRUPO, GP.NOME_DO_GRUPO FROM TB_GRUPO_USUARIO GPU JOIN TB_GRUPO GP ON GPU.ID_GRUPO = GP.ID_GRUPO WHERE GPU.ID_GRUPO = %s', (id_grupo,))
                id_grupo_g = cursor.fetchall()
                cursor.close()"""""

                queryRelatorio = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                queryRelatorio.execute('SELECT DISTINCT RL.ID_RELATORIO, RL.ID_GRUPO,  RL.DS_NOME_RELATORIO FROM TB_RELATORIO RL JOIN TB_GRUPO_USUARIO GPU ON GPU.ID_GRUPO = RL.ID_GRUPO WHERE GPU.ID_GRUPO = %s', (id_grupo,))
                nome_relatorio = queryRelatorio.fetchall()
                queryRelatorio.close()

                return render_template('relatorio/listar_relatorios.html', NOME_RELATORIO_GRUPO=nome_relatorio)
            except:
                return render_template('error/error.html')        
        # INSERIR RELATORIO
        
        if request.method == 'POST' and 'nome_relatorio' in request.form and 'link_relatorio' in request.form:
            DS_NOME_RELATORIO = request.form['nome_relatorio']
            DS_LINK_RELATORIO = request.form['link_relatorio']
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM TB_RELATORIO WHERE DS_LINK_RELATORIO = %s', (DS_LINK_RELATORIO,))
            relatorio = cursor.fetchone()
            if relatorio:
                flash('Já existe um relatório com o mesmo link!', 'danger')
            else:
                cursor.callproc('sp_create_relatorio', (0, DS_NOME_RELATORIO, DS_LINK_RELATORIO, id_grupo))
                mysql.connection.commit()
                flash('Relatório criado com sucesso!', 'success')
            return redirect(url_for('listar_relatorios', id_grupo=id_grupo))
    
    else:
        return render_template('error/error.html')

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
            return render_template('error/error.html', visualizar_relatorio=visualizar_relatorio)
        return render_template('relatorio/visualizar_relatorio.html', visualizar_relatorio=visualizar_relatorio)
    return redirect(url_for('login'))

# deletar relatorio
@app.route('/powerhub/deletar_relatorio/<int:id_relatorio>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def deletar_relatorio(id_relatorio):
    if 'loggedin' in session:
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute('DELETE FROM TB_RELATORIO WHERE ID_RELATORIO = %s', (id_relatorio, ))
                mysql.connection.commit()
                flash('Relatório excluído com sucesso!', 'success')
                return redirect(url_for('home'))
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
            return render_template('usuario/usuarios.html', contas=account)
        except:
            return render_template('error   .html')
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
                    flash('Já existe uma conta com esse e-mail!', 'danger')
                elif not nome or not email or not senha or not confirmar_senha:
                    flash('Por favor, preencha todos os campos!', 'danger')
                elif senha != confirmar_senha:
                    flash('As senhas não conferem!', 'danger')
                else:
                    cursor.execute('INSERT INTO TB_USUARIO VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)', (0, nome, telefone, email, login, senha, 0, session['ID_ORGANIZACAO'], 0, ))
                    mysql.connection.commit()
                    flash('Conta criada com sucesso!', 'success')
                    return redirect(url_for('list_user'))            
            return render_template('usuario/criar_usuario.html')
        except:
            return render_template('error/error.html')

# EDITAR USUARIO
@app.route('/powerhub/editar_usuario/<int:id_usuario>', methods=['GET', 'POST'])
def editar_usuario(id_usuario):
    if 'loggedin' in session:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM TB_USUARIO WHERE ID_USUARIO = %s', (id_usuario,))
            account = cursor.fetchone()
            if request.method == 'POST' and 'nome' in request.form and 'login' in request.form and 'telefone' in request.form and 'email' in request.form and 'senha' in request.form and 'confirmar_senha' in request.form and 'FL_ADMINISTRADOR' in request.form:
                nome = request.form['nome']
                login = request.form['login']
                telefone = request.form['telefone']
                email = request.form['email']
                senha = request.form['senha']
                confirmar_senha = request.form['confirmar_senha']
                FL_ADMINISTRADOR = request.form.getlist('FL_ADMINISTRADOR')
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute('SELECT * FROM TB_USUARIO WHERE DS_EMAIL = %s', (email,))
                account = cursor.fetchone()
                if not nome or not email or not senha or not confirmar_senha:
                    flash('Por favor, preencha todos os campos!', 'danger')
                elif senha != confirmar_senha:
                    flash('As senhas não conferem!', 'danger')
                else:
                    cursor.execute('UPDATE TB_USUARIO SET NOME_USUARIO = %s, DS_TELEFONE = %s, DS_EMAIL = %s, DS_LOGIN = %s, DS_SENHA = %s, FL_ADMINISTRADOR = %s WHERE ID_USUARIO = %s', (nome, telefone, email, login, senha, id_usuario, FL_ADMINISTRADOR, ))
                    mysql.connection.commit()
                    flash('Conta atualizada com sucesso!', 'success')
                    return redirect(url_for('list_user'))
            return render_template('usuario/v_editar_usuario.html', account=account) 

# excluir usuario
@app.route('/powerhub/excluir_usuario/<int:id_usuario>', methods=['GET', 'POST'])
def excluir_usuario(id_usuario):
    if 'loggedin' in session:
        try:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM TB_GRUPO_USUARIO WHERE ID_USUARIO  = %s', (id_usuario,))
            account_us = cursor.fetchone()
            if account_us:
                flash('Este usuário está vinculado a grupos!', 'danger')

            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT US.* FROM TB_USUARIO US LEFT JOIN TB_GRUPO_USUARIO  GPU ON GPU.ID_USUARIO = US.ID_USUARIO WHERE us.ID_USUARIO  = %s', (id_usuario,))
            account = cursor.fetchone()
            if account['FL_PROPRIETARIO_CONTA'] == 1:
                flash('Este usuário é o proprietário da conta. Não pode ser excluído!', 'danger')
            
            else:
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute('DELETE FROM TB_USUARIO WHERE ID_USUARIO = %s', (id_usuario,))
                mysql.connection.commit()
                flash('Conta excluída com sucesso!', 'success')
            return redirect(url_for('list_user'))
        except:
            return redirect(url_for('list_user'))

#  LISTAR GRUPOS ERROR
@app.route('/powerhub/grupos')
def Grupos():
    if 'loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT DISTINCT GP.NOME_DO_GRUPO, GP.ID_GRUPO FROM TB_GRUPO_USUARIO GPU JOIN TB_GRUPO GP ON GPU.ID_GRUPO = GP.ID_GRUPO WHERE GPU.ID_ORGANIZACAO = (%s)', (session['ID_ORGANIZACAO'],))
        grupos = cursor.fetchall()
        cursor.close()
        return render_template('grupos/v_grupos.html', grupos=grupos) 
        
# VINCULAR USUARIO AO GRUPO
@app.route('/powerhub/vincular_usuario/<int:id_grupo>', methods=['GET', 'POST'])
def vincular_usuario(id_grupo):
    if 'loggedin' in session:
            if request.method == 'GET':
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute('SELECT DISTINCT * FROM TB_USUARIO US JOIN TB_GRUPO_USUARIO GPU ON US.ID_USUARIO = GPU.ID_USUARIO JOIN TB_GRUPO GP ON GP.ID_GRUPO = GPU.ID_GRUPO  WHERE GPU.ID_GRUPO = (%s)', (id_grupo,))
                usuarios = cursor.fetchall()
                cursor.close()
                
                # TODOS OS USUARIOS
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute('SELECT * FROM TB_USUARIO WHERE ID_USUARIO  NOT IN (SELECT ID_USUARIO FROM TB_GRUPO_USUARIO WHERE ID_GRUPO = (%s) ) AND ID_ORGANIZACAO = (%s)', (id_grupo, session['ID_ORGANIZACAO'],))
                usuarios_nao_vinculados = cursor.fetchall()
                cursor.close()
            
            return render_template('grupos/v_vincular_usr_grupo.html', usuarios=usuarios, usuarios_nao_vinculados=usuarios_nao_vinculados)

# vincular usuario ao grupo
@app.route('/powerhub/vincular_usuarios/<int:id_grupo>/<int:id_usuario>', methods=['POST'])
def vincular_usuarios(id_grupo, id_usuario):
    if 'loggedin' in session:
            if request.method == 'POST':
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute('INSERT INTO TB_GRUPO_USUARIO VALUES(%s, %s, %s, %s)', (0, id_grupo, id_usuario, session['ID_ORGANIZACAO'],))
                mysql.connection.commit()
                cursor.close()
                flash('Usuário vinculado com sucesso!', 'success')
                return redirect(url_for('vincular_usuario', id_grupo=id_grupo))


# DESVINCULAR USUARIO DO GRUPO
@app.route('/powerhub/desvincular_usuario/<int:id_grupo>/<int:id_usuario>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def desvincular_usuario(id_grupo, id_usuario):
    if 'loggedin' in session:
                
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute('SELECT COUNT(*) AS CTG_USUARIOS FROM TB_USUARIO US JOIN TB_GRUPO_USUARIO GPU ON US.ID_USUARIO = GPU.ID_USUARIO JOIN TB_GRUPO GP ON GP.ID_GRUPO = GPU.ID_GRUPO  WHERE GPU.ID_GRUPO = (%s)', (id_grupo,))
                usuarios = cursor.fetchone()
                cursor.close()

                if usuarios['CTG_USUARIOS'] > 1:
                    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                    cursor.execute('DELETE FROM TB_GRUPO_USUARIO WHERE ID_GRUPO = (%s) AND ID_USUARIO = (%s)', (id_grupo, id_usuario,))
                    mysql.connection.commit()
                    cursor.close()
                    flash('Usuário desvinculado com sucesso!', 'success')
                else:
                    flash('Não é possível desvincular o último usuário do grupo!', 'danger')
            
                return redirect(url_for('vincular_usuario', id_grupo=id_grupo))


# configurações
@app.route('/powerhub/configuracoes', methods=['GET','POST'])
def Configuracoes():
    if 'loggedin' in session:
        if request.method == 'GET':
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT ORG.*, US.DS_EMAIL, US.DS_TELEFONE FROM TB_ORGANIZACAO ORG JOIN TB_USUARIO US ON US.ID_ORGANIZACAO = ORG.ID_ORGANIZACAO WHERE ORG.ID_ORGANIZACAO = %s AND US.FL_PROPRIETARIO_CONTA = 1', (session['ID_ORGANIZACAO'], ))
            organizacao = cursor.fetchall()
            print(organizacao)
            cursor.close()

        return render_template('/config/v_configuracoes.html', organizacao = organizacao)

# checkout
@app.route('/powerhub/checkout')
def pagamento():
    if 'loggedin' in session:
        # carregar dados da organizacao
        
        return render_template('premium/v_checkout.html')

