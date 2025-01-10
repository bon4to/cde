class cde:
    @staticmethod
    # função para salvar logs em um arquivo com nome de data
    def save_log(log_message):
        # nome do arquivo de log com a data atual
        user_id = session.get('id_user', 'unknown')
        log_file_name = datetime.now().strftime('%Y-%m-%d') + f'-u{user_id}' + '.log'
        log_file_path = os.path.join(dirs.get('logs_dir'), log_file_name)
        try:
            with open(log_file_path, 'a') as log_file:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # se o log_message for uma lista ou dicionário, converte para JSON
                if isinstance(log_message, (list, dict)):
                    log_message = json.dumps(log_message, ensure_ascii=False)
                
                log_file.write(f'[{timestamp}] {log_message}\n')
                return True
        except Exception as e:
            return False


    @staticmethod
    # logs no modo debug
    def debug_log(text):
        if debug == True:
            print(f'[DEBUG] {text}')
        else:
            pass
    
    
    @staticmethod
    # retorna o valor da chave "dsn > cargas" do arquivo "default.txt"
    def get_unit():
        file_path = "userdata/default.txt"
        try:
            # abre e lê o conteúdo do arquivo
            with open(file_path, 'r') as file:
                content = file.read()

            # converte o conteúdo do arquivo para um objeto Python
            data = json.loads(content)

            # extrai o valor desejado
            return data["dsn"]["cargas"]
        except FileNotFoundError:
            print("Erro: Arquivo não encontrado.")
        except KeyError:
            print("Erro: Chave 'dsn > cargas' não encontrada.")
        except json.JSONDecodeError:
            print("Erro: Conteúdo do arquivo não é um JSON válido.")
        # default
        print('Retornando HUGOPIET')
        return 'HUGOPIET'
    
    
    @staticmethod
    # conexão e consulta no banco de dados
    def db_query(query, dsn):
        # TODO: criar api para consultar nas dsns (micro-services)
        # TODO: criar métodos de mesclar consultas (ex: dadosNOE + dadosHP)
        if dsn == 'HUGOPIET':
            uid_pwd = os.getenv('DB_USER').split(';')
            user = uid_pwd[0]
            password = uid_pwd[1]
            try:
                connection = pyodbc.connect(f"DSN={dsn}", uid=user, pwd=password)
                cursor = connection.cursor()
                cursor.execute(query)
                columns = [str(column[0]) for column in cursor.description]
                result = cursor.fetchall()

                cursor.close()
                connection.close()
            except Exception as e:
                print("Erro ao enviar solicitação:", str(e))
                result = [[f'Erro de consulta: {e}']]
                columns = []
        elif dsn == "NOE":
            url, headers = cde.new_api_connection()
            data = {"query": query}
            try:
                response = requests.post(url, headers=headers, json=data)
                if response.status_code == 200:
                    response_data = response.json()
                    result = response_data.get("data", [])
                    
                    # retorno tabulado
                    if isinstance(result, str):
                        lines = result.strip().split("\n")
                        header = lines[0].split("\t")
                        rows = [line.split("\t") for line in lines[1:]]
                        return rows, header
                    
                    # retorno JSON
                    columns = list(result[0].keys()) if result else []
                    rows = [list(item.values()) for item in result]
                    return rows, columns
                else:
                    print(f"Erro na API: {response.status_code} - {response.text}")
                    return [[f"Erro: {response.text}"]], []
            except requests.exceptions.ConnectionError as e:
                print("API offline ou inacessível:", str(e))
                return [[f"Erro: A API está offline ou inacessível no momento. Consulte o suporte."]], []
            except Exception as e:
                print("Erro de conexão com a API:", str(e))
                return [[f"Erro: {str(e)}"]], []
        elif dsn == 'SQLITE':
            try:
                with sqlite3.connect(db_path) as connection:
                    cursor = connection.cursor()
                    cursor.execute(query)
                    columns = [str(column[0]) for column in cursor.description]
                    result = cursor.fetchall()
            except Exception as e:
                print("Erro ao enviar solicitação:", str(e))
                result = [[f'Erro de consulta: {e}']]
                columns = []

        else:
            result = [[f'DSN INVÁLIDA: {dsn}']]
            columns = []
            
        return result, columns
    
    
    @staticmethod
    def new_api_connection():
        noe_api = os.getenv('NOE_API')
        url = f"http://{noe_api}/query"
        headers = {"Content-Type": "application/json"}
        
        return url, headers
    
    
    @staticmethod
    # consulta tabelas do schema
    def db_get_tables(dsn):
        try:
            if dsn == 'HUGOPIET':
                query = '''
                    SELECT TABNAME
                    FROM SYSCAT.TABAUTH
                    WHERE GRANTEE = 'CDEADMIN'
                    AND SELECTAUTH = 'Y';
                '''
            elif dsn == 'SQLITE':
                query = '''
                    SELECT name 
                    FROM sqlite_master 
                    WHERE type = 'table' 
                        AND name NOT LIKE 'sqlite_%'
                    ORDER BY name;
                '''
            else:
                return [[f'DSN desconhecida: {dsn}']]
            
        except Exception as e:
            return [[f'Erro de consulta: {e}']]
        
        return cde.db_query(query, dsn)[0]
    
    
    @staticmethod
    def create_default_user():
        data_cadastro  = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            cursor.execute('''
                INSERT INTO users (
                    login_user, password_user, 
                    nome_user, sobrenome_user, 
                    privilege_user, data_cadastro 
                ) VALUES (
                    "DEFAULT", "12345", "USER",
                    "DEFAULT", 1, ? 
                );
            ''',(data_cadastro,))
        return
    
    
    @staticmethod
    # VERIFICA PRIVILÉGIO DE ACESSO
    def verify_auth(id_page):
        def decorator(f):
            @wraps(f)
            def decorador(*args, **kwargs):
                if not 'logged_in' in session:
                    return redirect(url_for('login'))
                id_user = session.get('id_user')
                session['id_page'] = f'{id_page}'
                if session.get('user_grant') <= 2:
                    log(TAGS.SERVER, TAGS.GRANTED, f'{id_user} - {id_page} ({inject_page()["current_page"]})')
                    app.config['APP_UNIT'] = cde.get_unit()
                    return f(*args, **kwargs)
                user_perm = UserUtils.get_user_permissions(id_user)
                user_perm = [item['id_perm'] for item in user_perm]
                if id_page in user_perm:
                    log(TAGS.SERVER, TAGS.GRANTED, f'{id_user} - {id_page} ({inject_page()["current_page"]})')
                    app.config['APP_UNIT'] = cde.get_unit()
                    return f(*args, **kwargs)
                log(TAGS.SERVER, TAGS.DENIED, f'{id_user} - {id_page} ({inject_page()["current_page"]})')
                return render_template(
                    'components/menus/alert.html', 
                    alert_type='SEM PERMISSÕES',
                    alert_msge='Você não tem permissão para acessar esta página.', 
                    alert_more='SOLUÇÕES:\n• Solicite ao seu supervisor um novo nível de acesso.',
                    url_return=url_for('index')
                )
            return decorador
        return decorator
    
    
    @staticmethod
    # method to split codes from their sequences
    def split_code_seq(code):
        if '-' in code:
            code, seq = code.split('-')
            return code, seq
        seq = '0'
        return code, seq
