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


if __name__:
    # PARÂMETROS
    load_dotenv()
    app = Flask(__name__)
    app.secret_key = os.getenv('SECRET_KEY')
    app.config['CDE_SESSION_LIFETIME'] = timedelta(minutes=90)

    app.config['APP_VERSION'] = ['0.4.6', 'Setembro/2024', False]

    # GET nome do diretório
    dir_os        = os.path.dirname(os.path.abspath(__file__)).upper()
    debug_dir     = os.getenv('DEBUG_DIR').upper().split(';')
    main_exec_dir = os.getenv('MAIN_EXEC_DIR').upper()

    class ANSI:
        RESET = ""
        BOLD = ""
        RED = ""
        GREEN = ""
        YELLOW = ""
        BLUE = ""
        MAGENTA = ""
        CYAN = ""
        WHITE = ""


    class TAGS:
        SERVIDOR = f'{ANSI.MAGENTA}[SERVIDOR]{ANSI.RESET}'
        ERRO     = f'{ANSI.RED}[ERRO]{ANSI.RESET}'
        INFO     = f'{ANSI.BLUE}[INFO]{ANSI.RESET}'
        STATUS   = f'{ANSI.GREEN}[STATUS]{ANSI.RESET}'
        DENIED   = f'{ANSI.RED}403{ANSI.RESET}'
        GRANTED  = f'{ANSI.CYAN}200{ANSI.RESET}'


    def logging(tag_1, tag_2, msge):
        timestamp = Misc.get_timestamp()
        if not tag_2:
            print(f'{tag_1} {msge}')
            return
        print(f'{tag_1} ({timestamp}) {tag_2} | {msge}')
        return


    # STRINGS DE EXECUCAO
    exec_head   = \
f'''
-.     .-.     .-.     .-.     .-.     .-.     .-.     .-.     .-.     .-
  '._.'   '._.'   '._.'   '._.'   '._.'   '._.'   '._.'   '._.'   '._.'

                                                                    
          CCCCCCCCCCCCC   DDDDDDDDDDDDD           EEEEEEEEEEEEEEEEEEEEEE
       CCC::::::::::::C   D::::::::::::DDD        E::::::::::::::::::::E
     CC:::::::::::::::C   D:::::::::::::::DD      E::::::::::::::::::::E
    C::::::CCCCCCCCCCCC   DDDDDDDDDDDD::::::D     EEEEEEEEEEEEEEEEEEEEEE
   C:::::CC                           DD:::::D                          
  C:::::C                               D:::::D                         
  C:::::C                               D:::::D   EEEEEEEEEEEEEEEEEEEE  
  C:::::C                               D:::::D   E::::::::::::::::::E  
  C:::::C                               D:::::D   EEEEEEEEEEEEEEEEEEEE  
  C:::::C                               D:::::D                         
   C:::::CC                           DD:::::D                          
    C::::::CCCCCCCCCCCC   DDDDDDDDDDDD::::::D     EEEEEEEEEEEEEEEEEEEEEE
     CC:::::::::::::::C   D:::::::::::::::DD      E::::::::::::::::::::E
       CCC::::::::::::C   D::::::::::::DDD        E::::::::::::::::::::E
          CCCCCCCCCCCCC   DDDDDDDDDDDDD           EEEEEEEEEEEEEEEEEEEEEE


-.     .-.     .-.     .-.     .-.     .-.     .-.     .-.     .-.     .-
  '._.'   '._.'   '._.'   '._.'   '._.'   '._.'   '._.'   '._.'   '._.'
'''
    start_head  = \
f'''
{TAGS.INFO} CDE Version: {app.config['APP_VERSION'][0]} (beta) - {app.config['APP_VERSION'][1]}
{TAGS.INFO} Python Version: {sys.version}
{TAGS.STATUS} Starting in: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
'''
    error_foot  = \
f'''
{TAGS.ERRO} 
* Impossível executar, verifique se o arquivo está alocado corretamente.

Pressione ENTER para sair...
'''


    if dir_os in debug_dir:
        # Se o user for listado dev, modo_exec = debug
        db_path = os.getenv('DEBUG_DB_PATH')
        port, debug = 5100, True
        app.config['APP_VERSION'][2] = True
        print(start_head)

    elif main_exec_dir in dir_os:
        # Se o diretório atende ao local para produção, modo_exec = produção.
        db_path = os.getenv('DB_PATH')
        port, debug = 5005, False
        print(exec_head, start_head)

    else:
        # Se o diretório não atende aos requisitos plenos de funcionamento, não executa.
        print(error_foot)
        sys.exit(2)


