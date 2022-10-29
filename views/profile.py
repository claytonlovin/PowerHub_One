

@app.route('/powerhub/profile')
def Usuarios():
    if 'loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT US.NOME_USUARIO, US.DS_LOGIN, US.DS_TELEFONE, US.DS_EMAIL, US.FL_ADMINISTRADOR, GP.NOME_DO_GRUPO  FROM TB_ORGANIZACAO ORG JOIN TB_GRUPO GP  ON GP.ID_ORGANIZACAO = ORG.ID_ORGANIZACAO JOIN TB_GRUPO_USUARIO GPU ON GPU.ID_ORGANIZACAO = ORG.ID_ORGANIZACAO JOIN TB_USUARIO US ON US.ID_USUARIO = GPU.ID_USUARIO WHERE ORG.ID_ORGANIZACAO = %s', (session['ID_ORGANIZACAO'], ))
        account = cursor.fetchone()
        cursor.close()
        print(account)
        return render_template('usuarios.html', contas=account)
    return redirect(url_for('login'))
