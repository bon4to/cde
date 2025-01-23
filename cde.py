import textwrap
import requests
import sqlite3
import random
import qrcode
import pyodbc
import base64
import json
import sys
import io
import re
import os

from flask import Flask, Response, request, redirect, render_template, url_for, jsonify, session, abort
from datetime import datetime, timezone, timedelta
from PIL import Image, ImageDraw, ImageFont
from passlib.hash import pbkdf2_sha256
from dotenv import load_dotenv
from functools import wraps
from math import pi, ceil

from werkzeug.wrappers.response import Response


if __name__:
    # carrega o .env
    load_dotenv()
    
    # define app
    app = Flask(__name__)
    
    # parâmetros
    app.secret_key = os.getenv('SECRET_KEY')
    app.config['CDE_SESSION_LIFETIME'] = timedelta(minutes=90)
    app.config['APP_VERSION'] = ['0.5.2', 'Janeiro/2025', False] # 'versão', 'release-date', 'debug-mode'
    app.config['APP_UNIT'] = '' # preset default
    
    current_dir = os.path.dirname(os.path.abspath(__file__)).upper() # current absolute directory
    debug_dir   = os.getenv('DEBUG_DIR').upper().split(';')          # debug directory (evita execução sem configurar diretório)
    default_dir = os.getenv('DEFAULT_DIR').upper()                   # default dir (executa somente no diretório de produção)


    class TAGS:
        SERVER  = '[CDE]'
        INFO    = '[INFO]'
        ERROR   = '[ERROR]'
        STATUS  = '[STATUS]'
        DENIED  = '403'
        GRANTED = '200'


    def log(tag_1, tag_2, text) -> None:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if not tag_2:
            print(f'{tag_1} {text}')
            return
        print(f'{tag_1} ({timestamp}) {tag_2} | {text}')
        return

    dirs = {}
    def create_dirs() -> None:
        dirs = {
            'db_dir'     : os.path.join(os.getcwd(), 'db'),
            'app_dir'    : os.path.join(os.getcwd(), 'app'),
            'a_rout_dir' : os.path.join(os.getcwd(), 'app/routes'),
            'a_mod_dir'  : os.path.join(os.getcwd(), 'app/models'),
            'a_serv_dir' : os.path.join(os.getcwd(), 'app/services'),
            'a_util_dir' : os.path.join(os.getcwd(), 'app/utils'),
            'tests_dir'  : os.path.join(os.getcwd(), 'tests'),
            'logs_dir'   : os.path.join(os.getcwd(), 'logs'),
            'r_dir'      : os.path.join(os.getcwd(), 'report'),
            'r_car_dir'  : os.path.join(os.getcwd(), 'report/cargas'),
            'r_pcar_dir' : os.path.join(os.getcwd(), 'report/cargas_preset'),
            'r_req_dir'  : os.path.join(os.getcwd(), 'report/requests'),
            'r_preq_dir' : os.path.join(os.getcwd(), 'report/requests_preset'),
            'r_pest_dir' : os.path.join(os.getcwd(), 'report/estoque_preset'),
            'userdt_dir' : os.path.join(os.getcwd(), 'userdata'),
        }
        
        total_dirs = len(dirs)
        
        # cria os diretórios (se não existirem)
        for i, dir_path in enumerate(dirs.values(), start=1):
            os.makedirs(dir_path, exist_ok=True)
            log(
                TAGS.SERVER,
                None,
                text=f'Verificando integridade dos diretórios... [{i}/{total_dirs}]'
            )
        log(
            TAGS.SERVER,
            None,
            text=f'Vefificação finalizada. Inicializando...'
        )

    create_dirs()

    # logs de execução
    exec_head   = \
f'''

          CCCCCCCCCCCCCCC   DDDDDDDDDDDDDDD           EEEEEEEEEEEEEEEEEEEEEE
       CCC::::::::::::::C   D::::::::::::::DDD        E::::::::::::::::::::E
     CC:::::::::::::::::C   D:::::::::::::::::DD      E::::::::::::::::::::E
    C::::::CCCCCCCCCCCCCC   DDDDDDDDDDDDDD::::::D     EEEEEEEEEEEEEEEEEEEEEE
   C:::::CC                               DD:::::D                          
  C:::::C                                   D:::::D                         
  C:::::C                                   D:::::D   EEEEEEEEEEEEEEEEEEEE  
  C:::::C                                   D:::::D   E::::::::::::::::::E  
  C:::::C                                   D:::::D   EEEEEEEEEEEEEEEEEEEE  
  C:::::C                                   D:::::D                         
   C:::::CC                               DD:::::D                          
    C::::::CCCCCCCCCCCCCC   DDDDDDDDDDDDDD::::::D     EEEEEEEEEEEEEEEEEEEEEE
     CC:::::::::::::::::C   D:::::::::::::::::DD      E::::::::::::::::::::E
       CCC::::::::::::::C   D::::::::::::::DDD        E::::::::::::::::::::E
          CCCCCCCCCCCCCCC   DDDDDDDDDDDDDDD           EEEEEEEEEEEEEEEEEEEEEE


'''
    start_head  = \
f'''
{TAGS.INFO} CDE Version: {app.config['APP_VERSION'][0]} (beta) - {app.config['APP_VERSION'][1]}
{TAGS.INFO} Python Version: {sys.version}
{TAGS.STATUS} Starting in: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
'''
    error_foot  = \