class system:
    @staticmethod
    # CONEXÃO E QUERY NO BANCO DE DADOS
    def db_query_connect(query, dsn):
        dsn = f"DSN={dsn}"
        if dsn != 'DSN=SQLITE':
            uid_pwd = os.getenv('DB_USER').split(';')
            user = uid_pwd[0]
            password = uid_pwd[1]
            try:
                connection = pyodbc.connect(dsn, uid=user, pwd=password)
                cursor = connection.cursor()
                cursor.execute(query)
                columns = [str(column[0]) for column in cursor.description]
                result = cursor.fetchall()

                cursor.close()
                connection.close()
            except Exception as e:
                result = [[f'Erro de consulta: {e}']]
                columns = []
        else:
            try:
                with sqlite3.connect(db_path) as connection:
                    cursor = connection.cursor()
                    cursor.execute(query)
                    columns = [str(column[0]) for column in cursor.description]
                    result = cursor.fetchall()
            except Exception as e:
                result = [[f'Erro de consulta: {e}']]
                columns = []
            
        return result, columns

    
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
                CREATE TABLE IF NOT EXISTS historico (
                    id_mov     INTEGER PRIMARY KEY AUTOINCREMENT,
                    rua_numero INTEGER(6),
                    rua_letra  VARCHAR(10),
                    cod_item   VARCHAR(100),
                    lote_item  VARCHAR(8),
                    quantidade INTEGER,
                    operacao   VARCHAR(15),
                    user_name  VARCHAR(30),
                    time_mov   DATETIME,
                    id_carga   INTEGER(6), 
                    id_user    INTEGER
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
                CREATE TABLE IF NOT EXISTS carga_incomp (
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
                if 'logged_in' in session:
                    id_user = session.get('id_user')
                    session['id_page'] = f'{id_page}'
                    if not session.get('user_grant') <= 2:
                        user_permissions = UserUtils.get_user_permissions(id_user)
                        user_permissions = [item['id_perm'] for item in user_permissions]
                        if id_page in user_permissions:
                            logging(TAGS.SERVIDOR, TAGS.GRANTED, f'{id_user} - {id_page} ({inject_page()["current_page"]})')
                            return f(*args, **kwargs)
                        else:
                            logging(TAGS.SERVIDOR, TAGS.DENIED, f'{id_user} - {id_page} ({inject_page()["current_page"]})')
                            alert_type = 'SEM PERMISSÕES'
                            alert_msge = 'Você não tem permissão para acessar esta página.'
                            alert_more = '''SOLUÇÕES:\n- Solicite ao seu supervisor um novo nível de acesso.'''
                            return render_template(
                                'components/menus/alert.html', 
                                alert_type=alert_type,
                                alert_msge=alert_msge, 
                                alert_more=alert_more,
                                url_return=url_for('index')
                            )
                    else:
                        logging(TAGS.SERVIDOR, TAGS.GRANTED, f'{id_user} - {id_page} ({inject_page()["current_page"]})')
                        return f(*args, **kwargs)
                else:
                    return redirect(url_for('login'))
            return decorador
        return decorator


class EstoqueUtils:
    @staticmethod
    # retorna saldo do item
    def estoque_endereco_with_item(cod_item=False):
        if cod_item:
            query = f'''
                SELECT  
                    h.rua_numero, h.rua_letra, i.cod_item, 
                    i.desc_item, h.lote_item,
                    SUM(
                        CASE 
                        WHEN operacao = 'E' OR operacao = 'TE'
                        THEN quantidade 
                        
                        WHEN operacao = 'S' OR operacao = 'TS' OR operacao = 'F' 
                        THEN (quantidade * -1)

                        ELSE (quantidade * 0)
                        END
                    ) as saldo
                FROM historico h

                JOIN itens i 
                ON h.cod_item = i.cod_item

                WHERE i.cod_item = "{str(cod_item)}"
                
                GROUP BY  
                    h.rua_numero, h.rua_letra, 
                    h.cod_item, h.lote_item
                HAVING saldo != 0

                ORDER BY 
                    h.lote_item ASC, h.rua_letra ASC,
                    h.rua_numero ASC, i.desc_item ASC;
            '''
            dsn = 'SQLITE'
            result_local, columns_local = system.db_query_connect(query, dsn)
            return result_local, columns_local
        else:
            return [], []


    @staticmethod
    # RETORNA TABELA DE SALDO
    def get_saldo_view(timestamp=False):
        if timestamp:
            timestamp = Misc.add_days_to_datetime_str(timestamp, 1)
        timestamp = Misc.parse_db_datetime(timestamp)
        
        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            cursor.execute('''
                SELECT i.desc_item, i.cod_item, COALESCE(t.saldo, 0) as saldo, COALESCE(t.time_mov, "-") as time_mov
                FROM itens i
                LEFT JOIN (
                    SELECT cod_item,
                    SUM(CASE 
                        WHEN operacao = 'E' OR operacao = 'TE' THEN quantidade 
                        WHEN operacao = 'S' OR operacao = 'TS' OR operacao = 'F' THEN (quantidade * -1)
                        ELSE (quantidade * 0)
                        END
                    ) as saldo,
                    MAX(time_mov) as time_mov,
                    ROW_NUMBER() OVER(PARTITION BY cod_item ORDER BY MAX(time_mov) DESC) as rn
                    FROM historico h
                    WHERE time_mov <= ?
                    GROUP BY cod_item
                ) t ON i.cod_item = t.cod_item
                WHERE t.rn = 1 OR t.rn IS NULL
                ORDER BY t.time_mov DESC;
            ''', (timestamp,))

            saldo_visualization = [{
                'cod_item' : row[1], 'desc_item': row[0], 
                'saldo'    : row[2], 'ult_mov'  : row[3]
            } for row in cursor.fetchall()]

        return saldo_visualization

    
    @staticmethod
    # BUSCA SALDO COM UM FILTRO (PRESET)
    def get_saldo_preset(index, timestamp=False):
        itens = EstoqueUtils.get_preset_itens(index)
        
        if not itens:
            return []

        placeholders = ','.join(['?'] * len(itens))
        query = f'''
            SELECT i.desc_item, i.cod_item, COALESCE(t.saldo, 0) as saldo
            FROM itens i
            LEFT JOIN (
                SELECT cod_item,
                SUM(CASE 
                    WHEN operacao = 'E' OR operacao = 'TE' THEN quantidade
                    WHEN operacao = 'S' OR operacao = 'TS' OR operacao = 'F' THEN (quantidade * -1)
                    ELSE (quantidade * 0)
                    END
                ) as saldo,
                MAX(time_mov) as time_mov,
                ROW_NUMBER() OVER(PARTITION BY cod_item ORDER BY MAX(time_mov) DESC) as rn
                FROM historico h
                WHERE time_mov <= ?
                GROUP BY cod_item
            ) t ON i.cod_item = t.cod_item
            WHERE i.cod_item IN ({placeholders})
            ORDER BY i.cod_item;
        '''

        if timestamp:
            timestamp = Misc.add_days_to_datetime_str(timestamp, 1)
        timestamp = Misc.parse_db_datetime(timestamp)

        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            cursor.execute(query, (timestamp, *itens))
            saldo_visualization = [{
                'cod_item' : row[1], 'desc_item': row[0], 
                'saldo'    : row[2]
            } for row in cursor.fetchall()]

        return saldo_visualization

    
    @staticmethod
    # BUSCA ITENS DE PRESETS
    def get_preset_itens(index):
        try:
            with open(f'report/estoque_preset/filtro_{index}.txt', 'r', encoding='utf-8') as file:
                itens = file.read().strip().split(', ')
        except:
            itens = []
        return itens


    @staticmethod
    # RETORNA ENDEREÇAMENTO POR LOTES
    def get_end_lote(timestamp=False):
        if timestamp:
            timestamp = Misc.add_days_to_datetime_str(timestamp, 1)
        timestamp = Misc.parse_db_datetime(timestamp)
        
        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            cursor.execute('''
                SELECT  h.rua_numero, h.rua_letra, i.cod_item, 
                        i.desc_item, h.lote_item,
                        SUM( 
                        CASE 
                        WHEN operacao = 'E' OR operacao = 'TE' THEN quantidade 
                        WHEN operacao = 'S' OR operacao = 'TS' OR operacao = 'F' THEN (quantidade * -1)
                        ELSE (quantidade * 0)
                        END
                        ) as saldo
                FROM historico h
                JOIN itens i ON h.cod_item = i.cod_item
                WHERE h.time_mov <= ?
                GROUP BY h.rua_numero, h.rua_letra, h.cod_item, 
                        h.lote_item
                HAVING saldo != 0
                ORDER BY h.rua_letra ASC, h.rua_numero ASC, i.desc_item ASC;
            ''', (timestamp,))

            end_lote = [{
                'letra'     : row[1], 'numero'   : row[0], 'cod_item': row[2],
                'desc_item' : row[3], 'cod_lote' : row[4], 'saldo'   : row[5]
            } for row in cursor.fetchall()]

        return end_lote


    @staticmethod
    # RETORNA ENDEREÇAMENTO DE FATURADOS POR LOTES
    def get_end_lote_fat():
        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            cursor.execute('''
                SELECT  
                    h.rua_numero, h.rua_letra, i.cod_item,
                    i.desc_item,  h.lote_item, h.id_carga, 
                    SUM( CASE WHEN operacao = 'F' 
                            THEN (quantidade)
                            ELSE (quantidade * 0)
                            END
                    ) as saldo, h.time_mov
                FROM historico h
                JOIN itens i ON h.cod_item = i.cod_item
                GROUP BY  
                    h.id_carga,  h.rua_numero, h.rua_letra,
                    h.cod_item, h.lote_item
                HAVING saldo   != 0
                AND h.id_carga != 0
                ORDER BY h.time_mov DESC, h.id_carga DESC, h.cod_item ASC;
            ''')

            end_lote = [{
                'numero'  : row[0], 'letra': row[1], 'cod_item': row[2],
                'desc_item' : row[3], 'cod_lote' : row[4], 'saldo'   : row[6],
                'id_carga': row[5], 'time_mov': row[7]
            } for row in cursor.fetchall()]

        return end_lote


    @staticmethod
    # RETORNA SALDO DO ITEM NO ENDEREÇO FORNECIDO
    def get_saldo_item(rua_numero, rua_letra, cod_item, cod_lote):
        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            cursor.execute('''
                SELECT COALESCE(SUM(CASE 
                    WHEN operacao = 'E' OR operacao = 'TE' THEN quantidade 
                    WHEN operacao = 'S' OR operacao = 'TS' OR operacao = 'F' THEN (quantidade * -1)
                    ELSE (quantidade * 0)
                END), 0) as saldo
                FROM historico h
                WHERE rua_numero = ? AND rua_letra = ? AND cod_item = ? AND lote_item = ?;
            ''', (rua_numero, rua_letra, cod_item, cod_lote))
            saldo_item = cursor.fetchone()[0]
        return saldo_item


    @staticmethod    
    # RETORNA TABELA DE SALDO
    def get_export_promob():
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
                        cod_item,
                        SUM(CASE 
                            WHEN operacao IN ('E', 'TE') THEN quantidade
                            WHEN operacao IN ('S', 'TS', 'F') THEN (quantidade * -1)
                            ELSE (quantidade * 0)
                        END) as saldo,
                        MAX(time_mov) as time_mov,
                        ROW_NUMBER() OVER(PARTITION BY cod_item ORDER BY MAX(time_mov) DESC) as rn
                    FROM 
                        historico h
                    GROUP BY 
                        cod_item
                    HAVING 
                        saldo != 0
                ) t ON i.cod_item = t.cod_item
                WHERE 
                    t.rn = 1 OR t.rn IS NULL
                ORDER BY 
                    i.cod_item;
            ''')

            saldo_visualization = [{
                'cod_item': row[1],
                'deposito': 2,
                'qtde'    : row[2]
            } for row in cursor.fetchall()]

        return saldo_visualization


class CargaUtils:
    @staticmethod
    # retorna a carga que já foi concluída
    # (presente no historico)
    def get_carga_from_hist(id_carga) -> list:
        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            cursor.execute('''
                SELECT cod_item, count(*)
                FROM historico
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
    # INSERE REGISTRO NA TABELA DE CARGAS PENDENTES
    def insert_carga_incomp(id_carga, cod_item, qtde_atual, qtde_solic):
        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            cursor.execute('''
                INSERT INTO carga_incomp (
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
                UPDATE carga_incomp 
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
                FROM carga_incomp 
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
                    UPDATE carga_incomp 
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

        query = f'''
            SELECT DISTINCT id_carga, i.cod_item, desc_item, qtde_atual, qtde_solic
            FROM carga_incomp ci
            JOIN itens i
            ON ci.cod_item = i.cod_item
            {where_clause};
        '''
        
        dsn = 'SQLITE'
        result, columns = system.db_query_connect(query, dsn)
        
        return result, columns 


    @staticmethod
    # retorna todas as cargas incompletas
    def listed_carga_incomp():
        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            cursor.execute('''
                SELECT DISTINCT id_carga
                FROM carga_incomp ci
                
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
                FROM historico h
                
                JOIN itens i
                ON h.cod_item = i.cod_item
                
                WHERE id_carga = ?;
            ''', (id_carga,))
            rows = cursor.fetchall()
            return rows


    @staticmethod
    # RETORNA OBSERVACOES COM O ID DE CARGA
    def get_obs_with_carga(id_carga):
        query = f'''
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

            WHERE icrg.CODIGO_GRUPOPED = {id_carga}
        '''

        dsn = 'HUGOPIET'
        result, columns = system.db_query_connect(query, dsn)

        if result:
            return result[0][0]
        return None


    @staticmethod
    # RETORNA CLIENTE COM O ID DE CARGA
    def get_cliente_with_carga(id_carga):
        query = f'''
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

            WHERE icrg.CODIGO_GRUPOPED = {id_carga}
        '''

        dsn = 'HUGOPIET'
        result, columns = system.db_query_connect(query, dsn)

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
                FROM historico
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


class HistoricoUtils:
    @staticmethod
    # SELECIONA TODOS ITENS DE REGISTRO POSITIVO NO ENDEREÇO FORNECIDO
    def select_rua(letra, numero):
        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            cursor.execute('''
                SELECT cod_item, lote_item, 
                COALESCE(SUM(CASE 
                    WHEN operacao = 'E' OR operacao = 'TE' THEN quantidade 
                    WHEN operacao = 'S' OR operacao = 'TS' OR operacao = 'F' THEN (quantidade * -1)
                    ELSE (quantidade * 0)
                END), 0) as saldo
                FROM historico
                WHERE rua_letra = ? AND rua_numero = ?
                GROUP BY cod_item, lote_item;
            ''', (letra, numero))
            
            items = cursor.fetchall()

            return items


    @staticmethod
    # INSERE REGISTRO NA TABELA DE HISTÓRICO
    def insert_historico(numero, letra, cod_item, lote_item, quantidade, operacao, timestamp_out, id_carga):
        user_name_mov = session['user_name']
        id_user_mov = session['id_user']

        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            cursor.execute('''
                INSERT INTO historico (
                    rua_numero, rua_letra, cod_item,
                    lote_item, quantidade, operacao,
                    time_mov, id_carga, id_user)
                VALUES (
                    ?, ?, ?,
                    ?, ?, ?,
                    ?, ?, ?);                
                ''',
                (numero, letra, cod_item,
                lote_item, quantidade, operacao, 
                timestamp_out, id_carga, id_user_mov)
            )
            
            connection.commit()


    @staticmethod
    # RETORNA MOVIMENTAÇÕES NO INTERVALO
    def get_historico(page=1, per_page=10):
        offset = (page - 1) * per_page

        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()

            cursor.execute('SELECT COUNT(*) FROM historico;')
            row_count = cursor.fetchone()[0] # número total de linhas

            cursor.execute('''
                SELECT  
                    h.rua_numero, h.rua_letra, h.cod_item,
                    i.desc_item, h.lote_item, h.quantidade,
                    h.operacao, u.id_user||' - '||u.nome_user,
                    h.time_mov
                FROM historico h
                
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
                FROM historico h
                
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
                -- copos cadastrados por extensão
                i.ITEM IN ('EM.3577', 'EM.1074');
        '''

        dsn = 'HUGOPIET'
        result, columns = system.db_query_connect(query, dsn)
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
        print(f'    | Código fornecido: {input_code}')
        
        if len(input_code) == 4 or len(input_code) == 0:
            desc_item, cod_item, cod_lote, cod_linha = 'ITEM NÃO CADASTRADO OU INATIVO', '', '', ''
            print(f'    | {desc_item}')
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
                        print(f'    | {desc_item}')
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
                        print(f'    | {desc_item}')
                    return jsonify(
                        {
                        'json_cod_item' : cod_item, 
                        'json_cod_lote' : cod_lote, 
                        'json_desc_item': desc_item
                        }
                    )

            else:
                desc_item, cod_item, cod_lote = 'ITEM NÃO CADASTRADO OU INATIVO', '', ''
                print(f'    | {desc_item}')
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
    def toggle_item_flag(cod_item, flag):
        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            cursor.execute('''
                UPDATE itens SET flag_ativo = ? WHERE cod_item = ?;
            ''', (flag, cod_item))

            connection.commit()
        return


class UserUtils:
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
                user_permissions = [{'id_perm': row[0]} for row in rows]
                return user_permissions
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
        query = f'''
            SELECT DISTINCT
                u.nome_user || ' ' || u.sobrenome_user AS NOME_USER

            FROM users u

            WHERE u.id_user = {id_user};
        '''

        dsn = 'SQLITE'
        result, columns = system.db_query_connect(query, dsn)

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


class Misc:
    @staticmethod
    # BUSCA FRASE PARA /INDEX
    def get_frase():
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
    # GERA ETIQUETA COM QRCODE
    def generate_etiqueta(qr_text, desc_item, cod_item, cod_lote):
        width, height = 400, 400
        img  = Image.new('RGB', (width, height), color='white')
        cod_lote = f'LOTE: {cod_lote}'
        desc_item = f'{cod_item} - {desc_item}'

        qr_image = Misc.qr_code(qr_text)
        qr_width, qr_height = qr_image.size
        img.paste(qr_image, ((width - qr_width) // 2, (height - qr_height) // 2))

        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype('arialbd.ttf', 30)

        lote_bbox  = draw.textbbox((0, 0), cod_lote, font=font)
        lote_width = lote_bbox[2] - lote_bbox[0]
        draw.text(((width - lote_width) // 2, height // 1.5), cod_lote, fill='black', font=font)

        text   = desc_item
        font   = ImageFont.truetype('arialbd.ttf', 22)
        lines  = textwrap.wrap(text, width=30)
        y_text = height - height // 4.6
        for line in lines:
            text_width, text_height = draw.textbbox((0, 0), line, font=font)[2:]
            draw.text(((width - text_width) // 2, y_text), line, font=font, fill='black')
            y_text += text_height

        img_io = io.BytesIO()
        img.save(img_io, format='PNG')
        img_io.seek(0)

        img_base64 = base64.b64encode(img_io.getvalue()).decode()
        return img_base64


    @staticmethod
    # RETORNA TIMESTAMP
    def get_timestamp():
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


    @staticmethod
    # ADICIONA DIAS À DATA INFORMADA
    def add_days_to_datetime_str(date_str, qtde_days):

        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        
        new_date_obj = date_obj + timedelta(days=qtde_days)
        
        new_date_str = new_date_obj.strftime('%Y-%m-%d')
        
        return new_date_str


    @staticmethod
    # MENSAGEM DO TELEGRAM
    def tlg_msg(msg):
        if not session.get('user_grant') == 1:
            if debug == True:
                print(f'{[TAGS.ERRO]}A mensagem não pôde ser enviada em modo debug')
            else:
                bot_token = os.getenv('TLG_BOT_TOKEN')
                chat_id   = os.getenv('TLG_CHAT_ID')

                url       = f'https://api.telegram.org/bot{bot_token}/sendMessage'
                params    = {'chat_id': chat_id, 'text': msg}
                response  = requests.post(url, params=params)
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
    def hash_key(password):
        return pbkdf2_sha256.hash(password)


    @staticmethod
    # PARSE P/ FLOAT
    def parse_float(value):
        try:
            return float(value.replace(',', '.'))
        except ValueError:
            return 0
    

    @staticmethod
    # VERIFICA SENHA NO BANCO DE HASH
    def password_check(id_user, password):
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
                return Misc.check_key(db_password, password)
            return False


    @staticmethod
    # VERIFICA SENHA NO BANCO DE HASH
    def check_key(hashed_pwd, pwd):
        return pbkdf2_sha256.verify(pwd, hashed_pwd)


    class CSVUtils:
        @staticmethod
        # CSV PARA INTEGRAÇÃO ERP
        def iterate_csv_data_erp(data):
            csv_data = ''
            for item in data:
                line = ';'.join(map(str, item.values()))
                csv_data += f'"{line}"\n'
            return csv_data


        @staticmethod
        # CORPO CSV PADRAO
        def iterate_csv_data(data):
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
        # CONSTRUTOR DE CSV
        def export_csv(data, filename, include_headers=True):
            if data and len(data) > 0:
                csv_data = ''
                if not include_headers:
                    csv_data += Misc.CSVUtils.iterate_csv_data_erp(data)
                else:
                    csv_data += Misc.CSVUtils.add_headers(data)
                    csv_data += Misc.CSVUtils.iterate_csv_data(data)

                csv_filename = Response(csv_data, content_type='text/csv')
                csv_filename.headers['Content-Disposition'] = f'attachment; filename={filename}.csv'

                return csv_filename
            else:
                alert_type = 'DOWNLOAD IMPEDIDO \n'
                alert_msge = 'A tabela não tem informações o suficiente para exportação. \n'
                alert_more = ('''POSSÍVEIS SOLUÇÕES:
                            - Verifique se a tabela possui mais de uma linha.
                            - Contate o suporte. ''')
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
    # VERIFICA SE A SESSÃO ESTÁ EXPIRADA
    if request.path.startswith(('/static', '/get', '/post')):
        # IGNORA AS REQUISICOES DE ARQUIVOS ESTÁTICOS
        return None
    if 'last_active' in session:
        next_url = request.url
        last_active     = session.get('last_active')
        expiration_time = app.config['CDE_SESSION_LIFETIME']
        if isinstance(last_active, datetime):
            utc_now     = datetime.now(timezone.utc)
            if (utc_now - last_active) > expiration_time:
                session.clear()
                session['next_url'] = next_url
                return redirect(url_for('login'))
    session['last_active'] = datetime.now(timezone.utc)


@app.before_request
def check_ip() -> None:
    # CHECA LISTA DE IPS (MODO DEBUG)
    client_ip = request.remote_addr
    if not debug == True:
        blacklist = os.getenv('BLACKLIST')
        if client_ip in blacklist:
            msg = f'{client_ip} na Blacklist.'
            Misc.tlg_msg(msg)
            abort(403)
    '''
    else:
        current_server_ip = request.host
        adm_ip = os.getenv('ADM_IPS').split(';')
        if client_ip not in current_server_ip:
            if client_ip not in adm_ip:
                msg = f'{client_ip}'
                tlg_msg(msg)
            abort(403)
    '''
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



# ROTAS DE ACESSO | URL
#
@app.route('/')
@system.verify_auth('CDE001')
def index():
    return redirect(url_for('home'))


@app.route('/debug-page')
@system.verify_auth('DEV000')
def debug_page():
    return render_template('pages/debug-page.html')


@app.route('/home')
@system.verify_auth('CDE001')
def home():
    return render_template(
        'pages/index/cde-index.html', 
        frase=Misc.get_frase()
    )


@app.route('/home/tl')
@system.verify_auth('CDE001')
def home_tl():
    return render_template(
        'pages/index/tl-index.html', 
        frase=Misc.get_frase()
    )


@app.route('/home/hp')
@system.verify_auth('CDE001')
def home_hp():
    return render_template(
        'pages/index/hp-index.html', 
        frase=Misc.get_frase()
    )


@app.route('/in-dev')
@system.verify_auth('CDE001')
def in_dev():
    return render_template('pages/developing.html')


@app.route('/users')
@system.verify_auth('CDE016')
def users():
    return render_template(
        'pages/users/users.html', 
        users=UserUtils.get_users()
    )


@app.route('/cde/permissions', methods=['GET', 'POST'])
@system.verify_auth('CDE018')
def permissions():
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


@app.route('/cde/permissions/<string:id_perm>', methods=['GET', 'POST'])
@system.verify_auth('CDE018')
def permissions_id(id_perm):
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
@app.route('/api', methods=['GET', 'POST'])
@system.verify_auth('DEV000')
def api():
    if request.method == 'POST':
        query = request.form['sql_query']
        dsn   = request.form['sel_schema']
        if re.search(r'\b(DELETE|INSERT|UPDATE)\b', query, re.IGNORECASE):
            result = [["Os comandos DELETE, INSERT e UPDATE; não são permitidos."]]
            return render_template(
                'pages/api.html', 
                result=result,
                query=query,
                dsn=dsn
            )
        else:
            result, columns = system.db_query_connect(query, dsn)

            return render_template(
                'pages/api.html', 
                result=result,
                columns=columns,
                query=query,
                dsn=dsn
            )
    return render_template(
        'pages/api.html'
    )


# ROTA PAGINA DE LOGIN
@app.route('/login')
def pagina_login():
    return render_template('pages/login.html')


@app.route('/change-password', methods=['GET', 'POST'])
def change_password():
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
        if user_id and Misc.password_check(user_id, password):
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


# ROTA DE SESSÃO LOGIN
@app.route('/login', methods=['POST'])
def login():
    # TODO: método auxiliar
    if request.method == 'POST':
        if 'logged_in' in session:
            return redirect(url_for('index'))
    
        input_login = str(request.form['login_user'])
        input_pwd   = str(request.form['password_user'])

        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            cursor.execute('''
                SELECT privilege_user, nome_user, sobrenome_user,
                        password_user, id_user, ult_acesso
                FROM users
                WHERE login_user = ?;
            ''', (input_login,))

            row = cursor.fetchone()

            if row is None:
                # if 'logged_in' in session:
                alert_msge = 'O usuário não foi encontrado. Tente novamente.'
                return render_template(
                    'pages/login.html', 
                    alert_msge=alert_msge
                )
            user_pwd = row[3]

            if not Misc.check_key(user_pwd, input_pwd):
                alert_msge = 'A senha está incorreta. Tente novamente.'
                return render_template(
                    'pages/login.html', 
                    alert_msge=alert_msge
                )
        
            privilege_user = row[0]
            nome_user      = row[1]
            sobrenome_user = row[2]
            id_user        = row[4]

            try:
                session['user_initials'] = f'{nome_user[0]}{sobrenome_user[0]}'
                session['user_name']     = f'{nome_user} {sobrenome_user}'
            finally:
                session['id_user']       = id_user
                session['logged_in']     = True
                session['user_grant']    = privilege_user

                msg = f'''[LOG-IN]\n{id_user} - {nome_user} {sobrenome_user}\n{request.remote_addr}'''
                Misc.tlg_msg(msg)

                acesso = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                input_pwd = "12345"
                if Misc.check_key(user_pwd, input_pwd):
                    alert_type = 'REDEFINIR (SENHA)'
                    alert_msge = 'Você deve definir sua senha no seu primeiro acesso.'
                    alert_more = '/users/reset-password'
                    url_return = 'Digite sua nova senha...'

                    with sqlite3.connect(db_path) as connection:
                        acesso = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        cursor = connection.cursor()
                        cursor.execute('''
                            UPDATE users
                            SET ult_acesso = ?
                            WHERE id_user  = ?;
                        ''',
                        (acesso, id_user))
                        connection.commit()
                    
                    return render_template(
                        'components/menus/alert-input.html', 
                        alert_type=alert_type,
                        alert_msge=alert_msge,
                        alert_more=alert_more,
                        url_return=url_return
                    )
                else:
                    # if ult_acesso:
                    if not debug == True:
                        with connection:
                            cursor = connection.cursor()
                            cursor.execute('''
                                UPDATE users
                                SET ult_acesso = ?
                                WHERE id_user  = ?;
                            ''', (acesso, id_user))
                    next_url = session.get('next_url')
                    
                    if next_url:
                        return redirect(next_url)
                    return redirect(url_for('index'))
    else:
        # if not request.method == 'POST':
        return redirect(url_for('login'))


# ROTA DE SAÍDA DO USUÁRIO
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/users/reset-password', methods=['POST'])
@system.verify_auth('CDE001')
def reset_password():
    password      = request.form['input']
    password_user = Misc.hash_key(password)
    id_user       = session.get('id_user')

    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute('''
            UPDATE users 
            SET password_user = ?
            WHERE id_user     = ?;
        ''',
        (password_user, id_user))
        connection.commit()

    return redirect(url_for('index'))


@app.route('/get/item', methods=['POST'])
@system.verify_auth('CDE001')
def get_item():
    input_code = request.form['input_code'].strip()
    result_json = ProdutoUtils.get_item_json(input_code)
    
    return result_json


# ROTA DE MOVIMENTAÇÃO NO ESTOQUE (/mov)
@app.route('/mov')
@system.verify_auth('MOV002')
def mov():
    end_lote = EstoqueUtils.get_end_lote()

    return render_template(
        'pages/mov/mov.html', 
        saldo_atual=end_lote
    )


@app.route('/mov/historico')
@system.verify_auth('MOV003')
def historico():
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


@app.route('/mov/historico/search', methods=['GET', 'POST'])
@system.verify_auth('MOV003')
def historico_search():
    if request.method == 'POST':
        search_term  = request.form['search_term']
        search_index = request.form['search_index']
        
        option_texts = {
            'cod_item': 'Item (Código)',
            'desc_item': 'Item (Descrição)',
            'endereco': 'Endereço',
            'operacao': 'Operação (Descrição)',
            'quantidade': 'Quantidade',
            'cod_lote': 'Lote (Código)',
            'user_name': 'Usuário (Nome)',
            'timestamp': 'Horário (Data/Hora)'
        }

        search_row_text = option_texts.get(search_index, '')

        estoque = HistoricoUtils.get_all_historico()
        filtered_estoque = [item for item in estoque if search_term.lower() in item[search_index].lower()]

        return render_template(
            'pages/mov/mov-historico.html', 
            estoque=filtered_estoque, 
            search_term=search_term, 
            page = 0, max=max, min=min, 
            total_pages=0,
            search_row_text=search_row_text
        )
    
    return render_template(
        'pages/mov/mov-historico.html', 
        estoque=[], 
        search_term="", 
        page = 0, max=max, min=min, 
        total_pages=0, 
        search_row_text=search_row_text
    )


@app.route('/mov/faturado')
@system.verify_auth('MOV005')
def faturado():
    end_lote = EstoqueUtils.get_end_lote_fat()

    return render_template(
        'pages/mov/mov-faturado.html', 
        saldo_atual=end_lote
    )


# ROTA DE MOVIENTAÇÃO NO ESTOQUE (/mov/MOVING)
@app.route('/mov/moving', methods=['POST'])
@system.verify_auth('MOV002')
def moving():
    numero          = int(request.form['end_number'])
    letra           = str(request.form['end_letra'])
    operacao        = str(request.form['operacao'])
    is_end_completo = bool(request.form.get('is_end_completo'))
    id_carga        = 0

    timestamp_br    = datetime.now(timezone(timedelta(hours=-3)))
    timestamp_out   = timestamp_br.strftime('%Y/%m/%d %H:%M:%S')
    timestamp_in    = (timestamp_br + timedelta(seconds=1)).strftime('%Y/%m/%d %H:%M:%S')

    print(f'    | OPERAÇÃO: {operacao}')

    if is_end_completo:
        # MOVIMENTA ENDEREÇO COMPLETO
        items = HistoricoUtils.select_rua(letra, numero)
        
        print(f'    | ENDEREÇO COMPLETO ({letra}.{numero}): {items}')

    else:
        cod_item   = str(request.form['cod_item'])
        lote_item  = str(request.form['cod_lote'])
        quantidade = int(request.form['quantidade'])
        items      = [(cod_item, lote_item, quantidade)]
        # MOVIMENTA ITEM ÚNICO
        
        print(f'    | ITEM ÚNICO ({letra}.{numero}): {items}')

        saldo_item  = int(EstoqueUtils.get_saldo_item(numero, letra, cod_item, lote_item))
        if operacao in ('S', 'T', 'F') and quantidade > saldo_item:
            # IMPOSSIBILITA ESTOQUE NEGATIVO 
            alert_type = 'OPERAÇÃO CANCELADA'
            alert_msge = 'O saldo do item selecionado é INSUFICIENTE.'
            alert_more = ('''POSSÍVEIS SOLUÇÕES:
                            - Verifique se está movimentando o item correspondente.
                            - Verifique a quantidade de movimentação.
                            - Verifique a operação selecionada. ''')
            
            return render_template(
                'components/menus/alert.html', 
                alert_type=alert_type,
                alert_msge=alert_msge,
                alert_more=alert_more, 
                url_return=url_for('mov')
            )

    if operacao == 'T':
        # TRANSFERENCIA
        destino_letter = str(request.form['destino_end_letra'])
        destino_number = int(request.form['destino_end_number'])

        if items:
            for item in items:
                cod_item, lote_item, quantidade = item
                if quantidade > 0:
                    # SAÍDA DO ENDEREÇO DE ORIGEM
                    HistoricoUtils.insert_historico(
                        numero, letra, cod_item, 
                        lote_item, quantidade, 'TS', 
                        timestamp_out, id_carga
                    )
                    # ENTRADA NO ENDEREÇO DE DESTINO
                    HistoricoUtils.insert_historico(
                        destino_number, destino_letter, cod_item, 
                        lote_item, quantidade, 'TE', 
                        timestamp_in, id_carga
                    )
                    print(f'    | {letra}.{numero} >> {destino_letter}.{destino_number}: ', cod_item, lote_item, quantidade)
        
    elif operacao == 'F':
        # FATURAMENTO
        id_carga = str(request.form['id_carga'])

        if items:
            for item in items:
                cod_item, lote_item, quantidade = item
                if quantidade > 0:
                    HistoricoUtils.insert_historico(
                        numero, letra, cod_item, 
                        lote_item, quantidade, operacao, 
                        timestamp_out, id_carga
                    )
                    print(f'    | {letra}.{numero}: ', cod_item, lote_item, quantidade)

    elif operacao == 'E' or operacao == 'S':
        # OPERAÇÃO PADRÃO (entrada 'E' ou saída 'S')
        HistoricoUtils.insert_historico(
            numero, letra, cod_item, 
            lote_item, quantidade, operacao, 
            timestamp_out, id_carga
        )
        print(f'    | {letra}.{numero}: ', cod_item, lote_item, quantidade)
    
    else:

        # OPERAÇÃO INVÁLIDA
        print(f'[ERRO] {letra}.{numero}: ', cod_item, lote_item, quantidade, ': OPERAÇÃO INVÁLIDA')

    return redirect(url_for('mov'))


@app.route('/mov/moving/bulk', methods=['POST'])
@system.verify_auth('MOV006')
def moving_bulk():
    sep_carga     = request.json
    timestamp_br  = datetime.now(timezone(timedelta(hours=-3)))
    timestamp_out = timestamp_br.strftime('%Y/%m/%d %H:%M:%S')
    
    try:
        for item in sep_carga:
            haveItem = EstoqueUtils.get_saldo_item(item['rua_numero'], item['rua_letra'], item['cod_item'], item['lote_item'])
            if haveItem < item['qtde_sep']:
                return jsonify({'success': False, 'error': f'Estoque insuficiente para o item {item["cod_item"]} no lote {item["lote_item"]}.'}), 400
        
        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            for item in sep_carga:
                HistoricoUtils.insert_historico(
                    numero=item['rua_numero'],
                    letra=item['rua_letra'],
                    cod_item=item['cod_item'],
                    lote_item=item['lote_item'],
                    quantidade=item['qtde_sep'],
                    operacao='F',
                    timestamp_out=timestamp_out,
                    id_carga=item['nrocarga']
                )
            connection.commit()
        return jsonify({'success': True})
    except Exception as e:
        print(f'[ERRO] Erro ao inserir histórico: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/get/clientes', methods=['GET'])
@system.verify_auth('CDE001')
def get_fant_clientes():
    query = '''
        SELECT FANTASIA
        FROM DB2ADMIN.CLIENTE;
    '''

    dsn = 'HUGOPIET'
    result, columns = system.db_query_connect(query, dsn)

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


@app.route('/mov/carga/incompleta', methods=['GET'])
@system.verify_auth('MOV006')
def carga_incomp():
    result, columns = CargaUtils.get_carga_incomp()
    carga_list = CargaUtils.listed_carga_incomp()
    
    return render_template(
        'pages/mov/mov-carga/mov-carga-incompleta.html',
        carga_incomp=result,
        columns=columns,
        carga_list=carga_list
    )


@app.route('/mov/carga/incompleta/<string:id_carga>', methods=['GET'])
@system.verify_auth('MOV006')
def carga_incomp_id(id_carga):
    id_carga = id_carga.split('-')[0]
    
    result, columns = CargaUtils.get_carga_incomp(id_carga)
    fant_cliente = CargaUtils.get_cliente_with_carga(id_carga)
    carga_list = CargaUtils.listed_carga_incomp()
    
    cod_item = request.args.get('cod_item', '')
    qtde_solic = request.args.get('qtde_solic', '')
    
    if cod_item:
        result_local, columns_local = EstoqueUtils.estoque_endereco_with_item(cod_item)
    else:
        result_local, columns_local = [], []
    
    return render_template(
        'pages/mov/mov-carga/mov-carga-incompleta.html',
        carga_incomp=result,
        columns=columns,
        carga_list=carga_list,
        id_carga=id_carga,
        fant_cliente=fant_cliente,
        cod_item=cod_item,
        qtde_solic=qtde_solic,
        result_local=result_local,
        columns_local=columns_local
    )


@app.route('/api/insert_carga_incomp', methods=['POST'])
@system.verify_auth('MOV006')
def api_insert_carga_incomp():
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


@app.route('/get/itens_carga_incomp/<string:id_carga>', methods=['GET'])
@system.verify_auth('MOV006')
def route_get_carga_incomp(id_carga):
    id_carga = id_carga.split('-')[0]
    
    pending_items = CargaUtils.get_carga_incomp(id_carga)[0]
    return jsonify(
        {
            'items': pending_items
        }
    )
    

@app.route('/api/conclude-incomp/<string:id_carga>', methods=['POST'])
@system.verify_auth('MOV006')
def conclude_incomp(id_carga):
    try:
        CargaUtils.conclude_carga_incomp(id_carga)
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, error=str(e))


@app.route('/envase', methods=['GET'])
@system.verify_auth('ENV006')
def envase():
    envase_list = Schedule.EnvaseUtils.get_envase()

    return render_template(
        'pages/envase/envase.html', 
        envase=envase_list
    )


@app.route('/envase/calendar')
@system.verify_auth('ENV008')
def calendar_envase():
    envase_list = Schedule.EnvaseUtils.get_envase()
    return render_template(
        'pages/envase/envase-calendar.html', 
        envase=envase_list
    )


@app.route('/envase/delete/<id_envase>')
@system.verify_auth('ENV007')
def delete_envase(id_envase):
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute('''
            DELETE 
            FROM prog_envase
            WHERE id_envase = ?;
        ''', 
        (id_envase,))

    return redirect(url_for('envase'))


@app.route('/envase/done/<id_envase>')
@system.verify_auth('ENV006')
def conclude_envase(id_envase):
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute('''
            UPDATE prog_envase
            SET flag_concluido = TRUE
            WHERE id_envase = ?;
        ''',
        (id_envase,))

    return redirect(url_for('envase'))


@app.route('/envase/pending/<id_envase>')
@system.verify_auth('ENV007')
def set_pending_envase(id_envase):
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute('''
            UPDATE prog_envase
            SET flag_concluido = false
            WHERE id_envase = ?;
        ''',
        (id_envase,))

    return redirect(url_for('envase'))


@app.route('/envase/edit', methods=['GET', 'POST'])
@system.verify_auth('ENV007')
def edit_envase():
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


@app.route('/envase/insert', methods=['POST'])
@system.verify_auth('ENV006')
def insert_envase():
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


@app.route('/processamento', methods=['GET'])
@system.verify_auth('PRC010')
def producao():
    id_user = session.get('id_user')
    user_permissions = UserUtils.get_user_permissions(id_user)
    user_permissions = [item['id_perm'] for item in user_permissions]
    producao_list = Schedule.ProcessamentoUtils.get_producao()
    
    return render_template(
        'pages/processamento/processamento.html', 
        producao=producao_list, 
        user_permissions=user_permissions
    )


@app.route('/processamento/calendar')
@system.verify_auth('PRC012')
def calendar_producao():
    producao_list =  Schedule.ProcessamentoUtils.get_producao()

    return render_template(
        'pages/processamento/processamento-calendar.html', 
        producao=producao_list
    )


@app.route('/processamento/delete/<id_producao>')
@system.verify_auth('PRC011')
def delete_producao(id_producao):
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute('''
            DELETE 
            FROM prog_producao 
            WHERE id_producao = ?;
        ''', 
        (id_producao,))

    return redirect(url_for('producao'))


@app.route('/processamento/done/<id_producao>')
@system.verify_auth('PRC010')
def conclude_producao(id_producao):
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute('''
            UPDATE prog_producao
            SET flag_concluido = true
            WHERE id_producao = ?;
        ''', 
        (id_producao,))
        
    return redirect(url_for('producao'))


@app.route('/processamento/pending/<id_producao>')
@system.verify_auth('PRC011')
def set_pending_producao(id_producao):
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute('''
            UPDATE prog_producao
            SET flag_concluido = false
            WHERE id_producao = ?;
        ''',
        (id_producao,))

    return redirect(url_for('producao'))


@app.route('/processamento/edit', methods=['GET', 'POST'])
@system.verify_auth('PRC011')
def edit_producao():
    id_user = session.get('id_user')
    user_permissions = UserUtils.get_user_permissions(id_user)
    user_permissions = [item['id_perm'] for item in user_permissions]

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
            (litros, data_entr_antec, data_producao, observacao, req_id_producao))
            
        return redirect(url_for('producao'))
    else:
        req_id_producao = request.args.get('id_producao')
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
            user_permissions=user_permissions, 
            mode=mode
        )


@app.route('/processamento/insert', methods=['POST'])
@system.verify_auth('PRC010')
def insert_producao():
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


@app.route('/about')
@system.verify_auth('CDE001')
def about():
    return render_template(
        'pages/about.html',
        about=True
    )


@app.route('/users/edit', methods=['POST', 'GET'])
@system.verify_auth('CDE016')
def users_edit():
    req_id_user = request.args.get('id_user')
    if request.method == 'POST':
        pass

    else:
        user_permissions = UserUtils.get_user_permissions(req_id_user)
        permissions = UserUtils.get_permissions()
        return render_template(
            'pages/users/users-edit.html', 
            user_permissions=user_permissions,
            permissions=permissions, 
            req_id_user=req_id_user,
            user_data=UserUtils.get_userdata(req_id_user)
        )


@app.route('/users/remove-perm/<int:id_user>/<string:id_perm>', methods=['GET', 'POST'])
@system.verify_auth('CDE016')
def remove_permission(id_user, id_perm):
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


@app.route('/users/add-perm/<int:id_user>/<string:id_perm>', methods=['GET', 'POST'])
@system.verify_auth('CDE016')
def add_permission(id_user, id_perm):
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


@app.route('/users/inserting', methods=['POST'])
@system.verify_auth('CDE016')
def cadastrar_usuario():
    if request.method == 'POST':
        login_user     = str(request.form['login_user'])
        nome_user      = str(request.form['nome_user'])
        sobrenome_user = str(request.form['sobrenome_user'])
        privilege_user = int(request.form['privilege_user'])
        data_cadastro  = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        password_user  = Misc.hash_key(request.form['password_user'])

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
                    f'''[CADASTRO]\n{request.remote_addr}\n{id_user} - {user_name} [+] {nome_user} {sobrenome_user} ({privilege_user})'''
                    Misc.tlg_msg(msg)

        except sqlite3.IntegrityError as e:
            if 'UNIQUE constraint failed' in str(e):
                alert_type = 'CADASTRO (USUÁRIO)'
                alert_msge = 'Não foi possível criar usuário...'
                alert_more = 'MOTIVO:\n- Já existe um usuário com este login.'
                
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
                alert_more = f'DESCRIÇÃO DO ERRO:\n- {e}.'
                
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


@app.route('/mov/carga/<string:id_carga>', methods=['GET', 'POST'])
@system.verify_auth('MOV006')
def carga_id(id_carga):
    result_local, columns_local = [], []
    if request.method == 'GET':
        cod_item = request.args.get('cod_item', '')
        qtde_solic = request.args.get('qtde_solic', '')
        
        if cod_item:
            result_local, columns_local = EstoqueUtils.estoque_endereco_with_item(cod_item)

        id_carga = id_carga.split('-')[0]
        
        fant_cliente = CargaUtils.get_cliente_with_carga(id_carga)
        all_cargas = CargaUtils.get_cargas_finalizadas()
        
        # SEARCH DE ITENS POR CARGA
        
        cargas_except_query = ', '.join(map(str, all_cargas))

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

            WHERE icrg.CODIGO_GRUPOPED = '{id_carga}'
            AND icrg.CODIGO_GRUPOPED NOT IN ({cargas_except_query})

            ORDER BY COD_ITEM

            LIMIT 100;
        '''

        dsn = 'HUGOPIET'
        result, columns = system.db_query_connect(query, dsn)
        if columns:
            alert = f'Última atualização em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}'
            class_alert = 'success'
        else:
            alert = f'''{result[0][0]}'''
            class_alert = 'error'
        return render_template(
            'pages/mov/mov-carga/mov-carga.html',
            result=result, columns=columns, alert=alert,
            class_alert=class_alert, id_carga=id_carga, 
            cod_item=cod_item, qtde_solic=qtde_solic,
            result_local=result_local, columns_local=columns_local,
            fant_cliente=fant_cliente
        )
    result = []
    return render_template('pages/mov/mov-carga/mov-carga.html', result=result, columns=columns)
        

@app.route('/mov/carga', methods=['GET', 'POST'])
@system.verify_auth('MOV006')
def cargas():
    if request.method == 'POST':
        all_cargas = CargaUtils.get_cargas_finalizadas()
        
        result, columns = CargaUtils.get_cargas(all_cargas)
        
        if columns:
            alert = f'Última atualização em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}'
            class_alert = 'success'

        else:
            alert = f'''{result[0][0]}'''
            class_alert = 'error'
        return render_template('pages/mov/mov-carga/mov-carga.html', result=result, columns=columns, alert=alert, class_alert=class_alert)
    result = []
    return render_template('pages/mov/mov-carga/mov-carga.html', result=result)


@app.route('/mov/requisicao')
@system.verify_auth('MOV007')
def mov_request():
    return render_template(
        'pages/mov/mov-request/mov-request.html'
    )


@app.route('/api/qtde_solic', methods=['GET'])
@system.verify_auth('MOV006')
def get_qtde_solic():
    id_carga = request.args.get('id_carga', type=int)
    cod_item = request.args.get('cod_item', type=str)
    
    query = f'''
        SELECT
            SUM(CAST(iped.QTDE_SOLICITADA AS INTEGER)) AS QTDE_SOLIC
        FROM DB2ADMIN.ITEMPED iped

        JOIN DB2ADMIN.IGRUPOPE icrg
        ON icrg.NRO_PEDIDO = iped.NRO_PEDIDO
        AND icrg.SEQ = iped.SEQ

        WHERE icrg.CODIGO_GRUPOPED = '{id_carga}'
        AND iped.ITEM = '{cod_item}'
    '''
    try:
        dsn = 'HUGOPIET'
        result, columns = system.db_query_connect(query, dsn)
        if result:
            qtde_solic = result[0][0]
        else:
            qtde_solic = 0
        return jsonify({'qtde_solic': qtde_solic})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/itens_carga', methods=['GET'])
@system.verify_auth('MOV006')
def get_itens_carga():
    id_carga = request.args.get('id_carga', type=int)
    
    query = f'''
        SELECT DISTINCT iped.ITEM
        FROM DB2ADMIN.ITEMPED iped

        JOIN DB2ADMIN.IGRUPOPE icrg
        ON icrg.NRO_PEDIDO = iped.NRO_PEDIDO
        AND icrg.SEQ = iped.SEQ

        WHERE icrg.CODIGO_GRUPOPED = '{id_carga}'
    '''
    try:
        dsn = 'HUGOPIET'
        result, columns = system.db_query_connect(query, dsn)
        if result:
            itens = [row[0] for row in result]
        else:
            itens = ['Erro: Nenhum item encontrado.']
        return jsonify({'itens': itens})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/mov/separacao-pend/<string:id_carga>', methods=['GET', 'POST'])
@system.verify_auth('MOV006')
def carga_sep_pend(id_carga):
    id_carga = id_carga.split('-')[0]
    
    id_user   = session.get('id_user')
    user_info = UserUtils.get_userdata(id_user)
    obs_carga = CargaUtils.get_obs_with_carga(id_carga)
    fant_cliente   = CargaUtils.get_cliente_with_carga(id_carga)
    return render_template(
        'pages/mov/mov-carga/mov-carga-separacao-pend.html', 
        id_carga=id_carga, 
        user_info=user_info,
        fant_cliente=fant_cliente,
        obs_carga=obs_carga
    )


@app.route('/mov/separacao-done/<string:id_carga>', methods=['GET', 'POST'])
@system.verify_auth('MOV006')
def carga_sep_done(id_carga):
    if '-' in id_carga:
        id_carga, seq = id_carga.split('-')
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
        obs_carga=obs_carga
    )


@app.route('/get/description_json/<cod_item>', methods=['GET'])
def get_description(cod_item):
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


@app.route('/get/username/<id_user>', methods=['GET'])
def get_username_route(id_user):
    username = UserUtils.get_username(id_user)
    return jsonify({"username": username})


@app.route('/post/save-localstorage', methods=['POST'])
@system.verify_auth('MOV006')
def save_localstorage():
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'Nenhum dado recebido do localStorage.'}), 400
        
        items_data = data.get('data')
        filename = data.get('filename')

        if not items_data or not filename:
            return jsonify({'error': 'Dados inválidos ou ausentes.'}), 400

        # Verifica se o arquivo já existe e cria um nome com sufixo sequencial se necessário
        save_path = os.path.join(app.root_path, 'report/cargas', f'{filename}.json')
        seq = 1
        while os.path.exists(save_path):
            save_path = os.path.join(app.root_path, 'report/cargas', f'{filename}-{seq}.json')
            seq += 1

        with open(save_path, 'w') as file:
            json.dump(items_data, file)

        return jsonify({'message': 'Dados do localStorage foram salvos com sucesso.'}), 200

    except Exception as e:
        print(f'[ERRO] Erro ao salvar dados do localStorage: {str(e)}')
        return jsonify({'error': 'Erro interno ao salvar dados do localStorage.'}), 500
    

@app.route('/get/has_carga_at_history/<string:id_carga>', methods=['GET'])
def has_carga_at_history(id_carga):
    id_carga = id_carga.split('-')[0]
    
    has_carga_at_history = bool(CargaUtils.get_carga_incomp(id_carga)[0])
    return jsonify(
        {
            'bool': has_carga_at_history
        }
    )


@app.route('/get/load-table-data', methods=['GET'])
@system.verify_auth('MOV006')
def load_table_data():
    try:
        filename = request.args.get('filename')
        seq = request.args.get('seq', False)
        
        if not filename:
            return jsonify({'error': 'Nome do arquivo não fornecido.'}), 400

        data = CargaUtils.readJsonCargaSeq(filename, seq)

        return jsonify(data), 200
    
    except FileNotFoundError:
        return jsonify({'error': 'Arquivo de dados da carga não encontrado.'}), 404
    
    except Exception as e:
        return jsonify({'error': f'Erro ao carregar dados da carga: {str(e)}'}), 500
    

@app.route('/get/list-all-separations', methods=['GET'])
@system.verify_auth('MOV006')
def list_all_separations():
    try:
        directory = os.path.join(app.root_path, 'report/cargas')
        files = [f for f in os.listdir(directory) if f.endswith('.json')]
        files_sorted = sorted(files, reverse=True)
        return jsonify(files_sorted), 200
    except Exception as e:
        return jsonify({'error': f'Erro ao listar arquivos: {str(e)}'}), 500