f'''
{TAGS.ERROR} 
* Impossível executar, verifique se o arquivo está alocado corretamente.

Pressione ENTER para sair...
'''


    if current_dir in debug_dir: # se o diretório atende ao local 'debug', modo_exec = 'debug'
        db_path = os.getenv('DEBUG_DB_PATH')
        port, debug = 5100, True
        app.config['APP_VERSION'][2] = True

        # logs server running info
        print(start_head) 

    elif default_dir in current_dir: # se o diretório atende ao local 'produção', modo_exec = 'produção'.
        db_path = os.getenv('DB_PATH')
        port, debug = 5005, False
        
        # logs header & server running info
        print(exec_head, start_head) 

    else: # se o diretório não corresponde aos listados, não executa.
        print(error_foot)
        sys.exit(2)



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
    # retorna texto do arquivo
    def get_file_text(dir) -> str:
        try:
            with open(dir, 'r') as file:
                return file.read().strip()
        except Exception as e:
            print(e)
            return ''


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
    # GERADOR DE TABELAS
    def create_tables() -> None:
        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()

            # TABELA DE PROGRAMAÇÃO DO ENVASE
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS prog_envase (
                    id_envase       INTEGER PRIMARY KEY AUTOINCREMENT,
                    cod_linha       INTEGER(3),
                    cod_cliente     INTEGER(10),
                    cod_item        VARCHAR(6),
                    qtde_solic      INTEGER(20),
                    data_entr_antec DATETIME,
                    data_envase     DATETIME,
                    observacao      VARCHAR(100),
                    flag_concluido  BOOLEAN DEFAULT FALSE
                );
            ''')

            # TABELA DE PROGRAMAÇÃO DA PROCESSAMENTO
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS prog_producao (
                    id_producao     INTEGER PRIMARY KEY AUTOINCREMENT,
                    cod_linha       INTEGER(3),
                    liq_tipo        VARCHAR(10),
                    liq_linha       VARCHAR(30),
                    liq_cor         VARCHAR(30),
                    embalagem       VARCHAR(10),
                    lts_solic       INTEGER(20),
                    data_entr_antec DATETIME,
                    data_producao   DATETIME,
                    observacao      VARCHAR(100),
                    flag_concluido  BOOLEAN DEFAULT FALSE
                );
            ''')

            # TABELA HISTÓRICO
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tbl_transactions (
                    id_mov     INTEGER PRIMARY KEY AUTOINCREMENT,
                    rua_letra  VARCHAR(10),
                    rua_numero INTEGER(6),
                    cod_item   VARCHAR(100),
                    lote_item  VARCHAR(8),
                    quantidade INTEGER,
                    operacao   VARCHAR(15),
                    id_carga   INTEGER(6),
                    id_request INTEGER(6), 
                    id_user    INTEGER,
                    time_mov   DATETIME
                );
            ''')
            
            # TABELA DE CLIENTES
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS clientes (
                    cod_cliente      INTEGER(10) PRIMARY KEY,
                    razao_cliente    VARCHAR(100),
                    fantasia_cliente VARCHAR(100),
                    cidade_cliente   VARCHAR(100),
                    estado_cliente   VARCHAR(30)
                );
            ''')
            
            # TABELA DE CARGAS PENDENTES
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tbl_carga_incomp (
                    id_log        INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_carga      INTEGER(6),
                    cod_item      VARCHAR(6),
                    qtde_atual    INTEGER(20),
                    qtde_solic    INTEGER(20),
                    flag_pendente BOOLEAN DEFAULT TRUE
                );
            ''')

            # TABELA DE USUÁRIOS
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id_user        INTEGER PRIMARY KEY AUTOINCREMENT,
                    login_user     VARCHAR(30) UNIQUE,
                    password_user  TEXT,
                    nome_user      VARCHAR(100),
                    sobrenome_user VARCHAR(100),
                    privilege_user INTEGER(2),
                    data_cadastro  DATETIME,
                    ult_acesso     DATETIME
                );
            ''')

            # TABELA DE PERMISSÕES DE USUÁRIO
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_permissions (
                    id_user INTEGER, 
                    id_perm VARCHAR(6)
                );
            ''')

            # TABELA DE ITENS
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS itens (
                    cod_item   VARCHAR(6) PRIMARY KEY,
                    desc_item  VARCHAR(100),
                    dun14      INTEGER(14),
                    flag_ativo BOOLEAN DEFAULT TRUE
                );
            ''')

            # TABELA AUXILIAR DE PRIVILÉGIOS
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS aux_privilege (
                    id_priv   INTEGER(2) PRIMARY KEY,
                    desc_priv VARCHAR(30) UNIQUE
                );
            ''')

            # TABELA AUXILIAR DE PERMISSÕES
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS aux_permissions (
                    id_perm   VARCHAR(6) PRIMARY KEY,
                    desc_perm VARCHAR(100)
                );
            ''')
            
            # TABELA AUXILIAR DE LINHAS
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS aux_linha (
                    cod_linha  INTEGER(3),
                    tipo_embal VARCHAR(10),
                    lit_embal  VARCHAR(10)
                );
            ''')

            connection.commit()
        return None

    
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


class EstoqueUtils:
    # DEFINE A QUERY SQL DE SALDO
    sql_balance_calc = '''
        SUM( 
            CASE 
            WHEN operacao = 'E' OR operacao = 'TE' 
            THEN quantidade 
            
            WHEN operacao = 'S' OR operacao = 'TS' OR operacao = 'F' 
            THEN (quantidade * -1)
            
            ELSE (quantidade * 0)
            END
        )
    '''
    
    @staticmethod
    # retorna saldo do item
    def estoque_address_with_item(cod_item=False):
        if cod_item:
            sql_balance_calc = EstoqueUtils.sql_balance_calc
            query = '''
                SELECT  
                    h.rua_numero, h.rua_letra, i.cod_item, 
                    i.desc_item, h.lote_item,
                    {a} as saldo
                FROM tbl_transactions h

                JOIN itens i 
                ON h.cod_item = i.cod_item

                WHERE i.cod_item = "{b}"
                
                GROUP BY  
                    h.rua_numero, h.rua_letra, 
                    h.cod_item, h.lote_item
                HAVING saldo != 0

                ORDER BY 
                    h.lote_item ASC, h.rua_letra ASC,
                    h.rua_numero ASC, i.desc_item ASC;
            '''.format(a=sql_balance_calc, b=str(cod_item))
            dsn = 'SQLITE'
            result_local, columns_local = cde.db_query(query, dsn)
            return result_local, columns_local
        else:
            return [], []


    @staticmethod
    # RETORNA TABELA DE SALDO
    def get_saldo_view(timestamp=False):
        if timestamp:
            timestamp = misc.add_days_to_datetime_str(timestamp, 1)
        timestamp = misc.parse_db_datetime(timestamp)
        
        sql_balance_calc = EstoqueUtils.sql_balance_calc
        
        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            cursor.execute('''
                SELECT 
                    i.cod_item, i.desc_item, 
                    COALESCE(t.saldo, 0) as saldo,
                    COALESCE(t.time_mov, "-") as time_mov
                FROM itens i
                
                LEFT JOIN (
                    SELECT 
                        cod_item, {a} as saldo,
                        MAX(time_mov) as time_mov,
                        ROW_NUMBER() OVER(
                            PARTITION BY cod_item 
                            ORDER BY MAX(time_mov) DESC
                        ) as rn
                    FROM tbl_transactions h
                    WHERE time_mov <= ?
                    GROUP BY cod_item
                ) t ON i.cod_item = t.cod_item
                
                WHERE 
                    t.rn = 1 OR 
                    t.rn IS NULL
                ORDER BY t.time_mov DESC;
            '''.format(a=sql_balance_calc), (timestamp,))

            result = [{
                'cod_item': row[0], 'desc_item': row[1], 
                'saldo'   : row[2], 'ult_mov'  : row[3]
            } for row in cursor.fetchall()]

        return result

    
    @staticmethod
    # BUSCA SALDO COM UM FILTRO (PRESET)
    def get_saldo_preset(index, timestamp=False):
        itens = EstoqueUtils.get_preset_itens(index)
        
        if not itens:
            return []
        
        if timestamp:
            timestamp = misc.add_days_to_datetime_str(timestamp, 1)
        timestamp = misc.parse_db_datetime(timestamp)
        
        # prepara uma string sql (ex.: ?, ?, ?...)
        # e coloca na query
        placeholders = ','.join(['?'] * len(itens))
        
        sql_balance_calc = EstoqueUtils.sql_balance_calc
        
        query = '''
            SELECT 
                i.cod_item, i.desc_item,
                COALESCE(t.saldo, 0) as saldo
            FROM itens i
            
            LEFT JOIN (
                SELECT 
                    cod_item, {a} as saldo,
                    MAX(time_mov) as time_mov,
                    ROW_NUMBER() OVER(
                        PARTITION BY cod_item 
                        ORDER BY MAX(time_mov) DESC
                    ) as rn
                FROM tbl_transactions h
                WHERE time_mov <= ?
                GROUP BY cod_item
            ) t ON i.cod_item = t.cod_item
            
            WHERE i.cod_item IN ({b})
            ORDER BY i.cod_item;
        '''.format(a=sql_balance_calc, b=placeholders)

        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            # executa a query, 
            # passando o timestamp e os itens p/ os placeholders
            cursor.execute(query, (timestamp, *itens))
        
            result = [{
                'cod_item': row[0], 'desc_item': row[1], 
                'saldo'   : row[2]
            } for row in cursor.fetchall()]
        return result

    
    @staticmethod
    # BUSCA ITENS DE PRESETS
    def get_preset_itens(index):
        try:
            with open(
                f'report/estoque_preset/filtro_{index}.txt', 'r', encoding='utf-8'
            ) as file:
                itens = file.read().strip().split(', ')
        except:
            itens = []
        return itens


    @staticmethod
    # RETORNA ENDEREÇAMENTO POR LOTES
    def get_address_lote(timestamp=False):
        if timestamp:
            timestamp = misc.add_days_to_datetime_str(timestamp, 1)
        timestamp = misc.parse_db_datetime(timestamp)
        
        sql_balance_calc = EstoqueUtils.sql_balance_calc
        
        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            cursor.execute('''
                SELECT  
                    h.rua_letra, h.rua_numero, 
                    i.cod_item, i.desc_item, h.lote_item,
                    {a} as saldo
                FROM tbl_transactions h
                
                JOIN itens i 
                ON h.cod_item = i.cod_item
                
                WHERE h.time_mov <= ?
                GROUP BY 
                    h.rua_numero, h.rua_letra, 
                    h.cod_item, h.lote_item
                    
                HAVING saldo != 0
                ORDER BY 
                    h.rua_letra ASC, h.rua_numero ASC,
                    i.desc_item ASC
                ;'''.format(a=sql_balance_calc),(timestamp,)
            )

            result = [{
                'letra'   : row[0], 'numero'   : row[1], 
                'cod_item': row[2], 'desc_item': row[3], 'cod_lote': row[4], 
                'saldo'   : row[5]
            } for row in cursor.fetchall()]
        return result


    @staticmethod
    # RETORNA ENDEREÇAMENTO DE FATURADOS POR LOTES
    def get_address_lote_fat():
        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            cursor.execute('''
                SELECT  
                    h.rua_numero, h.rua_letra, i.cod_item,
                    i.desc_item, h.lote_item, h.id_carga, 
                    h.id_request, h.quantidade, h.time_mov
                FROM tbl_transactions h
                
                JOIN itens i 
                ON h.cod_item = i.cod_item
                
                WHERE 
                    (h.operacao = 'S' AND (h.id_request != 0 OR h.id_request IS NULL)) 
                    OR
                    (h.operacao = 'F' AND (h.id_carga != 0 OR h.id_carga IS NULL))
                
                ORDER BY 
                    h.time_mov DESC, h.id_carga DESC,
                    h.id_request DESC, h.cod_item ASC;
            ''')

            result = [{
                'numero'   : row[0], 'letra'   : row[1], 'cod_item': row[2],
                'desc_item': row[3], 'cod_lote': row[4], 'saldo'   : row[7],
                'id_carga' : row[5], 'id_req'  : row[6], 'time_mov': row[8]
            } for row in cursor.fetchall()]
        return result


    @staticmethod
    # RETORNA SALDO DO ITEM NO ENDEREÇO FORNECIDO
    def get_saldo_item(rua_numero, rua_letra, cod_item, cod_lote):
        sql_balance_calc = EstoqueUtils.sql_balance_calc
        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            cursor.execute('''
                SELECT 
                    COALESCE({a}, 0) as saldo
                FROM tbl_transactions h
                WHERE 
                    rua_numero = ? AND
                    rua_letra = ? AND
                    cod_item = ? AND
                    lote_item = ?;
            '''.format(a=sql_balance_calc), (rua_numero, rua_letra, cod_item, cod_lote))
            saldo_item = cursor.fetchone()[0]
        return saldo_item


class CargaUtils:
    @staticmethod
    # retorna as cargas,
    # exceto cargas faturadas
    def get_cargas(all_cargas=False, dsn='HUGOPIET'):
        if all_cargas:

            # define o dsn conforme default (ou usuario)
            dsn = cde.get_unit()
            print('DSN: ' + dsn)
            
            if dsn == 'HUGOPIET':
                cargas_except_query = ', '.join(map(str, all_cargas))
                
                query = '''
                    SELECT DISTINCT 
                        icrg.CODIGO_GRUPOPED AS NRO_CARGA,
                        icrg.NRO_PEDIDO      AS NRO_PEDIDO,
                        ped.CODIGO_CLIENTE   AS COD_CLIENTE,
                        cl.FANTASIA          AS FANT_CLIENTE,
                        crg.DATA_EMISSAO     AS DT_EMISSAO,
                        iped.DT_ENTREGA      AS DT_ENTREGA, 
                        crg.OBSERVACAO       AS OBS_CARGA

                    FROM DB2ADMIN.ITEMPED iped

                    JOIN DB2ADMIN.IGRUPOPE icrg
                    ON icrg.NRO_PEDIDO = iped.NRO_PEDIDO
                    AND icrg.SEQ = iped.SEQ

                    JOIN DB2ADMIN.PEDIDO ped
                    ON icrg.NRO_PEDIDO = ped.NRO_PEDIDO
                    
                    JOIN DB2ADMIN.GRUPOPED crg
                    ON icrg.CODIGO_GRUPOPED = crg.CODIGO_GRUPOPED

                    JOIN DB2ADMIN.CLIENTE cl
                    ON cl.CODIGO_CLIENTE = ped.CODIGO_CLIENTE

                    JOIN DB2ADMIN.HUGO_PIETRO_VIEW_ITEM i 
                    ON i.ITEM = iped.ITEM

                    WHERE icrg.QTDE_FATUR != 0
                    -- AND icrg.CODIGO_GRUPOPED NOT IN ({a})

                    ORDER BY icrg.CODIGO_GRUPOPED DESC, crg.DATA_EMISSAO DESC;
                '''.format(a=cargas_except_query)
            elif dsn == 'CDE_NOE':
                cargas_except_query = ', '.join(map(str, all_cargas))

                query = '''
                    SELECT DISTINCT 
                        icrg.CODIGO_GRUPOPED AS NRO_CARGA,
                        icrg.NRO_PEDIDO      AS NRO_PEDIDO,
                        ped.CODIGO_CLIENTE   AS COD_CLIENTE,
                        cl.FANTASIA          AS FANT_CLIENTE,
                        crg.DATA_EMISSAO     AS DT_EMISSAO,
                        iped.DT_ENTREGA      AS DT_ENTREGA, 
                        crg.OBSERVACAO       AS OBS_CARGA

                    FROM DB2ADMIN.ITEMPED iped

                    JOIN DB2ADMIN.IGRUPOPE icrg
                    ON icrg.NRO_PEDIDO = iped.NRO_PEDIDO
                    AND icrg.SEQ = iped.SEQ

                    JOIN DB2ADMIN.PEDIDO ped
                    ON icrg.NRO_PEDIDO = ped.NRO_PEDIDO
                    
                    JOIN DB2ADMIN.GRUPOPED crg
                    ON icrg.CODIGO_GRUPOPED = crg.CODIGO_GRUPOPED

                    JOIN DB2ADMIN.CLIENTE cl
                    ON cl.CODIGO_CLIENTE = ped.CODIGO_CLIENTE

                    JOIN DB2ADMIN.HUGO_PIETRO_VIEW_ITEM i 
                    ON i.ITEM = iped.ITEM

                    WHERE icrg.QTDE_FATUR != 0

                    ORDER BY icrg.CODIGO_GRUPOPED DESC, crg.DATA_EMISSAO DESC;
                '''
        else:
            query = '''SELECT 'SEM CARGAS' AS MSG;'''
        
        result, columns = cde.db_query(query, dsn)
        return result, columns

    
    @staticmethod
    # retorna a carga que já foi concluída
    # (presente no historico)
    def get_carga_from_hist(id_carga) -> list:
        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            cursor.execute('''
                SELECT cod_item, count(*)
                FROM tbl_transactions
                WHERE id_carga = ?;
                ''',
                (id_carga,)
            )
            result = cursor.fetchall() 
        return result


    @staticmethod
    # lê o arquivo json no servidor local
    # e retorna a lista da carga
    def readJsonCargaSeq(filename, seq=False):
        base_path = os.path.join(app.root_path, 'report/cargas')
        seq = int(seq)
        
        num_files = 0
        while True:
            file_path = os.path.join(base_path, f'{filename}.json')
            if num_files > 0:
                file_path = os.path.join(base_path, f'{filename}-{num_files}.json')
            if not os.path.exists(file_path):
                break
            num_files += 1
        
        if not seq:
            # 1234.json
            # Unifica todos os arquivos JSON com a mesma base de nome
            unified_data = []
            seq = 0
            while True:
                file_path = os.path.join(base_path, f'{filename}.json')
                if seq > 0:  
                    file_path = os.path.join(base_path, f'{filename}-{seq}.json')
                
                if not os.path.exists(file_path):
                    break
                with open(file_path, 'r') as file:
                    data = json.load(file)
                    unified_data.extend(data)
                seq += 1
            if unified_data:
                return unified_data, num_files
            else:
                return None, num_files
        else:
            # 1234-1.json
            # Lê o arquivo JSON específico com a sequência fornecida
            file_path = os.path.join(base_path, f'{filename}.json')
            if seq > 0:  
                file_path = os.path.join(base_path, f'{filename}-{seq}.json')
            
            if os.path.exists(file_path):
                with open(file_path, 'r') as file:
                    return json.load(file), num_files
            else:
                return None, num_files


    @staticmethod
    # INSERE REGISTRO NA TABELA DE CARGAS PENDENTES
    def insert_carga_incomp(id_carga, cod_item, qtde_atual, qtde_solic):
        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            cursor.execute('''
                INSERT INTO tbl_carga_incomp (
                    id_carga, cod_item, qtde_atual, 
                    qtde_solic, flag_pendente
                ) VALUES (
                    ?, ?, ?, 
                    ?, TRUE
                );
                ''',
                (id_carga, cod_item, qtde_atual, qtde_solic)
            )
            connection.commit()
        return


    @staticmethod
    # FINALIZA REGISTRO NA TABELA DE CARGAS INCOMPLETAS
    def conclude_carga_incomp(id_carga):
        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            cursor.execute('''
                UPDATE tbl_carga_incomp 
                SET flag_pendente = FALSE
                WHERE 
                    id_carga = ?;
                ''',
                (id_carga,)
            )
        return
            
            
    @staticmethod
    # ALTERA REGISTRO NA TABELA DE CARGAS INCOMPLETAS
    def update_carga_incomp(id_carga, cod_item, set_qtde):
        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            cursor.execute('''
                SELECT qtde_atual
                FROM tbl_carga_incomp 
                WHERE 
                    id_carga = ? AND 
                    cod_item = ?;
                ''',
                (id_carga, cod_item)
            )
            row = cursor.fetchone()
            if not row:
                return 'Erro: Registro para alteracão não encontrado.'
            else:
                qtde_atual += row[0]
                
                flag_pendente = 'TRUE'
                if set_qtde == qtde_atual:
                    flag_pendente = 'FALSE'
                elif set_qtde < qtde_atual:
                    return 'Erro: Quantidade menor do que a separada.'
                
                cursor.execute('''
                    UPDATE tbl_carga_incomp 
                    SET 
                        qtde_atual = ?,
                        flag_pendente = ?
                    WHERE 
                        id_carga = ? AND 
                        cod_item = ?;
                    ''',
                    (qtde_atual, flag_pendente, id_carga, cod_item)
                )
                
                connection.commit()


    @staticmethod
    # BUSCA CARGAS INCOMPLETAS
    # id_carga = False // retorna todos os itens das cargas incompletas
    # id_carga = <int> // retorna todos os itens de uma carga incompletas
    def get_carga_incomp(id_carga=False):
        where_clause = 'WHERE flag_pendente = TRUE'
        
        if id_carga:
            where_clause += f' AND id_carga = {id_carga}'

        query = '''
            SELECT DISTINCT id_carga, i.cod_item, desc_item, qtde_atual, qtde_solic
            FROM tbl_carga_incomp ci
            JOIN itens i
            ON ci.cod_item = i.cod_item
            {a};
        '''.format(a=where_clause)
        
        dsn = 'SQLITE'
        result, columns = cde.db_query(query, dsn)
        
        return result, columns 


    @staticmethod
    # retorna todas as cargas incompletas
    def listed_carga_incomp():
        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            cursor.execute('''
                SELECT DISTINCT id_carga
                FROM tbl_carga_incomp ci
                
                WHERE ci.flag_pendente = TRUE;
            ''')
            rows = cursor.fetchall()
            return [row[0] for row in rows]


    @staticmethod
    # RETORNA CARGAS FINALIZADAS
    def get_cargas_finalizadas():
        all_cargas = CargaUtils.get_all_cargas()
        cargas_pendentes = CargaUtils.listed_carga_incomp()
        
        cargas_finalizadas = [carga for carga in all_cargas if carga not in cargas_pendentes]
        
        return cargas_finalizadas


    @staticmethod
    # BUSCA CARGAS DO HISTÓRICO
    def select_carga_from_historico(id_carga):
        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            cursor.execute('''
                SELECT i.cod_item, desc_item, quantidade
                FROM tbl_transactions h
                
                JOIN itens i
                ON h.cod_item = i.cod_item
                
                WHERE id_carga = ?;
            ''', (id_carga,))
            rows = cursor.fetchall()
            return rows


    @staticmethod
    # RETORNA OBSERVACOES COM O ID DE CARGA
    def get_obs_with_carga(id_carga):
        query = '''
            SELECT DISTINCT
                crg.OBSERVACAO AS OBS_CARGA

            FROM DB2ADMIN.ITEMPED iped

            JOIN DB2ADMIN.IGRUPOPE icrg
            ON icrg.NRO_PEDIDO = iped.NRO_PEDIDO
            AND icrg.SEQ = iped.SEQ

            JOIN DB2ADMIN.PEDIDO ped
            ON icrg.NRO_PEDIDO = ped.NRO_PEDIDO

            JOIN DB2ADMIN.GRUPOPED crg
            ON icrg.CODIGO_GRUPOPED = crg.CODIGO_GRUPOPED

            JOIN DB2ADMIN.CLIENTE cl
            ON cl.CODIGO_CLIENTE = ped.CODIGO_CLIENTE

            WHERE icrg.CODIGO_GRUPOPED = {a};
        '''.format(a=id_carga)

        dsn = cde.get_unit()
        result, columns = cde.db_query(query, dsn)

        if result:
            return result[0][0]
        return None


    @staticmethod
    # RETORNA CLIENTE COM O ID DE CARGA
    def get_cliente_with_carga(id_carga):
        query = '''
            SELECT DISTINCT
                cl.FANTASIA AS FANT_CLIENTE

            FROM DB2ADMIN.ITEMPED iped

            JOIN DB2ADMIN.IGRUPOPE icrg
            ON icrg.NRO_PEDIDO = iped.NRO_PEDIDO
            AND icrg.SEQ = iped.SEQ

            JOIN DB2ADMIN.PEDIDO ped
            ON icrg.NRO_PEDIDO = ped.NRO_PEDIDO

            JOIN DB2ADMIN.GRUPOPED crg
            ON icrg.CODIGO_GRUPOPED = crg.CODIGO_GRUPOPED

            JOIN DB2ADMIN.CLIENTE cl
            ON cl.CODIGO_CLIENTE = ped.CODIGO_CLIENTE

            WHERE icrg.CODIGO_GRUPOPED = {a};
        '''.format(a=id_carga)

        dsn = cde.get_unit()
        result, columns = cde.db_query(query, dsn)

        if result:
            return result[0][0]
        return None


    @staticmethod
    # Retorna todos os IDs de cargas faturadas,
    # incluindo as cargas 'implantados', sem duplicatas.
    def get_all_cargas():
        cargas_preset = CargaUtils.get_preset_cargas(1)
        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            cursor.execute('''
                SELECT DISTINCT id_carga
                FROM tbl_transactions
                WHERE 
                    id_carga != '' AND
                    id_carga != '0'
                ORDER BY id_carga DESC;
            ''')
            rows = cursor.fetchall()
            
            # Converte os resultados da consulta em uma lista de inteiros
            cargas_db = [row[0] for row in rows] if rows else []

        # Combina as cargas do banco de dados com as do preset
        combined_cargas = cargas_db + cargas_preset
        
        # Remove duplicatas mantendo a ordem
        seen = set()
        all_cargas = []
        for carga in combined_cargas:
            if carga not in seen:
                all_cargas.append(carga)
                seen.add(carga)
        return all_cargas


    @staticmethod
    # BUSCA CARGAS FINALIZADAS DE PRESETS
    def get_preset_cargas(index):
        try:
            with open(f'report/cargas_preset/filtro_{index}.txt', 'r', encoding='utf-8') as file:
                cargas = file.read().strip().split(', ')
        except:
            cargas = []
        return cargas

    
    @staticmethod
    # exclui carga colocando ela no preset de cargas (.txt)
    def excluir_carga(id_carga):
        with open('report/cargas_preset/filtro_1.txt', 'a', encoding='utf-8') as file:
            file.write(', ' + id_carga)
        return


class MovRequestUtils:
    @staticmethod
    def get_mov_request(id_req=False):
        # filtros para apenas requisições
        # produtos acabados
        # no deposito 2
        where_clause = \
            """
            AND 
                M.OBS LIKE '%Requisicao :%' AND 
                (
                    GRUPO_DESCRICAO = 'PRODUTO ACABADO' OR 
                    GRUPO_DESCRICAO = 'REVENDA'
                ) AND
                I.UNIDADE_DESCRICAO = 'CX' AND
                M.DEPOSITO = 2 AND
                TIPO_MOVIMENTO = 'S'
            """
        
        if id_req:
            # complementa o where_clause
            # para retornar apenas uma requisição
            where_clause += f" AND M.DOC_ORIGEM = '{id_req}'"
        
        all_requests = MovRequestUtils.get_all_requests()
        
        request_except_query = ', '.join(map(str, all_requests))
        
        query = '''
            SELECT DISTINCT
                M.DOCUMENTO           AS LOG_PROMOB,
                M.DOC_ORIGEM          AS DOC_ORIGEM,
                M.TIPO_TRANSACAO      AS TIPO_TRANSACAO, 
                M.TIPO_MOVIMENTO      AS TIPO_MOVIMENTO,
                M.DEPOSITO            AS DEPOSITO,
                I.ITEM                AS COD_ITEM,
                I.ITEM_DESCRICAO      AS DESC_ITEM, 
                I.UNIDADE_DESCRICAO   AS UNIDADE,
                CAST(QTDE AS INTEGER) AS QTDE,
                USUARIO               AS USUARIO,
                M.DATA_MOVIMENTACAO   AS DATA,
                M.OBS                 AS OBS
            FROM 
                DB2ADMIN.HUGO_PIETRO_VIEW_MOVIMENTOS M
            JOIN 
                DB2ADMIN.HUGO_PIETRO_VIEW_ITEM I
                ON I.ITEM = M.ITEM
                
            WHERE M.DOC_ORIGEM NOT IN ({b})
            {a}
            
            ORDER BY
                DOCUMENTO DESC, I.ITEM;
        '''.format(a=where_clause, b=request_except_query)
        
        dsn = cde.get_unit()
        result, columns = cde.db_query(query, dsn)
        
        return result, columns


    @staticmethod
    # lê o arquivo json no servidor local
    # e retorna a lista de requests
    def readJsonReqSeq(filename, seq=False):
        base_path = os.path.join(app.root_path, 'report/requests')
        seq = int(seq)
        if not seq:
            # 1234.json
            # Unifica todos os arquivos JSON com a mesma base de nome
            unified_data = []
            seq = 0
            while True:
                file_path = os.path.join(base_path, f'{filename}.json')
                if seq > 0:  
                    file_path = os.path.join(base_path, f'{filename}-{seq}.json')
                
                if not os.path.exists(file_path):
                    break
                with open(file_path, 'r') as file:
                    data = json.load(file)
                    unified_data.extend(data)
                seq += 1
            if unified_data:
                return unified_data
            else:
                return None
        else:
            # 1234-1.json
            # Lê o arquivo JSON específico com a sequência fornecida
            file_path = os.path.join(base_path, f'{filename}.json')
            if seq > 0:  
                file_path = os.path.join(base_path, f'{filename}-{seq}.json')
            
            if os.path.exists(file_path):
                with open(file_path, 'r') as file:
                    return json.load(file)
            else:
                return None
    
    
    @staticmethod
    # Retorna todos os IDs de requisição,
    # incluindo as requisições 'implantadas', sem duplicatas.
    def get_all_requests():
        requests_preset = MovRequestUtils.get_preset_requests(1)
        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            cursor.execute('''
                SELECT DISTINCT id_request
                FROM tbl_transactions
                ORDER BY id_request DESC;
            ''')
            rows = cursor.fetchall()
            
            # Converte os resultados da consulta em uma lista de inteiros
            requests_db = [row[0] for row in rows] if rows else []

        # Combina as requests do banco de dados com as do preset
        combined_requests = requests_db + requests_preset
        
        # Remove duplicatas mantendo a ordem
        seen = set()
        all_requests = []
        for request in combined_requests:
            if request not in seen:
                all_requests.append(request)
                seen.add(request)
        return all_requests
    
    
    @staticmethod
    # BUSCA requisições FINALIZADAS DE PRESETS
    def get_preset_requests(index):
        try:
            with open(f'report/requests_preset/filtro_{index}.txt', 'r', encoding='utf-8') as file:
                requests = file.read().strip().split(', ')
        except:
            requests = []
        return requests

    
class OrdemProducaoUtils:
    @staticmethod
    def get_ordem_producao(doc_origem=False):
        where_clause = """
            WHERE 
                I.GRUPO_DESCRICAO = 'PRODUTO ACABADO' AND
                I.UNIDADE_DESCRICAO = 'CX' AND
                M.TIPO_TRANSACAO = 'EPP' AND
                M.DEPOSITO = 2 AND
                L.ORDEM != 0
        """
        
        if doc_origem:
            where_clause += f" AND M.DOC_ORIGEM = '{doc_origem}'"
        
        query = '''
            SELECT DISTINCT
                M.DOCUMENTO           AS LOG_PROMOB,
                L.LOTE                AS LOTE_PROMOB,
                M.DOC_ORIGEM          AS DOC_ORIGEM,
                L.ORDEM               AS ORDEM_PRODUCAO,
                M.TIPO_TRANSACAO      AS TIPO_TRANSACAO, 
                M.TIPO_MOVIMENTO      AS TIPO_MOVIMENTO,
                M.DEPOSITO            AS DEPOSITO,
                I.ITEM                AS COD_ITEM,
                I.ITEM_DESCRICAO      AS DESC_ITEM, 
                I.UNIDADE_DESCRICAO   AS UNIDADE,
                CAST(QTDE AS INTEGER) AS QTDE,
                L.LOTE_FAB            AS COD_LOTE,
                M.DATA_MOVIMENTACAO   AS DATA,
                M.OBS                 AS OBS
            FROM 
                DB2ADMIN.HUGO_PIETRO_VIEW_MOVIMENTOS M
            JOIN 
                DB2ADMIN.HUGO_PIETRO_VIEW_VILOTFAB L 
                ON M.DOC_ORIGEM = CAST(L.ORDEM AS VARCHAR)
            JOIN 
                DB2ADMIN.HUGO_PIETRO_VIEW_ITEM I
                ON I.ITEM = M.ITEM
            {a}
            
            ORDER BY
                DOCUMENTO DESC, L.ORDEM, I.ITEM;
        '''.format(a=where_clause)
        
        dsn = cde.get_unit()
        result, columns = cde.db_query(query, dsn)
        
        return result, columns


class HistoricoUtils:
    @staticmethod
    # SELECIONA TODOS ITENS DE REGISTRO POSITIVO NO ENDEREÇO FORNECIDO
    def select_rua(letra, numero):
        sql_balance_calc = EstoqueUtils.sql_balance_calc
        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            cursor.execute('''
                SELECT 
                    cod_item, lote_item, 
                    COALESCE({a}, 0) as saldo
                FROM tbl_transactions
                WHERE 
                    rua_letra = ? AND
                    rua_numero = ?
                GROUP BY 
                    cod_item, lote_item;
            '''.format(a=sql_balance_calc), (letra, numero))
            
            items = cursor.fetchall()

            return items


    @staticmethod
    # INSERE REGISTRO NA TABELA DE HISTÓRICO
    def insert_historico(numero, letra, cod_item, lote_item, quantidade, operacao, timestamp, id_carga=0, id_request=0) -> bool:
        id_user_mov = session['id_user']
        try:    
            with sqlite3.connect(db_path) as connection:
                cursor = connection.cursor()
                cursor.execute(
                    '''
                    INSERT INTO tbl_transactions (
                        rua_numero, rua_letra, cod_item,
                        lote_item, quantidade, operacao,
                        time_mov, id_user, id_carga, 
                        id_request
                    ) VALUES (
                        ?, ?, ?,
                        ?, ?, ?,
                        ?, ?, ?,
                        ?
                    ) ;''', (
                        numero, letra, cod_item,
                        lote_item, quantidade, operacao, 
                        timestamp, id_user_mov, id_carga,
                        id_request
                    )
                )
                connection.commit()
            return True
        except Exception as e:
            return False


    @staticmethod
    # RETORNA MOVIMENTAÇÕES NO INTERVALO
    def get_historico(page=1, per_page=10):
        offset = (page - 1) * per_page

        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()

            cursor.execute('SELECT COUNT(*) FROM tbl_transactions;')
            row_count = cursor.fetchone()[0] # número total de linhas

            cursor.execute('''
                SELECT  
                    h.rua_numero, h.rua_letra, h.cod_item,
                    i.desc_item, h.lote_item, h.quantidade,
                    h.operacao, u.id_user||' - '||u.nome_user,
                    h.time_mov
                FROM tbl_transactions h
                
                JOIN itens i ON h.cod_item = i.cod_item
                JOIN users u ON h.id_user = u.id_user
                
                ORDER BY h.time_mov DESC
                
                LIMIT ? OFFSET ?;
            ''', (per_page, offset))

            estoque = [{
                'endereco'  : str(row[1]) + '.' + str(row[0]) + ' ', 'cod_item'   : row[2], 
                'desc_item' : row[3],          'cod_lote'  : row[4], 'quantidade' : row[5], 
                'operacao'  : row[6],          'user_name' : row[7], 'timestamp'  : row[8]
            } for row in cursor.fetchall()]
        return estoque, row_count


    @staticmethod
    # RETORNA TODAS AS MOVIMENTAÇÕES
    def get_all_historico():
        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            
            cursor.execute('''
                SELECT  
                    h.rua_numero, h.rua_letra, h.cod_item,
                    i.desc_item, h.lote_item, h.quantidade,
                    h.operacao, u.id_user||' - '||u.nome_user, 
                    h.time_mov
                FROM tbl_transactions h
                
                JOIN itens i ON h.cod_item = i.cod_item
                JOIN users u ON h.id_user = u.id_user
                
                ORDER BY h.time_mov DESC;
            ''')
            
            estoque = [{
                'endereco'  : str(row[1]) + '.' + str(row[0]) + ' ', 'cod_item'   : row[2], 
                'desc_item' : row[3],          'cod_lote'  : row[4], 'quantidade': row[5], 
                'operacao'  : row[6],          'user_name' : row[7],  'timestamp'  : row[8]
            } for row in cursor.fetchall()]
        return estoque


class ProdutoUtils:
    @staticmethod
    # retorna itens do banco de dados do ERP
    # implementa o filtro para itens embalagem
    def get_itens_from_erp():
        whitelist = cde.get_file_text('app/presets/item-whitelist.txt')
        query = '''
            SELECT i.ITEM, i.ITEM_DESCRICAO, i.GTIN_14
            FROM DB2ADMIN.HUGO_PIETRO_VIEW_ITEM i
            WHERE (
                (
                    UNIDADE_DESCRICAO = 'CX' OR 
                    UNIDADE_DESCRICAO = 'UN' OR 
                    UNIDADE_DESCRICAO = 'FD'
                ) AND (
                    GRUPO_DESCRICAO = 'PRODUTO ACABADO' OR 
                    GRUPO_DESCRICAO = 'REVENDA')
                AND 
                    NOT GTIN_14 = ''
            )
            OR 
                -- whitelist de itens
                i.ITEM IN ({a});
        '''.format(a=whitelist)

        dsn = cde.get_unit()
        result, columns = cde.db_query(query, dsn)
        return result, columns

    
    @staticmethod
    # RETORNA TODOS OS PARÂMETROS DA TABELA ITENS
    def get_all_itens():
        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            cursor.execute('''
                SELECT DISTINCT *
                FROM itens i
                ORDER BY i.cod_item;
            ''')

            itens = [{
                'cod_item': row[0], 'desc_item': row[1], 'dun14': row[2], 'flag_ativo': bool(row[3])
            } for row in cursor.fetchall()]
        return itens

    
    @staticmethod
    # RETORNA TODOS OS PARÂMETROS DOS ITENS ATIVOS
    def get_active_itens():
        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            cursor.execute('''
                SELECT DISTINCT *
                FROM itens i
                WHERE i.flag_ativo = 1
                ORDER BY i.cod_item;
            ''')

            itens = [{
                'cod_item': row[0], 'desc_item': row[1], 'dun14': row[2]
            } for row in cursor.fetchall()]
        return itens

  
    @staticmethod
    # leitor de código
    # retorna dados do item
    def get_item_json(input_code):
        if 'EM.' not in input_code:
            input_code = re.sub(r'[^0-9;]', '', (input_code.strip()))
        print(f'  | Código fornecido: {input_code}')
        
        if len(input_code) == 4 or len(input_code) == 0:
            desc_item, cod_item, cod_lote, cod_linha = 'ITEM NÃO CADASTRADO OU INATIVO', '', '', ''
            print(f'  | {desc_item}')
            return jsonify(
                {
                'json_cod_item' : cod_item, 
                'json_desc_item': desc_item, 
                'json_cod_lote' : cod_lote, 
                'json_cod_linha': cod_linha
                }
            )

        else:     
            # VALIDAÇÃO P/ CÓDIGO INTERNO SEM ';'
            if len(input_code) == 6 or len(input_code) == 7:
                input_code = input_code + ';'

            partes       = input_code.split(';')
            cod_item     = []
            cod_item_qnt = None

            if len(partes) == 1:
                cod_barra  = partes[0]

                with sqlite3.connect(db_path) as connection:
                    cursor = connection.cursor()
                    cursor.execute('''
                        SELECT i.desc_item, i.cod_item
                        FROM itens i
                        WHERE i.dun14 = ? 
                        AND i.flag_ativo = 1
                        ORDER BY i.cod_item;
                    ''',
                    (cod_barra,))

                    rows = cursor.fetchall()

                    for row in rows:
                        codigos_itens = row[1]
                        cod_item.append(codigos_itens)
                        cod_item_qnt = len(cod_item)
                    
                    if cod_item:
                        with sqlite3.connect(db_path) as connection:
                            cursor = connection.cursor()
                            cursor.execute('''
                                SELECT i.desc_item    
                                FROM itens i
                                WHERE i.cod_item = ? 
                                AND i.flag_ativo = 1
                                ORDER BY i.cod_item;
                            ''',
                            (cod_item[0],))

                        row = cursor.fetchall()
                        
                        if row:
                            desc_item = row[0][0]
                            if 'VINHO' in desc_item:
                                cod_lote = 'VINHOS'
                            else:
                                cod_lote = ''
                    else:
                        desc_item, cod_item, cod_lote = 'ITEM NÃO CADASTRADO OU INATIVO', '', ''
                        print(f'  | {desc_item}')
                    return jsonify(
                        {
                        'json_cod_item': cod_item,
                        'json_desc_item': desc_item, 
                        'json_cod_lote': cod_lote, 
                        'json_cod_item_ocurr': cod_item_qnt
                        }
                    )

            elif len(partes) == 2:
                codigos_itens = partes[0]
                cod_item.append(codigos_itens)
                
                if partes[1] != '':
                    cod_lote = 'CS' + partes[1]
                else:
                    cod_lote = ''
                if 'EM.' in input_code:
                    cod_lote = 'OUTROS'

                with sqlite3.connect(db_path) as connection:
                    cursor = connection.cursor()
                    cursor.execute('''
                        SELECT i.desc_item
                        FROM itens i
                        WHERE i.cod_item = ?
                        AND i.flag_ativo = 1;
                    ''', 
                    (codigos_itens,))

                    resultado = cursor.fetchone()
                    if resultado is not None:
                        desc_item = resultado[0]
                        if 'VINHO' in desc_item:
                            cod_lote = 'VINHOS'
                    else:
                        desc_item, cod_item, cod_lote = 'ITEM NÃO CADASTRADO OU INATIVO', '', ''
                        print(f'  | {desc_item}')
                    return jsonify(
                        {
                        'json_cod_item' : cod_item, 
                        'json_cod_lote' : cod_lote, 
                        'json_desc_item': desc_item
                        }
                    )

            else:
                desc_item, cod_item, cod_lote = 'ITEM NÃO CADASTRADO OU INATIVO', '', ''
                print(f'  | {desc_item}')
                return jsonify(
                    {
                    'json_cod_item' : cod_item, 
                    'json_cod_lote' : cod_lote, 
                    'json_desc_item': desc_item
                    }
                )


    @staticmethod
    # RETORNA APENAS DESCRIÇÃO DO ITEM (DESCONTINUADO)
    def get_desc_itens():
        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            cursor.execute('''
                SELECT DISTINCT desc_item
                FROM itens i
                ORDER BY i.desc_item;
            ''')

            desc_item = [row[0] for row in cursor.fetchall()]
        return desc_item


    @staticmethod
    # ALTERA STATUS (ATIVO/INATIVO) DO ITEM
    def toggle_item_flag(cod_item, flag) -> None:
        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            cursor.execute('''
                UPDATE itens SET flag_ativo = ? WHERE cod_item = ?;
            ''', (flag, cod_item))

            connection.commit()
        return


class UserUtils:
    @staticmethod
    def set_ult_acesso(id_user) -> bool:
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            with sqlite3.connect(db_path) as connection:
                cursor = connection.cursor()
                cursor.execute('''
                    UPDATE users
                    SET ult_acesso = ?
                    WHERE id_user = ?;
                ''',
                (current_time, id_user))
                connection.commit()
            return True
        except Exception as e:
            return False

    
    @staticmethod
    def set_password(id_user, password) -> bool:
        try:
            # hash the password
            password = misc.hash_key(password)
            
            with sqlite3.connect(db_path) as connection:
                cursor = connection.cursor()
                cursor.execute('''
                    UPDATE users 
                    SET password_user = ?
                    WHERE id_user = ?;
                ''',
                (password, id_user))
                connection.commit()
            return True
        
        except Exception as e:
            print(f'[ERRO] {e}')
            return False


    @staticmethod
    def get_user_key(login_user):
        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            cursor.execute('''
                SELECT 
                    password_user
                FROM users
                WHERE login_user = ?;
            ''', (login_user,))

            row = cursor.fetchone()

            if row is None:
                return ''
            return str(row[0])


    @staticmethod
    def get_user_data(login_user):
        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            cursor.execute('''
                SELECT 
                    id_user, nome_user, 
                    sobrenome_user, privilege_user,
                    ult_acesso
                FROM users
                WHERE login_user = ?;
            ''', (login_user,))

            row = cursor.fetchone()

            if row is None:
                return row
            return row

    
    @staticmethod
    def get_user_initials(nome, snome): # nome e sobrenome
        if snome == ' ': # verifica se o sobrenome é vazio
            session['user_name'] = f'{nome}'
            session['user_initials'] = f'{nome[0]}{snome[1]}'
        else:
            session['user_name'] = f'{nome} {snome}'
            session['user_initials'] = f'{nome[0]}{snome[0]}'
   

    @staticmethod
    # RETORNA DADOS DE PERMISSÃO
    def get_permissions(id_perm=False):
        if not id_perm:
            with sqlite3.connect(db_path) as connection:
                cursor = connection.cursor()
                cursor.execute('''
                    SELECT * 
                    FROM aux_permissions
                    ORDER BY id_perm;
                ''')

                permissions = [{
                    'id_perm': row[0], 'desc_perm': row[1]
                } for row in cursor.fetchall()]
        else:
            with sqlite3.connect(db_path) as connection:
                cursor = connection.cursor()
                cursor.execute('''
                    SELECT * 
                    FROM aux_permissions
                    WHERE id_perm = ?
                    ORDER BY id_perm;
                ''', (id_perm,))

                permissions = [{
                    'id_perm': row[0], 'desc_perm': row[1]
                } for row in cursor.fetchall()]

        return permissions


    @staticmethod
    # INSERE PERMISSÃO
    def insert_permissions(id_perm, desc_perm) -> bool:
        try:
            with sqlite3.connect(db_path) as connection:
                cursor = connection.cursor()
                cursor.execute('''
                    INSERT INTO aux_permissions (
                        id_perm, desc_perm
                    ) VALUES (
                        ?, ?
                    );
                ''',(id_perm, desc_perm))
                
                connection.commit()
                
                return True
        except Exception as e:
            return False


    @staticmethod
    # ALTERA PERMISSÃO
    def update_permissions(old_id_perm, id_perm, desc_perm) -> bool:
        try:
            with sqlite3.connect(db_path) as connection:
                cursor = connection.cursor()
                cursor.execute('''
                    UPDATE 
                    aux_permissions 
                    SET 
                        id_perm = ?,
                        desc_perm = ? 
                    WHERE 
                        id_perm = ?;
                ''',(id_perm, desc_perm, old_id_perm))
                
                connection.commit()
                
                return True
        except Exception as e:
            return False


    @staticmethod
    # DELETA PERMISSÃO
    def delete_permissions(id_perm) -> bool:
        try:
            with sqlite3.connect(db_path) as connection:
                cursor = connection.cursor()
                cursor.execute('''
                    DELETE FROM aux_permissions 
                    WHERE id_perm = ?;
                ''',(id_perm,))
                
                connection.commit()
                
                return True
        except Exception as e:
            return False


    @staticmethod
    # RETORNA DADOS DOS USUÁRIOS
    def get_users():
        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            cursor.execute('''
                SELECT 
                    u.nome_user || ' ' || u.sobrenome_user, 
                    ap.desc_priv,
                    u.ult_acesso, u.id_user
                FROM users u
                        
                JOIN aux_privilege ap 
                ON u.privilege_user = ap.id_priv
                        
                ORDER BY u.ult_acesso DESC;
            ''')

            users_list = [{
                'user_name' : row[0], 'user_grant': row[1], 
                'ult_acesso': row[2], 'cod_user'  : row[3],
            } for row in cursor.fetchall()]

        return users_list


    @staticmethod
    # RETORNA LISTA DE PERMISSÕES DO USUÁRIO
    def get_user_permissions(user_id):
        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            cursor.execute('''
                SELECT up.id_perm
                FROM user_permissions up
                WHERE id_user = ?
                ORDER BY id_user;
            ''',
            (user_id,))

            rows = cursor.fetchall()

            if rows:
                result = [{'id_perm': row[0]} for row in rows]
                return result
            else:
                return []


    @staticmethod
    # RETORNA DADOS DO USUÁRIO
    def get_userdata(id_user):
        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            cursor.execute('''
                SELECT  privilege_user, nome_user,
                        sobrenome_user, id_user, 
                        ult_acesso
                FROM users
                WHERE id_user = ?;
            ''',
            (id_user,))

            user_data = [{
                'privilege_user': row[0], 'nome_user' : row[1], 'sobrenome_user': row[2],
                'id_user'       : row[3], 'ult_acesso': row[4]
            } for row in cursor.fetchall()]

            return user_data


    @staticmethod
    # RETORNA NOME DO USUÁRIO
    def get_username(id_user):
        query = '''
            SELECT DISTINCT
                u.nome_user || ' ' || u.sobrenome_user AS NOME_USER
            FROM users u
            WHERE u.id_user = {a};
        '''.format(a=id_user)

        dsn = 'SQLITE'
        result, columns = cde.db_query(query, dsn)

        if result:
            return result[0][0]
        return None


    @staticmethod
    # RETORNA ULTIMO ACESSO DO USUÁRIO
    def get_ult_acesso():
        id_user = session.get('id_user')
        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            cursor.execute('''
                SELECT ult_acesso
                FROM users
                WHERE id_user = ?;
            ''', (id_user,))
            row = cursor.fetchone()

            ult_acesso = row[1] if row else None

            return ult_acesso


class Schedule:
    class EnvaseUtils:
        @staticmethod
        # RETORNA TABELA DE PROGRAMAÇÃO (ENVASE)
        def get_envase():
            with sqlite3.connect(db_path) as connection:
                cursor = connection.cursor()
                cursor.execute('''
                    SELECT  p.id_envase, p.cod_linha, c.fantasia_cliente,
                            i.cod_item, i.desc_item, p.qtde_solic,
                            p.data_entr_antec, p.data_envase, p.observacao,
                            p.flag_concluido
                    FROM prog_envase p
                    JOIN itens i ON p.cod_item = i.cod_item
                    JOIN clientes c ON p.cod_cliente = c.cod_cliente
                    ORDER BY p.data_envase;
                ''')

                envase_list = [{
                    'id_envase'       : row[0], 'linha'       : row[1], 'fantasia_cliente' : row[2], 
                    'cod_item'        : row[3], 'desc_item'   : row[4], 'quantidade'       : row[5],
                    'data_entr_antec' : row[6], 'data_envase' : row[7], 'observacao'       : row[8],
                    'flag_concluido'  : row[9]
                } for row in cursor.fetchall()]

            return envase_list


    class ProcessamentoUtils:
        @staticmethod
        # RETORNA TABELA DE PROGRAMAÇÃO (PROCESSAMENTO)
        def get_producao():
            with sqlite3.connect(db_path) as connection:
                cursor = connection.cursor()
                cursor.execute('''
                    SELECT  p.id_producao, p.cod_linha, p.liq_linha,
                            p.liq_cor, p.embalagem, p.lts_solic,
                            p.data_entr_antec, p.data_producao, p.observacao,
                            p.flag_concluido, p.liq_tipo
                    FROM prog_producao p
                    ORDER BY p.data_producao;
                ''')
                producao_list = [{
                    'id_producao'     : row[0], 'linha'        : row[1], 'liq_linha' : row[2], 
                    'liq_cor'         : row[3], 'embalagem'    : row[4], 'litros'    : row[5], 
                    'data_entr_antec' : row[6], 'data_producao': row[7], 'observacao': row[8],
                    'flag_concluido'  : row[9], 'liq_tipo'     : row[10]
                } for row in cursor.fetchall()]
                
            return producao_list


class EtiquetaGenerator:
    IMAGE_SIZE = (400, 400)
    FONT_PATH = 'arialbd.ttf'

    @staticmethod
    def generate(qr_text, desc_item, cod_item, cod_lote) -> str:
        """
        Gera uma etiqueta com QR Code e descrição.
        Retorna a imagem em base64.
        """
        img = EtiquetaGenerator._create_base_image()
        qr_image = misc.qr_code(qr_text)

        EtiquetaGenerator._paste_qr_code(img, qr_image)
        EtiquetaGenerator._draw_text(img, cod_item, desc_item, cod_lote)

        return EtiquetaGenerator._image_to_base64(img)

    @staticmethod
    def _create_base_image():
        """Cria a imagem base limpa."""
        return Image.new('RGB', EtiquetaGenerator.IMAGE_SIZE, color='white')

    @staticmethod
    def _paste_qr_code(img, qr_image):
        """Adiciona o QR Code na imagem centralizada."""
        width, height = img.size
        qr_width, qr_height = qr_image.size

        # Redimensiona o QR Code se necessário
        if qr_width > width or qr_height > height:
            qr_image = qr_image.resize((width // 2, height // 2))

        qr_x = (width - qr_width) // 2
        qr_y = (height - qr_height) // 2
        img.paste(qr_image, (qr_x, qr_y))

    @staticmethod
    def _draw_text(img, cod_item, desc_item, cod_lote):
        """Desenha os textos na imagem."""
        draw = ImageDraw.Draw(img)
        width, height = img.size

        # Configura fonte
        font_large = ImageFont.truetype(EtiquetaGenerator.FONT_PATH, 30)
        font_small = ImageFont.truetype(EtiquetaGenerator.FONT_PATH, 22)

        # Desenha o código do lote
        cod_lote_text = f'LOTE: {cod_lote}'
        lote_bbox = draw.textbbox((0, 0), cod_lote_text, font=font_large)
        lote_x = (width - (lote_bbox[2] - lote_bbox[0])) // 2
        lote_y = height // 1.5
        draw.text((lote_x, lote_y), cod_lote_text, fill='black', font=font_large)

        # Desenha a descrição do item em múltiplas linhas
        desc_text = f'{cod_item} - {desc_item}'
        lines = textwrap.wrap(desc_text, width=30)
        y_text = height - height // 4.6

        for line in lines:
            text_width, text_height = draw.textbbox((0, 0), line, font=font_small)[2:]
            line_x = (width - text_width) // 2
            draw.text((line_x, y_text), line, fill='black', font=font_small)
            y_text += text_height

    @staticmethod
    def _image_to_base64(img):
        """Converte a imagem para base64."""
        img_io = io.BytesIO()
        img.save(img_io, format='PNG')
        img_io.seek(0)
        return base64.b64encode(img_io.getvalue()).decode()


class misc:
    @staticmethod
    # BUSCA FRASE PARA /INDEX
    def get_frase() -> str:
        with open('static/frases.txt', 'r', encoding='utf-8') as file:
            frases = file.readlines()
            frase = random.choice(frases).strip()
            if not frase:
                frase = 'Seja a mudança que você deseja ver no mundo.'
        return frase


    @staticmethod
    # CONVERTE TIMESTAMP PARA FORMATO DO DATABASE
    def parse_db_datetime(timestamp):
        if not timestamp:
            timestamp = datetime.now(timezone(timedelta(hours=-3)))
        elif isinstance(timestamp, str):
            timestamp = datetime.strptime(timestamp, '%Y-%m-%d')
            timestamp = timestamp.replace(tzinfo=timezone(timedelta(hours=-3)))
        
        return timestamp.strftime('%Y/%m/%d %H:%M:%S')
    

    @staticmethod
    # RETORNA TIMESTAMP
    def get_timestamp() -> str:
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


    @staticmethod
    # ADICIONA DIAS À DATA INFORMADA
    def add_days_to_datetime_str(date_str, qtde_days) -> str:

        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        
        new_date_obj = date_obj + timedelta(days=qtde_days)
        
        new_date_str = new_date_obj.strftime('%Y-%m-%d')
        
        return new_date_str


    @staticmethod
    # MENSAGEM DO TELEGRAM
    def tlg_msg(msg):
        if not session.get('user_grant') == 1:
            if debug == True:
                print('[ERRO] A mensagem não pôde ser enviada em modo debug')
                return None
            else:
                bot_token = os.getenv('TLG_BOT_TOKEN')
                chat_id   = os.getenv('TLG_CHAT_ID')

                url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
                params = {'chat_id': chat_id, 'text': msg}
                response = requests.post(url, params=params)
                return response.json()
        else:
            return None


    @staticmethod
    # CRIA QRCODE
    def qr_code(qr_text):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=5,
            border=5,
        )
        qr.add_data(qr_text)
        qr.make(fit=True)
        qr_image = qr.make_image(fill_color='black', back_color='white')

        return qr_image


    @staticmethod
    # HASH DA SENHA
    def hash_key(password) -> str:
        return pbkdf2_sha256.hash(password)


    @staticmethod
    # PARSE P/ FLOAT
    def parse_float(value) -> float:
        try:
            return float(value.replace(',', '.'))
        except ValueError:
            return 0.0
    
    
    @staticmethod
    @app.template_filter('parse_date')
    def parse_date(value):
        try:
            dt = datetime.strptime(value, "%a, %d %b %Y %H:%M:%S %Z")
            return dt.strftime("%d/%m/%Y")
        except Exception as e:
            return value

    @staticmethod
    # VERIFICA SENHA NO BANCO DE HASH
    def password_check(id_user, password) -> bool:
        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            cursor.execute('''
                SELECT password_user
                FROM users
                WHERE id_user = ?;
            ''', (id_user,))

            row = cursor.fetchone()
            
            if row:
                db_password = row[0]
                return misc.check_key(db_password, password)
            return False


    @staticmethod
    # VERIFICA SENHA NO BANCO DE HASH
    def check_key(hashed_pwd, pwd) -> bool:
        return pbkdf2_sha256.verify(pwd, hashed_pwd)


    class CSVUtils:
        @staticmethod
        # CSV PARA INTEGRAÇÃO ERP
        def iterate_csv_data_erp(data) -> str:
            csv_data = ''
            for item in data:
                line = ';'.join(map(str, item.values()))
                csv_data += f'"{line}"\n'
            return csv_data


        @staticmethod
        # CORPO CSV PADRAO
        def iterate_csv_data(data) -> str:
            csv_data = ''
            for item in data:
                line = ';'.join(map(str, item.values()))
                csv_data += f'{line}\n'
            return csv_data


        @staticmethod
        # ADICIONA CABECALHO PARA CSV
        def add_headers(data):
            if data and len(data) > 0:
                headers = ';'.join(data[0].keys())
                return f'{headers}\n'
            return ''

        
        @staticmethod    
        # RETORNA TABELA DE SALDO
        def get_export_promob():
            sql_balance_calc = EstoqueUtils.sql_balance_calc
            with sqlite3.connect(db_path) as connection:
                cursor = connection.cursor()
                cursor.execute('''
                    SELECT 
                        i.desc_item, 
                        i.cod_item, 
                        COALESCE(t.saldo, 0) as saldo, 
                        t.time_mov
                    FROM 
                        itens i
                    LEFT JOIN (
                        SELECT 
                            cod_item, {a} as saldo,
                            MAX(time_mov) as time_mov,
                            ROW_NUMBER() OVER(
                                PARTITION BY cod_item 
                                ORDER BY MAX(time_mov) DESC
                            ) as rn
                        FROM 
                            tbl_transactions h
                        GROUP BY 
                            cod_item
                        HAVING 
                            saldo != 0
                    ) t ON i.cod_item = t.cod_item
                    WHERE 
                        t.rn = 1 OR t.rn IS NULL
                    ORDER BY 
                        i.cod_item;
                '''.format(a=sql_balance_calc))

                saldo_visualization = [{
                    'cod_item': row[1],
                    'deposito': int(2),
                    'qtde'    : row[2]
                } for row in cursor.fetchall()]

            return saldo_visualization

        
        @staticmethod
        # CONSTRUTOR DE CSV
        def export_csv(data, filename, include_headers=True):
            if data and len(data) > 0:
                csv_data = ''
                if not include_headers:
                    csv_data += misc.CSVUtils.iterate_csv_data_erp(data)
                else:
                    csv_data += misc.CSVUtils.add_headers(data)
                    csv_data += misc.CSVUtils.iterate_csv_data(data)

                csv_filename = Response(csv_data, content_type='text/csv')
                csv_filename.headers['Content-Disposition'] = f'attachment; filename={filename}.csv'

                return csv_filename
            else:
                alert_type = 'DOWNLOAD IMPEDIDO \n'
                alert_msge = 'A tabela não tem informações o suficiente para exportação. \n'
                alert_more = ('''
                    POSSÍVEIS SOLUÇÕES:
                    • Verifique se a tabela possui mais de uma linha.
                    • Contate o suporte. 
                ''')
                return render_template(
                    'components/menus/alert.html', 
                    alert_type=alert_type, 
                    alert_msge=alert_msge, 
                    alert_more=alert_more, 
                    url_return=url_for('index')
                )


# métodos sem classe
# 
@app.before_request
def renew_session() -> None:
    # RENOVA A SESSÃO DE USUÁRIO
    session.modified = True
    return None


@app.before_request
def check_session_expiry() -> None | Response:
# verifica se a sessão está expirada
    if request.path.startswith(('/static', '/get', '/post')):
        # ignora as requisições de arquivos estáticos
        return None
    if 'last_active' in session:
    # se ultimo acesso estiver definido
        next_url = request.url
        last_active = session.get('last_active')             # horário da ultima requisição
        expiration_time = app.config['CDE_SESSION_LIFETIME'] # lifetime da sessão
        
        if isinstance(last_active, datetime): 
        # se é um objeto datetime...
            time_now = datetime.now(timezone.utc)
            
            # compara a diferença de tempo
            if (time_now - last_active) > expiration_time: 
                # se ultrapassar o tempo de expiração...
                session.clear() # limpa todos os dados da sessão
                session['next_url'] = next_url # define ultimo url acessado
                return redirect(url_for('login'))
    session['last_active'] = datetime.now(timezone.utc)


@app.before_request
def check_ip() -> None:
    # CHECA LISTA DE IPS (MODO DEBUG)
    client_ip = request.remote_addr
    
    temp_password = os.getenv('TEMP_PASSWORD')
    provided_password = request.args.get('password')
    
    if not debug == True:
        blacklist = os.getenv('BLACKLIST')
        if client_ip in blacklist:
            msg = f'{client_ip} na Blacklist.'
            misc.tlg_msg(msg)
            abort(403)

    else:
        if temp_password == provided_password:
            return None
        
        current_server_ip = request.host
        adm_ip = 'debug.cde.com'
        
        if adm_ip not in current_server_ip:
            if client_ip not in adm_ip:
                msg = f'{client_ip}'
                misc.tlg_msg(msg)
            abort(403)

    return None


@app.context_processor
def inject_page() -> dict:
    # RETORNA URL ACESSADA PELO USER
    current_page  = request.path
    if 'logged_in' in session:
        user_name = session.get('user_name')
        id_user   = session.get('id_user')
    return {'current_page': current_page}


@app.context_processor
def inject_version() -> dict:
    # INJETA VARIAVEL DE VERSÃO AO AMBIENTE
    return dict(app_version=app.config['APP_VERSION'])


@app.context_processor
def inject_unit() -> dict:
    # INJETA VARIAVEL DE UNIDADE AO AMBIENTE
    return dict(app_unit=app.config['APP_UNIT'])


@app.errorhandler(403)
def page_not_found(e) -> tuple[str, 403]:
    return render_template(
        '403.html',
        error_code=403,
        error=e
    ), 403


@app.errorhandler(404)
def page_not_found(e) -> tuple[str, 404]:
    return render_template(
        '404.html',
        error_code=404,
        error=e
    ), 404


@app.errorhandler(502)
def page_not_found(e) -> tuple[str, 502]:
    return render_template(
        '502.html',
        error_code=502,
        error=e
    ), 502


@app.errorhandler(503)
def page_not_found(e) -> tuple[str, 503]:
    return render_template(
        '503.html',
        error_code=503,
        error=e
    ), 503


@app.route('/force_503/')
def force_503() -> None:
    abort(503)
    return None


# ROTAS DE ACESSO | URL
#
@app.route('/')
@cde.verify_auth('CDE001')
def index() -> Response:
    # cria as tabelas
    cde.create_tables() # TODO: REMOVE from here
    
    return redirect(url_for('home'))


@app.route('/debug-page/')
@cde.verify_auth('DEV000')
def debug_page() -> str:
    return render_template('pages/debug-page.html')


@app.route('/home/')
@cde.verify_auth('CDE001')
def home() -> str:
    return render_template(
        'pages/index/cde-index.html', 
        frase=misc.get_frase()
    )


@app.route('/home/tl/')
@cde.verify_auth('CDE001')
def home_tl() -> str:
    return render_template(
        'pages/index/tl-index.html', 
        frase=misc.get_frase()
    )


@app.route('/home/hp/')
@cde.verify_auth('CDE001')
def home_hp() -> str:
    return render_template(
        'pages/index/hp-index.html', 
        frase=misc.get_frase()
    )


@app.route('/in-dev/')
@cde.verify_auth('CDE001')
def in_dev() -> str:
    return render_template('pages/error-handler.html')


@app.route('/users/')
@cde.verify_auth('CDE016')
def users() -> str:
    id_user = session.get('id_user')
    users = UserUtils.get_users()
    user_perm = UserUtils.get_user_permissions(id_user)
    user_perm = [item['id_perm'] for item in user_perm]
    
    return render_template(
        'pages/users/users.html', 
        users=users,
        user_perm=user_perm
    )


@app.route('/api/log/', methods=['POST'])
def log_message():
    data = request.json
    if 'message' in data:
        if cde.save_log(data['message']):
            print(f'{TAGS.INFO} Log salvo com sucesso.')
            return jsonify({"status": "success", "message": "Log salvo com sucesso."}), 200
        else:
            print(f'{TAGS.ERROR} Não foi possível salvar o log.')
            return jsonify({"status": "error", "message": "Não foi possível salvar o log."}), 500
    else:
        print(f'{TAGS.ERROR} Nenhuma mensagem foi recebida.')
        return jsonify({"status": "error", "message": "Nenhuma mensagem foi recebida."}), 400


@app.route('/cde/permissions/', methods=['GET', 'POST'])
@cde.verify_auth('CDE018')
def permissions() -> str:
    if request.method == 'POST':
        id_perm_add = request.form['id_perm_add']
        desc_perm_add = request.form['desc_perm_add']
        
        if id_perm_add and desc_perm_add:
            UserUtils.insert_permissions(id_perm_add, desc_perm_add)
    
    permissions = UserUtils.get_permissions()
    
    return render_template(
        'pages/cde-permissions.html',
        permissions=permissions
    )


@app.route('/cde/permissions/<string:id_perm>/', methods=['GET', 'POST'])
@cde.verify_auth('CDE018')
def permissions_id(id_perm) -> str:
    if request.method == 'POST':
        input_id_perm = request.form['id_perm']
        input_desc_perm = request.form['desc_perm']
        
        if input_id_perm and input_desc_perm:
            UserUtils.update_permissions(id_perm, input_id_perm, input_desc_perm)

    permissions = UserUtils.get_permissions()
    id_perm_data = UserUtils.get_permissions(id_perm)
    
    return render_template(
        'pages/cde-permissions.html',
        permissions=permissions,
        id_perm_data=id_perm_data
    )


# ROTA DE DATABASE MANAGER
@app.route('/database/', methods=['GET', 'POST'])
@cde.verify_auth('DEV000')
def api() -> str:
    if debug:
        if request.method == 'POST':
            query = request.form['sql_query'].replace("▷", ".").replace("-- para executar, clique em '.' acima", "")
            dsn = request.form['sel_schema']
            tables = cde.db_get_tables(dsn)
            print(f'query: {query}; dsn: {dsn}; tables: {tables}') # print(query, dsn, tables)
            if re.search(r'\b(DELETE|INSERT|UPDATE)\b', query, re.IGNORECASE):
                result = [["Os comandos 'INSERT', 'DELETE' e 'UPDATE' não são permitidos."]]
                return render_template(
                    'pages/api.html', 
                    result=result,
                    tables=tables,
                    query=query,
                    dsn=dsn
                )
            else:
                result, columns = cde.db_query(query, dsn)

                return render_template(
                    'pages/api.html', 
                    result=result,
                    columns=columns,
                    tables=tables,
                    query=query,
                    dsn=dsn
                )
    return render_template(
        'pages/api.html'
    )


# ROTA PAGINA DE LOGIN
@app.route('/login/', methods=['GET'])
def pagina_login() -> Response | str:
    if session.get('logged_in'):
    # somente se estiver logado
        # define o nome da rota de acesso 
        cde.verify_auth('CDE003')
        return redirect(url_for('index'))
    return render_template('pages/login.html')


@app.route('/cde/minha-conta/', methods=['GET'])
def cde_account() -> str | None:
    if session.get('logged_in'):
        return render_template('pages/account.html')
    return None


# ROTA DE SESSÃO LOGIN
@app.route('/login/', methods=['POST'])
def login():
    # TODO: método auxiliar
    if not request.method == 'POST':
        return redirect(url_for('login'))
    else:
        if 'logged_in' in session: 
            # se já estiver logado, entra no sistema
            return redirect(url_for('index'))
    
        input_login = str(request.form['login_user'])  # login
        input_pwd = str(request.form['password_user']) # senha

        # busca senha do user com o input de login
        user_pwd = UserUtils.get_user_key(input_login)

        if not user_pwd: 
        # ou seja, user não existe
            alert_msge = 'O usuário não foi encontrado. Tente novamente.'
            return render_template(
                'pages/login.html',
                alert_msge=alert_msge
            )
        
        if not misc.check_key(user_pwd, input_pwd):
        # verifica se a senha do user corresponde à hash
            alert_msge = 'A senha está incorreta. Tente novamente.'
            return render_template(
                'pages/login.html', 
                alert_msge=alert_msge
            )

        # get dados do user
        user_data = UserUtils.get_user_data(input_login)
        if user_data is not None:
            user_id = user_data[0]    # id
            user_nome = user_data[1]  # nome
            user_snome = user_data[2] # sobrenome
            user_role = user_data[3]  # privilegios

        try:
            # pega as inicias do user
            UserUtils.get_user_initials(user_nome, user_snome)

        except Exception as e:
            print(e)
            
        finally:
            session['id_user'] = user_id      # id
            session['user_grant'] = user_role # privilegios
            session['logged_in'] = True       # logado
            
            # grava log no telegram
            msg = f'[LOG-IN]\n{user_id} - {user_nome} {user_snome}\n{request.remote_addr}'
            misc.tlg_msg(msg)

            # senha temporária
            input_pwd = '12345'

            # verifica se a senha inserida é a senha temporária
            if not misc.check_key(user_pwd, input_pwd): 
                if debug == False:
                # if ult_acesso:
                    UserUtils.set_ult_acesso(user_id)
                    
                next_url = session.get('next_url')
                if next_url:
                    return redirect(next_url)
                # else:
                return redirect(url_for('index'))

            else:
            # se a senha é temporária...
                alert_type = 'REDEFINIR (SENHA)'
                alert_msge = 'Você deve definir sua senha no seu primeiro acesso.'
                alert_more = '/users/reset-password'
                url_return = 'Digite sua nova senha...'

                UserUtils.set_ult_acesso(user_id)

                return render_template(
                    'components/menus/alert-input.html', 
                    alert_type=alert_type,
                    alert_msge=alert_msge,
                    alert_more=alert_more,
                    url_return=url_return
                ) 


# ROTA DE SAÍDA DO USUÁRIO
@app.route('/logout/')
def logout() -> Response:
    session.clear()
    return redirect(url_for('login'))


# ROTA DE ALTERAÇÃO DE SENHA
@app.route('/change-password/', methods=['GET', 'POST'])
def change_password() -> str | Response:
    if request.method == 'GET':
        alert_type = 'QUAL A SENHA ATUAL?'
        alert_msge = 'Primeiramente, informe sua senha.'
        alert_more = '/change-password'
        url_return = 'Informe sua senha atual...'
        return render_template(
            'components/menus/alert-input.html', 
            alert_type=alert_type,
            alert_msge=alert_msge,
            alert_more=alert_more,
            url_return=url_return
        )
    else:
        user_id = session.get('id_user')
        password = request.form['input']
        if user_id and misc.password_check(user_id, password):
            alert_type = 'REDEFINIR (SENHA)'
            alert_msge = 'A senha deve ter no mínimo 6 caracteres.'
            alert_more = '/users/reset-password'
            url_return = 'Digite sua nova senha...'
            return render_template(
                'components/menus/alert-input.html', 
                alert_type=alert_type,
                alert_msge=alert_msge,
                alert_more=alert_more,
                url_return=url_return
            )
        else:
            return redirect(url_for('change_password'))


@app.route('/users/reset-password/', methods=['POST'])
@cde.verify_auth('CDE001')
def reset_password() -> Response:
    id_user = session.get('id_user')
    password = request.form['input']

    UserUtils.set_password(id_user, password)

    return redirect(url_for('index'))


@app.route('/users/redefine-password/<int:id_user>/')
@cde.verify_auth('CDE001')
def redefine_password(id_user) -> Response:
    password = '12345'

    UserUtils.set_password(id_user, password)

    return redirect(url_for('index'))


@app.route('/get/item/', methods=['POST'])
@cde.verify_auth('CDE001')
def get_item() -> Response:
    input_code = request.form['input_code'].strip()
    result_json = ProdutoUtils.get_item_json(input_code)
    
    return result_json


# ROTA DE MOVIMENTAÇÃO NO ESTOQUE (/mov)
@app.route('/mov/')
@cde.verify_auth('MOV002')
def mov() -> str:
    result = EstoqueUtils.get_address_lote()

    return render_template(
        'pages/mov/mov.html', 
        saldo_atual=result
    )


@app.route('/mov/historico/')
@cde.verify_auth('MOV003')
def historico() -> str:
    page = request.args.get('page', 1, type=int)
    per_page = 20
    estoque, row_count = HistoricoUtils.get_historico(page, per_page)
    total_pages = ceil(row_count / per_page)

    return render_template(
        'pages/mov/mov-historico.html', 
        estoque=estoque, page=page, 
        total_pages=total_pages, max=max, min=min, 
        row_count=row_count
    )


@app.route('/mov/historico/search/', methods=['GET', 'POST'])
@cde.verify_auth('MOV003')
def historico_search() -> str:
    if request.method == 'POST':
        search_term = request.form.get('search_term', '').strip()
        search_index = request.form.get('search_index', '').strip()

        option_texts = {
            'cod_item': 'Item (Código)',
            'desc_item': 'Item (Descrição)',
            'endereco': 'Endereço',
            'operacao': 'Operação (Descrição)',
            'quantidade': 'Quantidade',
            'cod_lote': 'Lote (Código)',
            'user_name': 'Usuário (Nome)',
            'timestamp': 'Horário (Data/Hora)',
        }

        if not search_term or search_index not in option_texts:
            return render_template(
                'pages/mov/mov-historico.html', 
                estoque=[], 
                search_term=search_term, 
                search_row_text="Invalid search",
                page=0, 
                total_pages=0
            )

        search_row_text = option_texts[search_index]
        estoque = HistoricoUtils.get_all_historico()

        # Filtra resultados
        filtered_estoque = [
            item for item in estoque if search_term.lower() in item.get(search_index, '').lower()
        ]

        return render_template(
            'pages/mov/mov-historico.html', 
            estoque=filtered_estoque, 
            search_term=search_term, 
            page = 0, max=max, min=min, 
            total_pages=0,
            search_row_text=search_row_text
        )

    # GET retorna ao histórico padrão
    return historico()


@app.route('/mov/carga/faturado/')
@cde.verify_auth('MOV005')
def faturado() -> str:
    saldo_atual = EstoqueUtils.get_address_lote_fat()

    return render_template(
        'pages/mov/mov-faturado.html', 
        saldo_atual=saldo_atual
    )


# ROTA DE MOVIENTAÇÃO NO ESTOQUE (/mov/MOVING)
@app.route('/mov/moving/', methods=['POST'])
@cde.verify_auth('MOV002')
def moving() -> str | Response:
    try:
    # tenta acessar dados cruciais do formulário
        numero   = int(request.form['end_number'])
        letra    = str(request.form['end_letra'])
        operacao = str(request.form['operacao'])
        
    except Exception as e:
    # parametros de entrada inválidos 
        print(f'  | ERRO: {e}')
        alert_type = 'OPERAÇÃO CANCELADA'
        alert_msge = 'Os parâmetros de entrada são INVÁLIDOS.'
        alert_more = ('''
            POSSÍVEIS SOLUÇÕES:
            • Verifique se está movimentando o item correspondente.
            • Verifique a quantidade de movimentação.
            • Verifique a operação selecionada. 
        ''')
        
        return render_template(
            'components/menus/alert.html', 
            alert_type=alert_type,
            alert_msge=alert_msge,
            alert_more=alert_more, 
            url_return=url_for('mov')
        )
        
    is_end_completo = bool(request.form.get('is_end_completo'))
    id_carga        = str(request.form.get('id_carga', 0))
    id_request      = str(request.form.get('id_req', 0))

    timestamp_br    = datetime.now(timezone(timedelta(hours=-3)))
    timestamp_out   = timestamp_br.strftime('%Y/%m/%d %H:%M:%S')
    timestamp_in    = (timestamp_br + timedelta(seconds=1)).strftime('%Y/%m/%d %H:%M:%S')

    print(f'  | OPERAÇÃO: {operacao}')

    if is_end_completo:
    # se o modo for movimetação de endereço completo,
    # seleciona todos os itens de registro positivo
        items = HistoricoUtils.select_rua(letra, numero)
        
        print(f'  | ENDEREÇO COMPLETO ({letra}.{numero}): {items}')

    else:
    # seleção padrao de item no endereço
        cod_item   = str(request.form['cod_item'])
        lote_item  = str(request.form['cod_lote'])
        quantidade = int(request.form['quantidade'])
        items      = [(cod_item, lote_item, quantidade)]
        
        print(f'  | ITEM ÚNICO ({letra}.{numero}): {items}')

        saldo_item  = int(EstoqueUtils.get_saldo_item(numero, letra, cod_item, lote_item))
        if operacao in ('S', 'T', 'F') and quantidade > saldo_item:
        # impossibilita estoque negativo
            alert_type = 'OPERAÇÃO CANCELADA'
            alert_msge = 'O saldo do item selecionado é INSUFICIENTE.'
            alert_more = ('''
                POSSÍVEIS SOLUÇÕES:
                • Verifique se está movimentando o item correspondente.
                • Verifique a quantidade de movimentação.
                • Verifique a operação selecionada. 
            ''')
            
            return render_template(
                'components/menus/alert.html', 
                alert_type=alert_type,
                alert_msge=alert_msge,
                alert_more=alert_more, 
                url_return=url_for('mov')
            )

    if operacao == 'T':
    # transferência
        destino_letter = str(request.form['destino_end_letra'])
        destino_number = int(request.form['destino_end_number'])

        if items:
            for item in items:
                cod_item, lote_item, quantidade = item
                if quantidade > 0:
                    # SAÍDA DO ENDEREÇO DE ORIGEM
                    mov_ts = HistoricoUtils.insert_historico(
                        numero=numero, letra=letra, 
                        cod_item=cod_item, lote_item=lote_item,
                        quantidade=quantidade, operacao='TS', # transferencia saida
                        timestamp=timestamp_out, 
                        id_carga=id_carga
                    )
                    # ENTRADA NO ENDEREÇO DE DESTINO
                    mov_te = HistoricoUtils.insert_historico(
                        numero=destino_number, letra=destino_letter, 
                        cod_item=cod_item, lote_item=lote_item,
                        quantidade=quantidade, operacao='TE', # transferencia entrada 
                        timestamp=timestamp_in, 
                        id_carga=id_carga
                    )
                    # verifica se operação foi realizada corretamente
                    sucesso = mov_ts and mov_te
                    if sucesso:
                        print(f'  | {letra}.{numero} >> {destino_letter}.{destino_number}: ', cod_item, lote_item, quantidade)
                    else:
                        print(f'  | ERRO AO MOVIMENTAR: {letra}.{numero} ({mov_ts}) >> {destino_letter}.{destino_number} ({mov_te}): ', cod_item, lote_item, quantidade)
        
    elif operacao == 'F':
    # faturamento
        if items: # se items foi definido (cod_item, cod_lote, quantidade)
            for item in items:
                cod_item, lote_item, quantidade = item
                if quantidade > 0:
                    sucesso = HistoricoUtils.insert_historico(
                        numero=numero, letra=letra, 
                        cod_item=cod_item, lote_item=lote_item,
                        quantidade=quantidade, operacao=operacao, 
                        timestamp=timestamp_out, 
                        id_carga=id_carga
                    )
                    if sucesso:
                        print(f'  | {letra}.{numero}: ', cod_item, lote_item, quantidade)
                    else:
                        print(f'  | ERRO AO MOVIMENTAR: {letra}.{numero}: ', cod_item, lote_item, quantidade)

    elif operacao == 'E' or operacao == 'S':
    # operacao padrao (entrada 'E' ou saída 'S')
        sucesso = HistoricoUtils.insert_historico(
            numero=numero, letra=letra, 
            cod_item=cod_item, lote_item=lote_item,
            quantidade=quantidade, operacao=operacao, 
            timestamp=timestamp_out, 
            id_carga=id_carga
        )
        if sucesso:
            print(f'  | {letra}.{numero}: ', cod_item, lote_item, quantidade)
        else:
            print(f'  | ERRO AO MOVIMENTAR: {letra}.{numero}: ', cod_item, lote_item, quantidade)
    
    else:
    # operacao invalida
        print(f'[ERRO] {letra}.{numero}: ', cod_item, lote_item, quantidade, f': OPERAÇÃO INVÁLIDA ({operacao})')

    return redirect(url_for('mov'))


@app.route('/mov/map/')
@cde.verify_auth('MOV008')
def stock_map() -> str:
    if debug:
        return render_template(
            'pages/stock-map.html'
        )
    return force_503()


@app.route('/mov/request/moving/bulk/', methods=['POST'])
@cde.verify_auth('MOV007')
def moving_req_bulk():
    sep_carga     = request.json
    timestamp_br  = datetime.now(timezone(timedelta(hours=-3)))
    timestamp_out = timestamp_br.strftime('%Y/%m/%d %H:%M:%S')
    
    try:
        for item in sep_carga:
            # VERIFICA SE O ITEM E LOTE (NO ENDEREÇO) AINDA TEM ESTOQUE SUFICIENTE
            haveItem = EstoqueUtils.get_saldo_item(
                item['rua_numero'],
                item['rua_letra'],
                item['cod_item'],
                item['lote_item']
            )
            if haveItem < item['qtde_sep']:
                return jsonify({'success': False, 'error': f'Estoque insuficiente para o item {item["cod_item"]} no lote {item["lote_item"]}.'}), 400
        
        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            for item in sep_carga:
                HistoricoUtils.insert_historico(
                    timestamp=timestamp_out,
                    numero=item['rua_numero'],
                    letra=item['rua_letra'],
                    cod_item=item['cod_item'],
                    lote_item=item['lote_item'],
                    quantidade=item['qtde_sep'],
                    id_request=item['nroreq'],
                    operacao='S'
                )
            connection.commit()
        return jsonify({'success': True})
    except Exception as e:
        print(f'[ERRO] Erro ao inserir histórico: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/mov/carga/moving/bulk/', methods=['POST'])
@cde.verify_auth('MOV002')
def moving_carga_bulk():
    sep_carga     = request.json
    timestamp_br  = datetime.now(timezone(timedelta(hours=-3)))
    timestamp_out = timestamp_br.strftime('%Y/%m/%d %H:%M:%S')
    timestamp_in  = (timestamp_br + timedelta(seconds=1)).strftime('%Y/%m/%d %H:%M:%S')
    
    try:
        for item in sep_carga:
            # Define o valor padrão 'F' para 'operacao' caso não esteja presente
            operacao = item.get('operacao', 'F')

            # Verifica a quantidade em estoque
            haveItem = EstoqueUtils.get_saldo_item(
                item['rua_numero'],
                item['rua_letra'],
                item['cod_item'],
                item['lote_item']
            )
            if haveItem < item['qtde_sep']:
                return jsonify({'success': False, 'error': f'Estoque insuficiente para o item {item["cod_item"]} no lote {item["lote_item"]}.'}), 400

            # Logica para inserir histórico de acordo com a operação
            if operacao == 'F':
                HistoricoUtils.insert_historico(
                    timestamp=timestamp_out,
                    numero=item['rua_numero'],
                    letra=item['rua_letra'],
                    cod_item=item['cod_item'],
                    lote_item=item['lote_item'],
                    quantidade=item['qtde_sep'],
                    id_carga=item['nrocarga'],
                    operacao=operacao
                )
            elif operacao == 'S':
                HistoricoUtils.insert_historico(
                    timestamp=timestamp_out,
                    numero=item['rua_numero'],
                    letra=item['rua_letra'],
                    cod_item=item['cod_item'],
                    lote_item=item['lote_item'],
                    quantidade=item['qtde_sep'],
                    operacao=operacao
                )
            elif operacao == 'T':
                # Operação de transferência
                HistoricoUtils.insert_historico(
                    timestamp=timestamp_out,
                    numero=item['rua_numero'],
                    letra=item['rua_letra'],
                    cod_item=item['cod_item'],
                    lote_item=item['lote_item'],
                    quantidade=item['qtde_sep'],
                    operacao='TS'
                )
                letra_destino, numero_destino = item['endereco_destino'].split('.')
                HistoricoUtils.insert_historico(
                    timestamp=timestamp_in,
                    numero=numero_destino,
                    letra=letra_destino,
                    cod_item=item['cod_item'],
                    lote_item=item['lote_item'],
                    quantidade=item['qtde_sep'],
                    id_carga=item['nrocarga'],
                    operacao='TE'
                )

        return jsonify({'success': True})
    except Exception as e:
        print(f'[ERRO] Erro ao inserir histórico: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/get/stock_items/')
@cde.verify_auth('MOV002')
def get_stock_items() -> str:
    result = EstoqueUtils.get_address_lote()

    return jsonify(result)


@app.route('/get/clientes/', methods=['GET'])
@cde.verify_auth('CDE001')
def get_fant_clientes() -> Response:
    query = '''
        SELECT FANTASIA
        FROM DB2ADMIN.CLIENTE;
    '''

    dsn = cde.get_unit()
    result, columns = cde.db_query(query, dsn)

    clientes = [{'FANTASIA': '(indefinido)'}]
    if result:
        for row in result:
            cliente = {columns[i]: row[i] for i in range(len(columns))}
            clientes.append(cliente)
        alert = f'Última atualização em: {datetime.now().strftime("%d/%m/%Y às %H:%M")}'
        class_alert = 'success'
    else:
        alert = 'Nenhum cliente encontrado.'
        class_alert = 'error'

    response = {
        'clientes': clientes,
        'alert': alert,
        'class_alert': class_alert
    }

    return jsonify(response)


@app.route('/mov/carga/incompleta/', methods=['GET'])
@cde.verify_auth('MOV006')
def carga_incomp():
    result, columns = CargaUtils.get_carga_incomp()
    carga_list = CargaUtils.listed_carga_incomp()
    
    return render_template(
        'pages/mov/mov-carga/mov-carga-incompleta.html',
        carga_incomp=result,
        columns=columns,
        carga_list=carga_list
    )


@app.route('/mov/carga/incompleta/<string:id_carga>/', methods=['GET'])
@cde.verify_auth('MOV006')
def carga_incomp_id(id_carga) -> str:
    id_carga = cde.split_code_seq(id_carga)[0]
    
    result, columns = CargaUtils.get_carga_incomp(id_carga)
    fant_cliente = CargaUtils.get_cliente_with_carga(id_carga)
    carga_list = CargaUtils.listed_carga_incomp()
    
    cod_item = request.args.get('cod_item', '')
    qtde_solic = request.args.get('qtde_solic', '')
    
    if columns:
        # cria lista dos itens da carga (p/ validação de necessidade no jinja)
        cod_item_list = []
        for row in result:
            cod_item_list.append(row[columns.index('cod_item')])
        
        alert = f'Última atualização em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}'
        class_alert = 'success'
    else:
        alert = f'{result[0][0]}'
        class_alert = 'error'
    
    if cod_item:
        result_local, columns_local = EstoqueUtils.estoque_address_with_item(cod_item)
    else:
        result_local, columns_local = [], []
    
    return render_template(
        'pages/mov/mov-carga/mov-carga-incompleta.html',
        alert=alert, class_alert=class_alert,
        carga_incomp=result,
        columns=columns,
        carga_list=carga_list,
        id_carga=id_carga,
        fant_cliente=fant_cliente,
        cod_item=cod_item,
        qtde_solic=qtde_solic,
        result_local=result_local,
        columns_local=columns_local,
        cod_item_list=cod_item_list
    )


@app.route('/api/insert_carga_incomp/', methods=['POST'])
@cde.verify_auth('MOV006')
def api_insert_carga_incomp() -> Response:
    data = request.get_json()
    id_carga = data.get('id_carga')
    cod_item = data.get('cod_item')
    qtde_atual = data.get('qtde_atual')
    qtde_solic = data.get('qtde_solic')
    
    try:
        CargaUtils.insert_carga_incomp(id_carga, cod_item, qtde_atual, qtde_solic)
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, error=str(e))


@app.route('/get/itens_carga_incomp/<string:id_carga>/', methods=['GET'])
@cde.verify_auth('MOV006')
def route_get_carga_incomp(id_carga) -> Response:
    id_carga = cde.split_code_seq(id_carga)[0]
    
    pending_items = CargaUtils.get_carga_incomp(id_carga)[0] #index 0 para pegar o result
    return jsonify(
        {
            'items': pending_items
            # items = {
            #   id_carga, i.cod_item,
            #   desc_item, qtde_atual,
            #   qtde_solic   
            # }
        }
    )


@app.route('/api/conclude-carga/<string:id_carga>/', methods=['POST'])
@cde.verify_auth('MOV006')
def conclude_carga(id_carga) -> Response:
    try:
        CargaUtils.excluir_carga(id_carga)
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, error=str(e))


@app.route('/api/conclude-incomp/<string:id_carga>/', methods=['POST'])
@cde.verify_auth('MOV006')
def conclude_incomp(id_carga) -> Response:
    try:
        CargaUtils.conclude_carga_incomp(id_carga)
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, error=str(e))


@app.route('/envase/', methods=['GET'])
@cde.verify_auth('ENV006')
def envase() -> str:
    envase_list = Schedule.EnvaseUtils.get_envase()

    return render_template(
        'pages/envase/envase.html', 
        envase=envase_list
    )


@app.route('/envase/calendar/')
@cde.verify_auth('ENV008')
def calendar_envase() -> str:
    envase_list = Schedule.EnvaseUtils.get_envase()
    return render_template(
        'pages/envase/envase-calendar.html', 
        envase=envase_list
    )


@app.route('/envase/delete/<id_envase>/')
@cde.verify_auth('ENV007')
def delete_envase(id_envase) -> Response:
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute('''
            DELETE 
            FROM prog_envase
            WHERE id_envase = ?;
        ''', 
        (id_envase,))

    return redirect(url_for('envase'))


@app.route('/envase/done/<id_envase>/')
@cde.verify_auth('ENV006')
def conclude_envase(id_envase) -> Response:
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute('''
            UPDATE prog_envase
            SET flag_concluido = TRUE
            WHERE id_envase = ?;
        ''',
        (id_envase,))

    return redirect(url_for('envase'))


@app.route('/envase/pending/<id_envase>/')
@cde.verify_auth('ENV007')
def set_pending_envase(id_envase) -> Response:
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute('''
            UPDATE prog_envase
            SET flag_concluido = false
            WHERE id_envase = ?;
        ''',
        (id_envase,))

    return redirect(url_for('envase'))


@app.route('/envase/edit/', methods=['GET', 'POST'])
@cde.verify_auth('ENV007')
def edit_envase() -> Response | str:
    # TODO: criar função auxiliar
    if request.method == 'POST':

        req_id_envase   = request.form['id_envase']
        quantidade      = request.form['quantidade']
        data_entr_antec = request.form['data_antec']
        data_envase     = request.form['data_envase']
        observacao      = re.sub(r'\r\n|\r|\n|<br>', ' ', request.form['observacao']).upper()

        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            cursor.execute('''
                UPDATE prog_envase
                SET qtde_solic      = ?,
                    data_entr_antec = ?,
                    data_envase     = ?,
                    observacao      = ?
                WHERE id_envase     = ?;
            ''',
            (quantidade, data_entr_antec, data_envase, observacao, req_id_envase))

        return redirect(url_for('envase'))
    else:
        req_id_envase = request.args.get('id_envase')

        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            cursor.execute('''
                SELECT  p.cod_linha, c.fantasia_cliente, i.cod_item,
                        i.desc_item, p.qtde_solic, p.data_entr_antec,
                        p.data_envase, p.observacao, p.id_envase,
                        p.flag_concluido
                FROM prog_envase p
                JOIN itens i ON p.cod_item = i.cod_item
                JOIN clientes c ON p.cod_cliente = c.cod_cliente
                WHERE id_envase = ?;
            ''',
            (req_id_envase,))

            env_edit = [{
                'linha'         : row[0], 'fantasia_cliente': row[1], 'cod_item'       : row[2],
                'desc_item'     : row[3], 'quantidade'      : row[4], 'data_entr_antec': row[5],
                'data_envase'   : row[6], 'observacao'      : row[7], 'id_envase'      : row[8],
                'flag_concluido': row[9]
            } for row in cursor.fetchall()]

        return render_template(
            'pages/envase/envase-edit.html', 
            env_edit=env_edit
        )


@app.route('/envase/insert/', methods=['POST'])
@cde.verify_auth('ENV006')
def insert_envase() -> Response:
    # TODO: criar função auxiliar
    if request.method == 'POST':
        linha           = request.form['linha']
        cod_item        = request.form['codinterno']
        quantidade      = request.form['quantidade']
        data_entr_antec = request.form['data_antec']
        data_envase     = request.form['data_envase']
        cliente         = request.form['cliente']
        observacao      = re.sub(r'\r\n|\r|\n|<br>', ' ', request.form['observacao']).upper()

        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            cursor.execute('''
                SELECT cod_cliente
                FROM clientes
                WHERE fantasia_cliente = ?;
            ''', 
            (cliente,))

            row = cursor.fetchone()
            cod_cliente = row[0] if row else None

        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            cursor.execute('''
                INSERT INTO prog_envase (
                    cod_linha, cod_cliente, cod_item,
                    qtde_solic, data_entr_antec, data_envase,
                    observacao, flag_concluido 
                )
                VALUES (
                    ?, ?, ?,
                    ?, ?, ?,
                    ?, false 
                );
            ''',
            (linha, cod_cliente, cod_item, 
             quantidade, data_entr_antec, data_envase,
             observacao))
            
            connection.commit()
    return redirect(url_for('envase'))


@app.route('/processamento/', methods=['GET'])
@cde.verify_auth('PRC010')
def producao() -> str:
    id_user = session.get('id_user')
    user_perm = UserUtils.get_user_permissions(id_user)
    user_perm = [item['id_perm'] for item in user_perm]
    producao_list = Schedule.ProcessamentoUtils.get_producao()
    
    return render_template(
        'pages/processamento/processamento.html', 
        producao=producao_list, 
        user_perm=user_perm
    )


@app.route('/processamento/calendar/')
@cde.verify_auth('PRC012')
def calendar_producao() -> str:
    producao_list =  Schedule.ProcessamentoUtils.get_producao()

    return render_template(
        'pages/processamento/processamento-calendar.html', 
        producao=producao_list
    )


@app.route('/processamento/delete/<id_producao>/')
@cde.verify_auth('PRC011')
def delete_producao(id_producao) -> Response:
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute('''
            DELETE 
            FROM prog_producao 
            WHERE id_producao = ?;
        ''', 
        (id_producao,))

    return redirect(url_for('producao'))


@app.route('/processamento/done/<id_producao>/')
@cde.verify_auth('PRC010')
def conclude_producao(id_producao) -> Response:
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute('''
            UPDATE prog_producao
            SET flag_concluido = true
            WHERE id_producao = ?;
        ''', 
        (id_producao,))
        
    return redirect(url_for('producao'))


@app.route('/processamento/pending/<id_producao>/')
@cde.verify_auth('PRC011')
def set_pending_producao(id_producao) -> Response:
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute('''
            UPDATE prog_producao
            SET flag_concluido = false
            WHERE id_producao = ?;
        ''',
        (id_producao,))

    return redirect(url_for('producao'))


@app.route('/processamento/edit/', methods=['GET', 'POST'])
@cde.verify_auth('PRC011')
def edit_producao() -> Response | str:
    id_user = session.get('id_user')
    user_perm = UserUtils.get_user_permissions(id_user)
    user_perm = [item['id_perm'] for item in user_perm]

    if request.method == 'POST':
        req_id_producao = request.form['id_producao']
        litros          = request.form['litros']
        data_entr_antec = request.form['data_antec']
        data_producao   = request.form['data_producao']
        observacao      = re.sub(r'\r\n|\r|\n|<br>', ' ', request.form['observacao']).upper()

        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            cursor.execute('''
                UPDATE prog_producao
                SET lts_solic       = ?,
                    data_entr_antec = ?,
                    data_producao   = ?,
                    observacao      = ?
                WHERE id_producao   = ?;
            ''',
            (litros, data_entr_antec, data_producao, observacao, req_id_producao)
        )
            
        return redirect(url_for('producao'))
    else:
        req_id_producao = request.args.get('id_producao')
        # se possui id_producao, puxa apenas uma produção
        if req_id_producao:
            mode = 'singleRow'
            with sqlite3.connect(db_path) as connection:
                cursor = connection.cursor()
                cursor.execute('''
                    SELECT  p.cod_linha, p.liq_linha, p.liq_cor, p.embalagem,
                            p.lts_solic, p.data_entr_antec, p.data_producao,
                            p.observacao, p.id_producao, p.flag_concluido,
                            p.liq_tipo
                    FROM prog_producao p
                    WHERE ? = p.id_producao
                    ORDER BY p.data_producao;
                ''', 
                (req_id_producao,))

                prod_edit = [{
                    'linha'         : row[0], 'liq_linha' : row[1], 'liq_cor'        : row[2],
                    'embalagem'     : row[3], 'litros'    : row[4], 'data_entr_antec': row[5],
                    'data_producao' : row[6], 'observacao': row[7], 'id_producao'    : row[8],
                    'flag_concluido': row[9], 'liq_tipo'  : row[10]
                } for row in cursor.fetchall()]

        else:
            mode = 'onlyConcluded'
            prod_edit =  Schedule.ProcessamentoUtils.get_producao()

        return render_template(
            'pages/processamento/processamento-edit.html', 
            prod_edit=prod_edit, 
            user_perm=user_perm, 
            mode=mode
        )


@app.route('/processamento/insert/', methods=['POST'])
@cde.verify_auth('PRC010')
def insert_producao() -> Response:
    if request.method == 'POST':
        linha           = request.form['linha']
        liq_tipo        = request.form['liq_tipo']
        liq_linha       = request.form['liq_linha']
        liq_cor         = request.form['liq_cor']
        embalagem       = request.form['embalagem']
        litros          = request.form['litros']
        data_entr_antec = request.form['data_antec']
        data_producao   = request.form['data_producao']
        observacao      = re.sub(r'\r\n|\r|\n|<br>', ' ', request.form['observacao']).upper()

        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            cursor.execute(''' 
                INSERT INTO prog_producao (  
                    cod_linha, liq_linha, liq_cor,
                    embalagem, lts_solic, data_entr_antec,
                    data_producao, observacao, liq_tipo, 
                    flag_concluido ) 
                VALUES (
                    ?, ?, ?,
                    ?, ?, ?,
                    ?, ?, ?,
                    false );
                ''',
                (linha, liq_linha, liq_cor,
                 embalagem, litros, data_entr_antec,
                 data_producao, observacao, liq_tipo))
            
            connection.commit()

    return redirect(url_for('producao'))


@app.route('/about/')
@cde.verify_auth('CDE001')
def about() -> str:
    return render_template(
        'pages/about.html',
        about=True
    )


@app.route('/users/edit/', methods=['POST', 'GET'])
@cde.verify_auth('CDE016')
def users_edit() -> str | None:
    req_id_user = request.args.get('id_user')
    if request.method == 'GET':
        user_perm = UserUtils.get_user_permissions(req_id_user)
        permissions = UserUtils.get_permissions()
        return render_template(
            'pages/users/users-edit.html', 
            user_perm=user_perm,
            permissions=permissions, 
            req_id_user=req_id_user,
            user_data=UserUtils.get_userdata(req_id_user)
        )
    else:
        return None


@app.route('/users/remove-perm/<int:id_user>/<string:id_perm>/', methods=['GET', 'POST'])
@cde.verify_auth('CDE016')
def remove_permission(id_user, id_perm) -> Response:
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute('''
            DELETE FROM user_permissions 
            WHERE id_user = ? 
            AND   id_perm = ?;
        ''', 
        (id_user, id_perm))

        connection.commit()

    return redirect(url_for('users_edit', id_user=id_user))


@app.route('/users/add-perm/<int:id_user>/<string:id_perm>/', methods=['GET', 'POST'])
@cde.verify_auth('CDE016')
def add_permission(id_user, id_perm) -> Response:
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute('''
            INSERT INTO user_permissions (
                id_user, id_perm 
            ) 
            VALUES (
                ?, ? 
            );
        ''', 
        (id_user, id_perm))

        connection.commit()

    return redirect(url_for('users_edit', id_user=id_user))


@app.route('/users/inserting/', methods=['POST'])
@cde.verify_auth('CDE016')
def cadastrar_usuario() -> Response | str:
    if request.method == 'POST':
        login_user     = str(request.form['login_user'])
        nome_user      = str(request.form['nome_user'])
        sobrenome_user = str(request.form['sobrenome_user'])
        privilege_user = int(request.form['privilege_user'])
        data_cadastro  = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        password_user  = misc.hash_key(str(12345))

        try:
            with sqlite3.connect(db_path) as connection:
                cursor = connection.cursor()
                
                cursor.execute('''
                    INSERT INTO users (
                        login_user, password_user, 
                        nome_user, sobrenome_user, 
                        privilege_user, data_cadastro 
                    ) VALUES (
                        ?, ?, ?,
                        ?, ?, ? 
                    );
                ''',
                (login_user, password_user, nome_user,
                 sobrenome_user, privilege_user, data_cadastro))

                cursor.execute('''
                    SELECT id_user 
                    FROM users 
                    ORDER BY id_user DESC 
                    LIMIT 1;
                ''')
                id_user_row = cursor.fetchone()

                if id_user_row:
                    id_user = id_user_row[0]

                    cursor.execute('''
                        INSERT INTO user_permissions (
                            id_user, id_perm 
                        )
                        VALUES (
                            ?, ? 
                        );
                    ''',
                    (id_user, 'CDE001'))
                    connection.commit()
                    user_name = session.get('user_name')
                    id_user   = session.get('id_user')

                    msg = \
                    f'[CADASTRO]\n{request.remote_addr}\n{id_user} - {user_name} [+] {nome_user} {sobrenome_user} ({privilege_user})'
                    misc.tlg_msg(msg)

        except sqlite3.IntegrityError as e:
            if 'UNIQUE constraint failed' in str(e):
                alert_type = 'CADASTRO (USUÁRIO)'
                alert_msge = 'Não foi possível criar usuário...'
                alert_more = 'MOTIVO:\n• Já existe um usuário com este login.'
                
                return render_template(
                    'components/menus/alert.html', 
                    alert_type=alert_type,
                    alert_msge=alert_msge,
                    alert_more=alert_more, 
                    url_return=url_for('users')
                )
                
            else:
                alert_type = 'CADASTRO (USUÁRIO)'
                alert_msge = 'Não foi possível criar usuário...'
                alert_more = f'DESCRIÇÃO DO ERRO:\n• {e}.'
                
                return render_template(
                    'components/menus/alert.html', 
                    alert_type=alert_type,
                    alert_msge=alert_msge, 
                    alert_more=alert_more, 
                    url_return=url_for('users')
                )
                
        else:
            return redirect(url_for('users'))
    return render_template('pages/users/users.html')


@app.route('/mov/carga/<string:id_carga>/', methods=['GET', 'POST'])
@cde.verify_auth('MOV006')
def carga_id(id_carga) -> str:
    result_local, columns_local = [], []
    
    if request.method == 'GET':
        cod_item = request.args.get('cod_item', '')
        qtde_solic = request.args.get('qtde_solic', '')
        
        if cod_item:
            result_local, columns_local = EstoqueUtils.estoque_address_with_item(cod_item)

        # extrai o primeiro elemento de `id_carga`
        id_carga = cde.split_code_seq(id_carga)[0]
        
        fant_cliente = CargaUtils.get_cliente_with_carga(id_carga)
        all_cargas = CargaUtils.get_cargas_finalizadas()
        
        # sanitiza a lista all_cargas para garantir que contenha apenas inteiros
        cargas_except_query = ', '.join(str(int(carga)) for carga in all_cargas if isinstance(carga, int))

        query = f'''
            SELECT DISTINCT 
                icrg.CODIGO_GRUPOPED                  AS NRO_CARGA,
                icrg.NRO_PEDIDO                       AS NRO_PEDIDO,
                (iped.NRO_PEDIDO || '.' || iped.SEQ)  AS NROPED_SEQ,
                CAST(iped.ITEM AS VARCHAR(255))       AS COD_ITEM,
                i.ITEM_DESCRICAO                      AS DESC_ITEM,
                CAST(iped.QTDE_SOLICITADA AS INTEGER) AS QTDE_SOLIC,
                crg.OBSERVACAO                        AS OBS_CARGA
                
            FROM DB2ADMIN.ITEMPED iped

            JOIN DB2ADMIN.IGRUPOPE icrg
            ON icrg.NRO_PEDIDO = iped.NRO_PEDIDO
            AND icrg.SEQ = iped.SEQ

            JOIN DB2ADMIN.HUGO_PIETRO_VIEW_ITEM i 
            ON i.ITEM = iped.ITEM
            
            JOIN DB2ADMIN.GRUPOPED crg
            ON icrg.CODIGO_GRUPOPED = crg.CODIGO_GRUPOPED

            WHERE icrg.CODIGO_GRUPOPED = {id_carga}
            AND icrg.CODIGO_GRUPOPED NOT IN ({cargas_except_query})

            ORDER BY COD_ITEM

            LIMIT 100;
        '''

        # executa a consulta de forma segura
        dsn = cde.get_unit()
        result, columns = cde.db_query(query, dsn)
        
        if columns:
            # cria lista dos itens da carga (p/ validação de necessidade no jinja)
            cod_item_list = [row[columns.index('COD_ITEM')] for row in result]
            alert = f'Última atualização em: {datetime.now().strftime("%d/%m/%Y às %H:%M")}'
            class_alert = 'success'
        else:
            cod_item_list = []
            alert = f'{result[0][0]}' if result else 'Nenhum resultado encontrado.'
            class_alert = 'error'

        return render_template(
            'pages/mov/mov-carga/mov-carga.html',
            result=result, columns=columns, alert=alert,
            class_alert=class_alert, id_carga=id_carga, 
            cod_item=cod_item, qtde_solic=qtde_solic,
            result_local=result_local, columns_local=columns_local,
            fant_cliente=fant_cliente, cod_item_list=cod_item_list
        )
    
    # se não for uma requisição GET, renderiza a página com dados vazios
    result = []
    return render_template('pages/mov/mov-carga/mov-carga.html', result=result, columns=[])
 

@app.route('/mov/carga/', methods=['GET', 'POST'])
@cde.verify_auth('MOV006')
def cargas() -> str:
    if request.method == 'POST':
        all_cargas = CargaUtils.get_cargas_finalizadas()
        
        result, columns = CargaUtils.get_cargas(all_cargas)
        
        if columns:
            alert = f'Última atualização em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}'
            class_alert = 'success'

        else:
            alert = f'{result[0][0]}'
            class_alert = 'error'
        return render_template(
            'pages/mov/mov-carga/mov-carga.html',
            result=result, columns=columns,
            alert=alert, class_alert=class_alert
        )
    result = []
    return render_template(
        'pages/mov/mov-carga/mov-carga.html',
        result=result
    )


@app.route('/mov/requisicao/', methods=['GET', 'POST'])
@cde.verify_auth('MOV007')
def mov_request() -> str:
    if request.method == 'POST':
        result, columns = MovRequestUtils.get_mov_request()
        
        class_alert = 'success'
        alert = 'A lista foi carregada com sucesso.'
        if len(result) == 1:
            class_alert = 'error'
            alert = result[0][0]
    
        return render_template(
            'pages/mov/mov-request/mov-request.html',
            result=result,
            columns=columns,
            alert=alert,
            class_alert=class_alert
        )
    return render_template(
        'pages/mov/mov-request/mov-request.html'
    )


@app.route('/mov/requisicao/<int:id_req>/', methods=['GET', 'POST'])
@cde.verify_auth('MOV007')
def mov_request_id(id_req) -> str:
    result_local, columns_local = [], []
    if request.method == 'GET':
        cod_item = request.args.get('cod_item', '')
        qtde_solic = request.args.get('qtde_solic', '')
        
        if cod_item:
            result_local, columns_local = EstoqueUtils.estoque_address_with_item(cod_item)

        result, columns = MovRequestUtils.get_mov_request(id_req)

        if columns:
            # cria lista dos itens da requisicao (p/ validação de necessidade no jinja)
            cod_item_list = []
            for row in result:
                cod_item_list.append(row[columns.index('COD_ITEM')])
            
            alert = f'Última atualização em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}'
            class_alert = 'success'
        else:
            alert = f'{result[0][0]}'
            class_alert = 'error'

        if len(result) == 1:
            class_alert = 'error'
            alert = result[0][0]

        return render_template(
            'pages/mov/mov-request/mov-request.html',
            id_req=id_req,
            result=result, columns=columns,
            result_local=result_local, columns_local=columns_local,
            cod_item=cod_item, qtde_solic=qtde_solic,
            class_alert=class_alert, alert=alert,
            cod_item_list=cod_item_list
        )
    return render_template(
        'pages/mov/mov-request/mov-request.html'
    )


@app.route('/mov/requisicao/separacao/p/<string:id_req>', methods=['GET', 'POST'])
@cde.verify_auth('MOV007')
def req_sep_pend(id_req) -> str:
    id_req = id_req.split('-')[0]

    id_user   = session.get('id_user')
    user_info = UserUtils.get_userdata(id_user)
    obs_carga = CargaUtils.get_obs_with_carga(id_req)
    return render_template(
        'pages/mov/mov-request/mov-request-separacao-pend.html', 
        id_req=id_req, 
        user_info=user_info,
        obs_carga=obs_carga,
        status='p' # pendente
    )


@app.route('/mov/requisicao/separacao/f/<string:id_req>', methods=['GET', 'POST'])
@cde.verify_auth('MOV007')
def req_sep_done(id_req) -> str:
    # se houver sequencia, usa, senão usa 0 (código padrao)
    if '-' in id_req:
        id_req, seq = id_req.split('-')
    else:
        seq = 0

    id_user   = session.get('id_user')
    user_info = UserUtils.get_userdata(id_user)
    obs_carga = CargaUtils.get_obs_with_carga(id_req)
    return render_template(
        'pages/mov/mov-request/mov-request-separacao-done.html', 
        id_req=id_req,
        seq=seq, 
        user_info=user_info,
        obs_carga=obs_carga,
        status='f' # finalizado
    )


@app.route('/api/req/qtde_solic/', methods=['GET'])
@cde.verify_auth('MOV007')
def get_req_qtde_solic():
    id_req = request.args.get('id_req', type=int)
    cod_item = request.args.get('cod_item', type=str)
    
    query = '''
        SELECT DISTINCT
            SUM(CAST(M.QTDE AS INTEGER)) AS QTDE_SOLIC
        FROM 
            DB2ADMIN.HUGO_PIETRO_VIEW_MOVIMENTOS M
		JOIN 
        	DB2ADMIN.HUGO_PIETRO_VIEW_ITEM I
            ON I.ITEM = M.ITEM
        WHERE 
            M.OBS LIKE '%Requisicao :%' AND 
            (
                GRUPO_DESCRICAO = 'PRODUTO ACABADO' OR 
                GRUPO_DESCRICAO = 'REVENDA'
            ) AND
            I.UNIDADE_DESCRICAO = 'CX' AND
            M.DEPOSITO = 2 AND
            TIPO_MOVIMENTO = 'S' AND
            M.DOC_ORIGEM = '{a}' AND
            I.ITEM = '{b}';
    '''.format(a=id_req, b=cod_item)
    try:
        dsn = cde.get_unit()
        result, columns = cde.db_query(query, dsn)
        if result:
            qtde_solic = result[0][0]
        else:
            qtde_solic = 0
        return jsonify({'qtde_solic': qtde_solic})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/itens_req/', methods=['GET'])
@cde.verify_auth('MOV007')
def get_itens_req():
    id_req = request.args.get('id_req', type=int)
    
    query = '''
        SELECT DISTINCT
            M.ITEM
        FROM 
            DB2ADMIN.HUGO_PIETRO_VIEW_MOVIMENTOS M
		JOIN 
        	DB2ADMIN.HUGO_PIETRO_VIEW_ITEM I
            ON I.ITEM = M.ITEM
        WHERE 
            M.OBS LIKE '%Requisicao :%' AND 
            (
                GRUPO_DESCRICAO = 'PRODUTO ACABADO' OR 
                GRUPO_DESCRICAO = 'REVENDA'
            ) AND
            I.UNIDADE_DESCRICAO = 'CX' AND
            M.DEPOSITO = 2 AND
            TIPO_MOVIMENTO = 'S' AND
            M.DOC_ORIGEM = '{a}';
    '''.format(a=id_req)
    try:
        dsn = cde.get_unit()
        result, columns = cde.db_query(query, dsn)
        if result:
            itens = [row[0] for row in result]
        else:
            itens = ['Erro: Nenhum item encontrado.']
        return jsonify({'itens': itens})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/mov/op/', methods=['GET', 'POST'])
@cde.verify_auth('MOV007')
def mov_op() -> str:
    if request.method == 'POST':
        result, columns = OrdemProducaoUtils.get_ordem_producao()
        
        class_alert = 'success'
        alert = 'A lista foi carregada com sucesso.'
        if len(result) == 1:
            class_alert = 'error'
            alert = result[0][0]
    
        return render_template(
            'pages/mov/mov-op.html',
            result=result,
            columns=columns,
            alert=alert,
            class_alert=class_alert
        )
    return render_template(
        'pages/mov/mov-op.html'
    )


@app.route('/api/carga/qtde_solic/', methods=['GET'])
@cde.verify_auth('MOV006')
def get_carga_qtde_solic():
    id_carga = request.args.get('id_carga', type=int)
    cod_item = request.args.get('cod_item', type=str)
    
    # solicita o valor inicial/máximo da quantidade solicitada
    # usado em relatórios finais
    is_total = request.args.get('is_total', type=int)
    
    if is_total != 0:
        query = '''
            SELECT DISTINCT 
                MAX(qtde_solic) AS QTDE_SOLIC
            FROM tbl_carga_incomp
            WHERE 
                id_carga = '{a}' AND
                cod_item = '{b}'
            ;
        '''.format(a=id_carga, b=cod_item)
        dsn = 'SQLITE'
        result, columns = cde.db_query(query, dsn)
    else:
        query = '''
            SELECT 
                qtde_solic AS QTDE_SOLIC
            FROM tbl_carga_incomp
            WHERE 
                id_carga = '{a}' AND
                cod_item = '{b}' AND
                flag_pendente = TRUE
            ;
        '''.format(a=id_carga, b=cod_item)
        dsn = 'SQLITE'
        result, columns = cde.db_query(query, dsn)
        
    if result != []:
        qtde_solic = result[0][0]
        return jsonify({'qtde_solic': qtde_solic})
    else:
        query = '''
            SELECT
                SUM(CAST(iped.QTDE_SOLICITADA AS INTEGER)) AS QTDE_SOLIC
            FROM DB2ADMIN.ITEMPED iped

            JOIN DB2ADMIN.IGRUPOPE icrg
            ON icrg.NRO_PEDIDO = iped.NRO_PEDIDO
            AND icrg.SEQ = iped.SEQ

            WHERE icrg.CODIGO_GRUPOPED = '{a}'
            AND iped.ITEM = '{b}';
        '''.format(a=id_carga, b=cod_item)
        try:
            dsn = cde.get_unit()
            result, columns = cde.db_query(query, dsn)
            if result:
                qtde_solic = result[0][0]
            else:
                qtde_solic = 0
            return jsonify({'qtde_solic': qtde_solic})
        except Exception as e:
            return jsonify({'error': str(e)}), 500


@app.route('/api/itens_carga/', methods=['GET'])
@cde.verify_auth('MOV006')
def get_itens_carga():
    id_carga = request.args.get('id_carga', type=int)
    
    query = '''
        SELECT DISTINCT iped.ITEM
        FROM DB2ADMIN.ITEMPED iped

        JOIN DB2ADMIN.IGRUPOPE icrg
        ON icrg.NRO_PEDIDO = iped.NRO_PEDIDO
        AND icrg.SEQ = iped.SEQ

        WHERE icrg.CODIGO_GRUPOPED = '{a}';
    '''.format(a=id_carga)
    try:
        dsn = cde.get_unit()
        result, columns = cde.db_query(query, dsn)
        if result:
            itens = [row[0] for row in result]
        else:
            itens = ['Erro: Nenhum item encontrado.']
        return jsonify({'itens': itens})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/mov/carga/separacao/p/<string:id_carga>', methods=['GET', 'POST'])
@cde.verify_auth('MOV006')
def carga_sep_pend(id_carga) -> str:
    id_carga = cde.split_code_seq(id_carga)[0]
    
    id_user   = session.get('id_user')
    user_info = UserUtils.get_userdata(id_user)
    obs_carga = CargaUtils.get_obs_with_carga(id_carga)
    fant_cliente   = CargaUtils.get_cliente_with_carga(id_carga)
    return render_template(
        'pages/mov/mov-carga/mov-carga-separacao-pend.html', 
        id_carga=id_carga, 
        user_info=user_info,
        fant_cliente=fant_cliente,
        obs_carga=obs_carga,
        status='p' # pendente
    )


@app.route('/mov/carga/separacao/f/<string:id_carga>', methods=['GET', 'POST'])
@cde.verify_auth('MOV006')
def carga_sep_done(id_carga) -> str:
    if '-' in id_carga:
        id_carga, seq = cde.split_code_seq(id_carga)
    else:
        seq = 0
    id_user      = session.get('id_user')
    user_info    = UserUtils.get_userdata(id_user)
    obs_carga    = CargaUtils.get_obs_with_carga(id_carga)
    fant_cliente = CargaUtils.get_cliente_with_carga(id_carga)
    return render_template(
        'pages/mov/mov-carga/mov-carga-separacao-done.html', 
        id_carga=id_carga,
        seq=seq, 
        user_info=user_info,
        fant_cliente=fant_cliente,
        obs_carga=obs_carga,
        status='f' # finalizado
    )


@app.route('/get/description_json/<cod_item>/', methods=['GET'])
def get_description(cod_item) -> Response:
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute('''
            SELECT i.desc_item
            FROM itens i
            WHERE i.cod_item = ?;
        ''', 
        (cod_item,))
        
        resultado = cursor.fetchone()
        if resultado is not None:
            desc_item = resultado[0]
        else:
            desc_item = 'O item não foi encontrado.'
    return jsonify({"description": desc_item})


@app.route('/get/username/<id_user>/', methods=['GET'])
def get_username_route(id_user) -> Response:
    username = UserUtils.get_username(id_user)
    return jsonify({"username": username})


@app.route('/post/save-localstorage/', methods=['POST'])
@cde.verify_auth('MOV006')
def save_localstorage():
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'Nenhum dado recebido do localStorage.'}), 400
        
        items_data = data.get('data')
        report_dir = data.get('report_dir')
        filename = data.get('filename')

        if not items_data or not filename or not report_dir:
            return jsonify({'error': 'Dados inválidos ou ausentes.'}), 400

        # verifica se o arquivo já existe
        # cria um nome com sufixo sequencial se necessário
        save_path = os.path.join(
            app.root_path,
            # exemplo: 
            # 'c:/users/user/desktop/cde/'
            f'report/{report_dir}', f'{filename}.json'
            # exemplo: 
            # 'report/cargas/separacao-carga-123.json'
        )
        seq = 1
        while os.path.exists(save_path):
            save_path = os.path.join(
                app.root_path,
                # exemplo: 
                # 'c:/users/user/desktop/cde/'
                f'report/{report_dir}', f'{filename}-{seq}.json'
                # exemplo: 
                # 'report/cargas/separacao-carga-123-1.json'
            )
            seq += 1

        with open(save_path, 'w') as file:
            json.dump(items_data, file)

        return jsonify({'message': 'Dados do localStorage foram salvos com sucesso.'}), 200

    except Exception as e:
        print(f'[ERRO] Erro ao salvar dados do localStorage: {str(e)}')
        return jsonify({'error': 'Erro interno ao salvar dados do localStorage.'}), 500
    

@app.route('/get/has_carga_at_history/<string:id_carga>/', methods=['GET'])
def has_carga_at_history(id_carga) -> Response:
    id_carga = cde.split_code_seq(id_carga)[0]
    
    has_carga_at_history = bool(CargaUtils.get_carga_incomp(id_carga)[0])
    return jsonify(
        {
            'bool': has_carga_at_history
        }
    )


@app.route('/get/carga/load-table-data/', methods=['GET'])
@cde.verify_auth('MOV006')
def get_carga_table_data():
    try:
        filename = request.args.get('filename')
        seq = request.args.get('seq', False)
        
        if not filename:
            return jsonify({'error': 'Nome do arquivo não fornecido.'}), 400

        data, num_files = CargaUtils.readJsonCargaSeq(filename, seq)
        return jsonify({'data': data, 'num_files': num_files}), 200
    
    except FileNotFoundError:
        return jsonify({'error': 'FileNotFound'}), 404
    
    except Exception as e:
        return jsonify({'error': f'Erro ao carregar dados da carga: {str(e)}'}), 500
    
    
@app.route('/get/request/load-table-data/', methods=['GET'])
@cde.verify_auth('MOV006')
def get_request_table_data():
    try:
        filename = request.args.get('filename')
        seq = request.args.get('seq', False)
        
        if not filename:
            return jsonify({'error': 'Nome do arquivo não fornecido.'}), 400

        data = MovRequestUtils.readJsonReqSeq(filename, seq)

        return jsonify(data), 200
    
    except FileNotFoundError:
        return jsonify({'error': 'Arquivo de dados da carga não encontrado.'}), 404
    
    except Exception as e:
        return jsonify({'error': f'Erro ao carregar dados da carga: {str(e)}'}), 500
    

@app.route('/get/list-all-separations/', methods=['GET', 'POST'])
@cde.verify_auth('MOV006')
def list_all_separations():
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'Nenhum dado recebido do localStorage.'}), 400

        report_dir = data.get('report_dir')

        directory = os.path.join(
            app.root_path,
            f'report/{report_dir}'
        )
        files = [f for f in os.listdir(directory) if f.endswith('.json') and len(f.split('-')) == 3]
        
        files_sorted = sorted(files, reverse=True)
        return jsonify(files_sorted), 200
    except Exception as e:
        return jsonify({'error': f'Erro ao listar arquivos: {str(e)}'}), 500


@app.route('/produtos/toggle-perm/<string:cod_item>/<int:flag>/', methods=['GET', 'POST'])
@cde.verify_auth('ITE005')
def produtos_toggle_perm(cod_item, flag) -> Response:
    ProdutoUtils.toggle_item_flag(cod_item, flag)
    return redirect(url_for('produtos_flag'))


@app.route('/produtos/status/', methods=['GET', 'POST'])
@cde.verify_auth('ITE005')
def produtos_flag() -> str:
    itens = ProdutoUtils.get_all_itens()
    
    return render_template(
        'pages/produtos-flag.html',
        itens=itens
    )


@app.route('/produtos/', methods=['GET', 'POST'])
@cde.verify_auth('ITE005')
def produtos() -> str:
    itens = ProdutoUtils.get_active_itens()
    if request.method == 'POST':
        result, columns = ProdutoUtils.get_itens_from_erp()

        if columns:
            alert = f'Última atualização em: {datetime.now().strftime("%d/%m/%Y às %H:%M")}'
            class_alert = 'success'
            with sqlite3.connect(db_path) as connection:
                cursor = connection.cursor()
                cursor.execute('BEGIN TRANSACTION;')
                
                cursor.execute('SELECT cod_item FROM itens WHERE flag_ativo = 0;')
                inactive_items = cursor.fetchall()

                cursor.execute('DELETE FROM itens;')

                cursor.executemany('''
                    INSERT INTO itens (cod_item, desc_item, dun14, flag_ativo)
                    VALUES (?,?,?,1);
                ''', [(item[0], item[1], item[2]) for item in result])

                cursor.executemany('''
                    UPDATE itens SET flag_ativo = 0 WHERE cod_item = ?;
                ''', inactive_items)

                connection.commit()
        else:
            alert = f'{result[0][0]}'
            class_alert = 'error'
        itens = ProdutoUtils.get_active_itens()
        return render_template(
            'pages/produtos.html', 
            itens=itens, 
            alert=alert, 
            class_alert=class_alert
        )
    return render_template(
        'pages/produtos.html', 
        itens=itens
    )


@app.route('/etiqueta/', methods=['GET', 'POST'])
@cde.verify_auth('OUT014')
def etiqueta() -> str:
    if request.method == 'POST':
        qr_text   = str(request.form['qr_text'])
        desc_item = str(request.form['desc_item'])
        cod_item  = str(request.form['cod_item'])
        cod_lote  = str(request.form['lote_item'])

        return EtiquetaGenerator.generate(qr_text, desc_item, cod_item, cod_lote)
    return render_template('pages/etiqueta.html', produtos=produtos)


@app.route('/rotulo/', methods=['GET', 'POST'])
@cde.verify_auth('OUT015')
def rotulo() -> Response | str:
    if request.method == 'POST':
        espessura_fita      = misc.parse_float(request.form['espessura_fita'])
        diametro_inicial    = misc.parse_float(request.form['diametro_inicial'])
        diametro_minimo     = misc.parse_float(request.form['diametro_minimo'])
        espessura_papelao   = misc.parse_float(request.form['espessura_papelao'])
        compr_rotulo        = misc.parse_float(request.form['compr_rotulo'])
        comprimento_total   = 0 # INICIALIZA
        num_voltas          = 0 # INICIALIZA

        if espessura_fita != 0:

            diametro_minimo += (espessura_papelao * 2 + 0.15)
            espessura_fita += 0.03

            while diametro_inicial > diametro_minimo:
                circunferencia_atual = pi * diametro_inicial
                comprimento_total += circunferencia_atual
                diametro_inicial -= 2 * espessura_fita
                num_voltas += 1

            if not compr_rotulo == 0:
                num_rotulos = comprimento_total / compr_rotulo
            else:
                num_rotulos = 0

            num_rotulos_str  = f"{num_rotulos:_.0f}".replace('.', ',').replace('_', '.')
            comprimento_mtrs = f"{(comprimento_total / 1000):_.2f}".replace('.', ',').replace('_', '.')

            return jsonify(
                {
                'num_rotulos_str': num_rotulos_str,
                'num_voltas': num_voltas,
                'comprimento_mtrs': comprimento_mtrs
                }
            )
        else:
            return jsonify(
                {
                'num_rotulos_str': 0,
                'num_voltas': 0,
                'comprimento_mtrs': "0,00"
                }
            )

    return render_template('pages/rotulo.html')


@app.route('/get/linhas/', methods=['POST'])
@cde.verify_auth('ENV006')
def get_linhas() -> Response | None:
    desc_item = request.form['desc_item']

    def find_emb(desc_item):
        if 'PET' in desc_item:
            tipos_embalagem = {
                'PET': ['1L', '1,35L', '1,5L', '900ML', '450ML', '200ML']
            }
        elif 'BAG' in desc_item:
            tipos_embalagem = {
                'BAG': ['10L', '5L', '3L']
            }
        else:
            tipos_embalagem = {
                'VIDRO': ['1L', '1,5L', '300ML']
            }

        for tipo, volumes in tipos_embalagem.items():
            for volume in volumes:
                if volume in desc_item:
                    print(f'  | EMBALAGEM {tipo} {volume}')
                    return tipo, volume

        return '', ''
        
    if desc_item:
        tipo_embal, lit_embal = find_emb(desc_item)
        if tipo_embal:
            with sqlite3.connect(db_path) as connection:
                cursor = connection.cursor()
                cursor.execute('''
                    SELECT DISTINCT cod_linha
                    FROM aux_linha
                    WHERE lit_embal = ?
                    AND tipo_embal = ?;
                ''',
                (lit_embal, tipo_embal))

                cod_linha = cursor.fetchall()

            return jsonify(
                {
                'cod_linha': cod_linha
                }
            )
        else:
            cod_linha = ''
            return jsonify(
                {
                'json_cod_linha': cod_linha
                }
            )


@app.route('/estoque/', methods=['GET', 'POST'])
@cde.verify_auth('MOV004')
def estoque() -> str:
    if request.method == 'POST':
        date = request.form['date']
        saldo_visualization = EstoqueUtils.get_saldo_view(date)
    else:
        date = False
        saldo_visualization = EstoqueUtils.get_saldo_view()
    return render_template(
        'pages/estoque.html', 
        saldo_visualization=saldo_visualization,
        search_term=date
    )


@app.route('/estoque/enderecado/', methods=['GET', 'POST'])
@cde.verify_auth('MOV004')
def estoque_enderecado() -> str:
    if request.method == 'POST':
        date = request.form['date']
        result = EstoqueUtils.get_address_lote(date)
    else:
        result = EstoqueUtils.get_address_lote()
        date = False
    return render_template(
        'pages/estoque-enderecado.html',
        saldo_atual=result,
        search_term=date
    )


@app.route('/estoque/presets/', methods=['GET', 'POST'])
@cde.verify_auth('MOV004')
def estoque_preset() -> str:
    preset_id = request.form.get('preset_id', 1)
    if request.method == 'POST':
        saldo_preset = EstoqueUtils.get_saldo_preset(preset_id, False)
    else:
        saldo_preset = EstoqueUtils.get_saldo_preset(preset_id)
    return render_template(
        'pages/estoque-preset.html',
        saldo_atual=saldo_preset,
        search_term=preset_id
    )


@app.route('/cargas-presets/', methods=['GET', 'POST'])
@cde.verify_auth('MOV006')
def cargas_preset() -> str:
    preset_id = request.form.get('preset_id', 1)
    if request.method == 'POST':
        cargas_preset = EstoqueUtils.get_saldo_preset(preset_id, False)
    else:
        cargas_preset = EstoqueUtils.get_saldo_preset(preset_id)
    return render_template(
        'pages/estoque-preset.html',
        saldo_atual=cargas_preset,
        search_term=preset_id
    )


@app.route('/export_csv/<tipo>/', methods=['GET'])
@cde.verify_auth('CDE017')
def export_csv_tipo(tipo) -> str | Response:
    # EXPORT .csv
    header = True
    if tipo == 'historico':
        data =  HistoricoUtils.get_all_historico()
        filename = 'exp_historico'
    elif tipo == 'produtos':
        data = ProdutoUtils.get_active_itens()
        filename = 'exp_produtos'
    elif tipo == 'saldo':
        data = EstoqueUtils.get_address_lote()
        filename = 'exp_saldo_lote'
    elif tipo == 'faturado':
        data = EstoqueUtils.get_address_lote_fat()
        filename = 'exp_faturado'
    elif tipo == 'estoque':
        data = EstoqueUtils.get_saldo_view()
        filename = 'exp_estoque'
    elif tipo == 'envase':
        data =  Schedule.EnvaseUtils.get_envase()
        filename = 'exp_prog_envase'
    elif tipo == 'producao':
        data =  Schedule.ProcessamentoUtils.get_producao()
        filename = 'exp_prog_producao'
    elif tipo == 'saldo_preset':
        data = EstoqueUtils.get_saldo_preset(1)
        filename = 'get_saldo_preset'    
    elif tipo == 'export_promob':
        header = False
        data = misc.CSVUtils.get_export_promob()
        filename = 'export_promob'
    else:
        alert_type = 'DOWNLOAD IMPEDIDO \n'
        alert_msge = 'A tabela não tem informações suficientes para exportação. \n'
        alert_more = 'POSSÍVEIS SOLUÇÕES:\n• Verifique se a tabela possui mais de uma linha.\n• Contate o suporte.'
        return render_template(
            'components/menus/alert.html', 
            alert_type=alert_type, 
            alert_msge=alert_msge,
            alert_more=alert_more, 
            url_return=url_for('index')
        )
    return misc.CSVUtils.export_csv(data, filename, header)


# __MAIN__
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port, debug=debug)