@app.route('/produtos/toggle-perm/<string:cod_item>/<int:flag>', methods=['GET', 'POST'])
@system.verify_auth('ITE005')
def produtos_toggle_perm(cod_item, flag):
    ProdutoUtils.toggle_item_flag(cod_item, flag)
    return redirect(url_for('produtos_flag'))


@app.route('/produtos/flag', methods=['GET', 'POST'])
@system.verify_auth('ITE005')
def produtos_flag():
    itens = ProdutoUtils.get_all_itens()
    
    return render_template(
        'pages/produtos-flag.html',
        itens=itens
    )


@app.route('/produtos', methods=['GET', 'POST'])
@system.verify_auth('ITE005')
def produtos():
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
            alert = f'''{result[0][0]}'''
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


@app.route('/etiqueta', methods=['GET', 'POST'])
@system.verify_auth('OUT014')
def etiqueta():
    if request.method == 'POST':
        qr_text   = str(request.form['qr_text'])
        desc_item = str(request.form['desc_item'])
        cod_item  = str(request.form['cod_item'])
        cod_lote  = str(request.form['lote_item'])

        return Misc.generate_etiqueta(qr_text, desc_item, cod_item, cod_lote)
    return render_template('pages/etiqueta.html', produtos=produtos)


@app.route('/rotulo', methods=['GET', 'POST'])
@system.verify_auth('OUT015')
def rotulo():
    if request.method == 'POST':
        espessura_fita      = Misc.parse_float(request.form['espessura_fita'])
        diametro_inicial    = Misc.parse_float(request.form['diametro_inicial'])
        diametro_minimo     = Misc.parse_float(request.form['diametro_minimo'])
        espessura_papelao   = Misc.parse_float(request.form['espessura_papelao'])
        compr_rotulo        = Misc.parse_float(request.form['compr_rotulo'])
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


@app.route('/get/linhas', methods=['POST'])
@system.verify_auth('ENV006')
def get_linhas():
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
                    print(f'    | EMBALAGEM {tipo} {volume}')
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


@app.route('/estoque', methods=['GET', 'POST'])
@system.verify_auth('MOV004')
def estoque():
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


@app.route('/estoque-enderecado', methods=['GET', 'POST'])
@system.verify_auth('MOV004')
def estoque_enderecado():
    if request.method == 'POST':
        date = request.form['date']
        end_lote = EstoqueUtils.get_end_lote(date)
    else:
        end_lote = EstoqueUtils.get_end_lote()
        date = False
    return render_template(
        'pages/estoque-enderecado.html',
        saldo_atual=end_lote,
        search_term=date
    )


@app.route('/estoque-presets', methods=['GET', 'POST'])
@system.verify_auth('MOV004')
def estoque_preset():
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


@app.route('/cargas-presets', methods=['GET', 'POST'])
@system.verify_auth('MOV006')
def cargas_preset():
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


@app.route('/export_csv/<tipo>', methods=['GET'])
@system.verify_auth('CDE017')
def export_csv_tipo(tipo):
    # EXPORT .csv
    header = True
    if tipo == 'historico':
        data =  HistoricoUtils.get_all_historico()
        filename = 'exp_historico'
    elif tipo == 'produtos':
        data = ProdutoUtils.get_active_itens()
        filename = 'exp_produtos'
    elif tipo == 'saldo':
        data = EstoqueUtils.get_end_lote()
        filename = 'exp_saldo_lote'
    elif tipo == 'faturado':
        data = EstoqueUtils.get_end_lote_fat()
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
        data = Misc.CSVUtils.get_export_promob()
        filename = 'export_promob'
    else:
        alert_type = 'DOWNLOAD IMPEDIDO \n'
        alert_msge = 'A tabela não tem informações suficientes para exportação. \n'
        alert_more = 'POSSÍVEIS SOLUÇÕES:\n- Verifique se a tabela possui mais de uma linha.\n- Contate o suporte.'
        return render_template(
            'components/menus/alert.html', 
            alert_type=alert_type, 
            alert_msge=alert_msge,
            alert_more=alert_more, 
            url_return=url_for('index')
        )
    return Misc.CSVUtils.export_csv(data, filename, header)


# __MAIN__
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port, debug=debug)
