import textwrap
import requests
import sqlite3
import random
import qrcode
import pyodbc
import base64
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


# PARÂMETROS
load_dotenv()   
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=90)


@app.before_request
def renew_session():
    session.modified = True


@app.before_request
def check_session_expiry():
    if 'last_active' in session:
        last_active     = session.get('last_active')
        expiration_time = app.config['PERMANENT_SESSION_LIFETIME']
        if isinstance(last_active, datetime):
            utc_now     = datetime.now(timezone.utc)
            if (utc_now - last_active) > expiration_time:
                session.clear()
                return redirect(url_for('login'))
    session['last_active'] = datetime.now(timezone.utc)


@app.before_request
def check_ip():                                                                                                                         #// CHECA LISTA DE IPS (MODO DEBUG)
    client_ip = request.remote_addr
    """
    if debug:
        current_server_ip = request.host
        adm_ip = os.getenv('ADM_IPS').split(';')
        if client_ip not in current_server_ip and client_ip not in adm_ip:
            msg = f'{client_ip}'
            tlg_msg(msg)
            abort(403)
    else:
        blacklist = os.getenv('BLACKLIST')
        if client_ip in blacklist:
            msg = f'{client_ip} na Blacklist.'
            tlg_msg(msg)
            abort(403)
    """


@app.context_processor
def inject_version():                                                                                                                   #? INJETA VARIAVEL DE VERSÃO AO AMBIENTE
    return dict(app_version=app.config['APP_VERSION'])


@app.context_processor
def inject_page():                                                                                                                      #? RETORNA URL ACESSADA PEÇO USER
    current_page    = request.path
    if 'logged_in' in session:
        user_name   = session.get('user_name')
        id_user     = session.get('id_user')
        print(f"{id_user} - [{user_name}] | ", current_page)
    return {'current_page': current_page}


def get_frase():                                                                                                                        #* BUSCA FRASE MOTIVACIONAL PARA /INDEX
    with open('static/frases.txt', 'r', encoding='utf-8') as file:
        frases = file.readlines()
        frase = random.choice(frases).strip()
        if not frase:
            frase = 'Seja a mudança que você deseja ver no mundo.'
    return frase


def create_tables():                                                                                                                    #* GERADOR DE TABELAS
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()

        # TABELA DE PROGRAMAÇÃO DO ENVASE
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS envase (
                id_envase           INTEGER PRIMARY KEY AUTOINCREMENT,
                linha               INTEGER(3),
                cod_cliente         INTEGER(10),
                cod_item            VARCHAR(6),
                quantidade          INTEGER(20),
                data_entr_antec     DATETIME,
                data_envase         DATETIME,
                observacao          VARCHAR(100),
                concluido           BOOLEAN
            );
        ''')

        # TABELA DE PROGRAMAÇÃO DA PROCESSAMENTO
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS producao (
                id_producao         INTEGER PRIMARY KEY AUTOINCREMENT,
                linha               INTEGER(3),
                liq_tipo            VARCHAR(10),
                liq_linha           VARCHAR(30),
                liq_cor             VARCHAR(30),
                embalagem           VARCHAR(10),
                litros              INTEGER(20),
                data_entr_antec     DATETIME,
                data_producao       DATETIME,
                observacao          VARCHAR(100),
                concluido           BOOLEAN
            );
        ''')

        # TABELA HISTÓRICO
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS historico (
                id_mov              INTEGER PRIMARY KEY AUTOINCREMENT,
                rua_numero          INTEGER(6),
                rua_letra           VARCHAR(10),
                desc_item           VARCHAR(6),
                lote_item           VARCHAR(8),
                quantidade          INTEGER,
                operacao            VARCHAR(15),
                user_name           VARCHAR(30),
                id_carga            INTEGER(6),
                time_mov            DATETIME
            );
        ''')
        
        # TABELA DE CLIENTES
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clientes (
                cod_cliente         INTEGER(10) PRIMARY KEY,
                razao_cliente       VARCHAR(100),
                fantasia_cliente    VARCHAR(100),
                cidade_cliente      VARCHAR(100),
                estado_cliente      VARCHAR(2)
            );
        ''')

        # TABELA DE USUÁRIOS
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id_user             INTEGER PRIMARY KEY AUTOINCREMENT,
                login_user          VARCHAR(30) UNIQUE,
                password_user       TEXT,
                nome_user           VARCHAR(100),
                sobrenome_user      VARCHAR(100),
                privilege_user      INTEGER(2),
                data_cadastro       DATETIME,
                ult_acesso          DATETIME
            );
        ''')

        # TABELA DE PERMISSÕES DE USUÁRIO
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_permissions (
                id_user             INTEGER,
                id_perm             VARCHAR(6)
            );
        ''')                                                                                                                            #TODO! mudar id_perm: integer para varchar(6)

        # TABELA DE ITENS
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS itens (
                cod_item            INTEGER(6) PRIMARY KEY,
                desc_item           VARCHAR(100),
                dun14               INTEGER(14)
            );
        ''')

        # TABELA AUXILIAR DE PRIVILÉGIOS
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS aux_privilege (
                id_priv             INTEGER(2) PRIMARY KEY,
                desc_priv           VARCHAR(30)
            );
        ''')

        # TABELA AUXILIAR DE PERMISSÕES
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS aux_permissions (
                id_perm             VARCHAR(6) PRIMARY KEY,
                desc_perm           VARCHAR(30)
            );
        ''')                                                                                                                            #TODO! mudar id_perm: integer para varchar(6)


        connection.commit()


def get_desc_itens():                                                                                                                   #// RETORNA APENAS DESCRIÇÃO DO ITEM
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute('''
            SELECT DISTINCT desc_item
            FROM itens i
            ORDER BY i.desc_item;
        ''')

        desc_item = [row[0] for row in cursor.fetchall()]
    return desc_item


def get_itens():                                                                                                                        #* RETORNA TODOS OS PARÂMETROS DO ITEM
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute('''
            SELECT DISTINCT *
            FROM itens i
            ORDER BY i.desc_item;
        ''')

        itens = [{
            'cod_item': row[0], 'desc_item': row[1], 'dun14': row[2]
        } for row in cursor.fetchall()]
    return itens


def get_producao():                                                                                                                     #* RETORNA TABELA DE PROGRAMAÇÃO (PROCESSAMENTO)
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute('''
            SELECT  p.id_producao, p.linha, p.liq_linha,
                    p.liq_cor, p.embalagem, p.litros,
                    p.data_entr_antec, p.data_producao, p.observacao,
                    p.concluido, p.liq_tipo
            FROM producao p
            ORDER BY p.data_producao;
        ''')
        producao_list = [{
            'id_producao'     : row[0], 'linha'        : row[1], 'liq_linha' : row[2], 
            'liq_cor'         : row[3], 'embalagem'    : row[4], 'litros'    : row[5], 
            'data_entr_antec' : row[6], 'data_producao': row[7], 'observacao': row[8],
            'concluido'       : row[9], 'liq_tipo'     : row[10]
        } for row in cursor.fetchall()]
        
    return producao_list


def get_envase():                                                                                                                       #* RETORNA TABELA DE PROGRAMAÇÃO (ENVASE)
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute('''
            SELECT  p.id_envase, p.linha, c.fantasia_cliente,
                    i.cod_item, i.desc_item, p.quantidade,
                    p.data_entr_antec, p.data_envase, p.observacao,
                    p.concluido
            FROM envase p
            JOIN itens i ON p.cod_item = i.cod_item
            JOIN clientes c ON p.cod_cliente = c.cod_cliente
            ORDER BY p.data_envase;
        ''')

        envase_list = [{
            'id_envase'       : row[0], 'linha'       : row[1], 'fantasia_cliente' : row[2], 
            'cod_item'        : row[3], 'desc_item'   : row[4], 'quantidade'       : row[5],
            'data_entr_antec' : row[6], 'data_envase' : row[7], 'observacao'       : row[8],
            'concluido'       : row[9]
        } for row in cursor.fetchall()]

    return envase_list


def get_historico(page=1, per_page=10):                                                                                                 #* RETORNA MOVIMENTAÇÕES
    offset = (page - 1) * per_page

    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()

        cursor.execute('SELECT COUNT(*) FROM historico;')
        row_count = cursor.fetchone()[0]

        cursor.execute('''
            SELECT  h.rua_numero, h.rua_letra, h.desc_item,
                    i.desc_item, h.lote_item, h.quantidade,
                    h.operacao, h.user_name, h.time_mov
            FROM historico h
            JOIN itens i ON h.desc_item = i.cod_item
            ORDER BY h.time_mov DESC
            LIMIT ? OFFSET ?;
        ''', (per_page, offset))

        estoque = [{
            'endereco'  : str(row[1]) + '.' + str(row[0]), 'cod_item'   : row[2], 
            'desc_item' : row[3], 'lote'      : row[4],    'quantidade' : row[5], 
            'operacao'  : row[6], 'user_name' : row[7],    'timestamp'  : row[8]
        } for row in cursor.fetchall()]
    return estoque, row_count


def get_all_historico():                                                                                                  
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        
        cursor.execute('''
            SELECT  h.rua_numero, h.rua_letra, h.desc_item,
                    i.desc_item, h.lote_item, h.quantidade,
                    h.operacao, h.user_name, h.time_mov
            FROM historico h
            JOIN itens i ON h.desc_item = i.cod_item
            ORDER BY h.time_mov DESC;
        ''')
        
        estoque = [{
            'endereco'  : str(row[1]) + '.' + str(row[0]), 'cod_item'   : row[2], 
            'desc_item' : row[3], 'lote'      : row[4],    'quantidade' : row[5], 
            'operacao'  : row[6], 'user_name' : row[7],    'timestamp'  : row[8]
        } for row in cursor.fetchall()]
    return estoque


def get_users():                                                                                                                        #* RETORNA DADOS DOS USUÁRIOS
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute('''
            SELECT u.nome_user, u.sobrenome_user, ap.desc_priv,
                   u.ult_acesso, u.id_user
            FROM users u
            JOIN aux_privilege ap ON u.privilege_user = ap.id_priv
            ORDER BY u.ult_acesso DESC;
        ''')

        users_list = [{
            'user_name'  : f'{row[0]} {row[1]}', 'privilegio': row[2], 
            'ult_acesso' : row[3],               'cod_user'  : row[4],
        } for row in cursor.fetchall()]

    return users_list


def get_permissions():
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

    return permissions


def get_end_lote():
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute('''
            SELECT  h.rua_numero, h.rua_letra, i.cod_item, 
                    i.desc_item, h.lote_item,
                    SUM( CASE 
                         WHEN operacao = 'E' OR operacao = 'TE' THEN quantidade 
                         WHEN operacao = 'S' OR operacao = 'TS' OR operacao = 'F' THEN (quantidade * -1)
                         ELSE (quantidade * 0)
                         END
                    ) as saldo
            FROM historico h
            JOIN itens i ON h.desc_item = i.cod_item
            GROUP BY  h.rua_numero, h.rua_letra, h.desc_item, 
                      h.lote_item
            HAVING saldo != 0
            ORDER BY h.rua_letra ASC, h.rua_numero ASC, i.desc_item ASC;
        ''')

        end_lote = [{
            'numero'  : row[0], 'letra': row[1], 'cod_item': row[2],
            'produto' : row[3], 'lote' : row[4], 'saldo'   : row[5]
        } for row in cursor.fetchall()]

    return end_lote


def get_end_lote_fat():
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute('''
            SELECT  h.rua_numero, h.rua_letra, i.cod_item,
                    i.desc_item,  h.lote_item, h.id_carga, 
                    SUM( CASE WHEN operacao = 'F' 
                         THEN (quantidade)
                         ELSE (quantidade * 0)
                         END
                    ) as saldo
            FROM historico h
            JOIN itens i ON h.desc_item = i.cod_item
            GROUP BY  h.id_carga,  h.rua_numero, h.rua_letra,
                      h.desc_item, h.lote_item
            HAVING saldo != 0
            AND h.id_carga != 0
            ORDER BY h.desc_item;
        ''')

        end_lote = [{
            'numero'  : row[0], 'letra': row[1], 'cod_item': row[2],
            'produto' : row[3], 'lote' : row[4], 'saldo'   : row[6],
            'id_carga': float(row[5]) / 10
        } for row in cursor.fetchall()]

    return end_lote


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

        if row:
            ult_acesso = row[1]
        else:
            ult_acesso = None

        return ult_acesso


def get_saldo_view():
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute('''
            SELECT i.desc_item, t.desc_item, t.saldo, t.time_mov
            FROM ( 
                SELECT desc_item,
                SUM(CASE 
                    WHEN operacao IN ('E', 'TE') THEN quantidade
                    WHEN operacao IN ('S', 'TS') THEN (quantidade * -1)
                    ELSE (quantidade * -1)
                    END
                ) as saldo,
                MAX(time_mov) as time_mov,
                ROW_NUMBER() OVER(PARTITION BY desc_item ORDER BY MAX(time_mov) DESC) as rn
                FROM historico h
                GROUP BY desc_item
                HAVING saldo != 0
            ) t
            JOIN itens i ON t.desc_item = i.cod_item
            WHERE rn = 1
            ORDER BY t.desc_item;
        ''')

        saldo_visualization = [{
            'desc_item': row[0], 'cod_item': row[1], 'saldo': row[2], 
            'ult_mov'  : row[3]
        } for row in cursor.fetchall()]

    return saldo_visualization


def tlg_msg(msg):                                                                                                                       #* TLG-bot API
    if not session.get('privilegio') == 1:
        if debug:
            print('[Telegram] não pôde ser enviada em modo debug')
        else:
            bot_token = os.getenv('TLG_BOT_TOKEN')
            chat_id   = os.getenv('TLG_CHAT_ID')

            url       = f'https://api.telegram.org/bot{bot_token}/sendMessage'
            params    = {'chat_id': chat_id, 'text': msg}
            response  = requests.post(url, params=params)
            return response.json()
    else:
        return None


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


def hash_key(password):
    return pbkdf2_sha256.hash(password)


def parse_float(value):
    try:
        return float(value.replace(',', '.'))
    except ValueError:
        return 0


def verify_auth(id_page):
    def decorator(f):
        @wraps(f)
        def decorador(*args, **kwargs):
            if 'logged_in' in session:
                id_user = session.get('id_user')
                session['id_page'] = f'{id_page}'
                if not session.get('privilegio') <= 2:
                    user_permissions = get_user_permissions(id_user)
                    user_permissions = [item['id_perm'] for item in user_permissions]
                    if id_page in user_permissions:
                        print('[ACESSO] PERMITIDO')
                        return f(*args, **kwargs)
                    else:
                        print('[ACESSO] NEGADO')
                        alerta_tipo     = 'SEM PERMISSÕES \n'
                        alerta_mensagem = 'Você não tem permissão para acessar esta página.\n'
                        alerta_mais     = ('''SOLUÇÕES:
                                       - Solicite ao seu supervisor um novo nível de acesso.''')
                        return render_template('components/menus/alert.html', alerta_tipo=alerta_tipo,
                                               alerta_mensagem=alerta_mensagem, alerta_mais=alerta_mais,
                                               url_return=url_for('index'))
                else:
                    print('[ACESSO] PERMITIDO')
                    return f(*args, **kwargs)
            else:
                return redirect(url_for('login'))
        return decorador
    return decorator


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


def select_rua(letra, numero):                                                                                                          #* SELECIONA TODOS ITENS DE REGISTRO POSITIVO NO ENDEREÇO FORNECIDO
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute('''
            SELECT desc_item, lote_item, 
            COALESCE(SUM(CASE 
                WHEN operacao = 'E' OR operacao = 'TE' THEN quantidade 
                WHEN operacao = 'S' OR operacao = 'TS' THEN (quantidade * -1)
                ELSE (quantidade * -1)
            END), 0) as saldo
            FROM historico
            WHERE rua_letra = ? AND rua_numero = ?
            GROUP BY desc_item, lote_item;
        ''', (letra, numero))
        
        items = cursor.fetchall()

        return items


def export_csv(data, filename):                                                                                                         #* EXPORTA DADOS EM CSV (CONFORME FUNÇÃO NO PYTHON)
    if data and len(data) > 0:
        csv_data = ';'.join(data[0].keys()) + '\n'
        for item in data:
            csv_data += ';'.join(map(str, item.values())) + '\n'

        csv_filename = Response(csv_data, content_type='text/csv')
        csv_filename.headers['Content-Disposition'] = f'attachment; filename={filename}.csv'

        return csv_filename
    else:
        alerta_tipo     = 'DOWNLOAD IMPEDIDO \n'
        alerta_mensagem = 'A tabela não tem informações o suficiente para exportação. \n'
        alerta_mais     = ('''POSSÍVEIS SOLUÇÕES:
                       - Verifique se a tabela possui mais de uma linha.
                       - Contate o suporte. ''')
        return render_template('components/menus/alert.html', alerta_tipo=alerta_tipo, 
                               alerta_mensagem=alerta_mensagem, alerta_mais=alerta_mais, 
                               url_return=url_for('index'))


def db_query_connect(query, dsn):                                                                                                       #* CONEXÃO E QUERY NO BANCO DE DADOS
    dsn = f"DSN={dsn}"
    print(dsn)
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


def get_user_permissions(user_id):                                                                                                      #* RETORNA LISTA DE PERMISSÕES DO USUÁRIO
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


def check_key(hashed_password, password):                                                                                               #* VERIFICA SENHA NO BANCO DE HASH
    return pbkdf2_sha256.verify(password, hashed_password)


def get_saldo_item(numero, letra, cod_item, lote):                                                                                      #* RETORNA SALDO DO ITEM NO ENDEREÇO FORNECIDO
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute('''
            SELECT COALESCE(SUM(CASE 
                WHEN operacao = 'E' OR operacao = 'TE' THEN quantidade 
                WHEN operacao = 'S' OR operacao = 'TS' THEN (quantidade * -1)
                ELSE (quantidade * -1)
            END), 0) as saldo
            FROM historico h
            WHERE rua_numero = ? AND rua_letra = ? AND desc_item = ? AND lote_item = ?;
        ''', (numero, letra, cod_item, lote))
        saldo_item = cursor.fetchone()[0]
    return saldo_item


def generate_etiqueta(qr_text, desc_item, cod_item, lote):                                                                              #* GERA ETIQUETA COM QRCODE
    width, height = 400, 400
    img = Image.new('RGB', (width, height), color='white')
    lote = f'LOTE: {lote}'
    desc_item = f'{cod_item} - {desc_item}'

    qr_image = qr_code(qr_text)
    qr_width, qr_height = qr_image.size
    img.paste(qr_image, ((width - qr_width) // 2, (height - qr_height) // 2))

    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype('arialbd.ttf', 30)

    lote_bbox = draw.textbbox((0, 0), lote, font=font)
    lote_width = lote_bbox[2] - lote_bbox[0]
    draw.text(((width - lote_width) // 2, height // 1.5), lote, fill='black', font=font)

    text = desc_item
    font = ImageFont.truetype('arialbd.ttf', 22)
    lines = textwrap.wrap(text, width=30)
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


def insert_historico(numero, letra, cod_item, lote_item, quantidade, operacao, timestamp_out, id_carga):                                #* INSERE REGISTRO NA TABELA DE HISTÓRICO
    user_name_mov = session['user_name']

    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute('''
            INSERT INTO historico (
                rua_numero, rua_letra, desc_item,
                lote_item, quantidade, operacao,
                user_name, time_mov, id_carga )
            VALUES (
                ?, ?, ?,
                ?, ?, ?,
                ?, ?, ? );
            ''',
            (numero, letra, cod_item,
            lote_item, quantidade, operacao,
            user_name_mov, timestamp_out, 
            id_carga))
        
        connection.commit()


@app.route('/')                                                                                                                         #! ROTAS DE ACESSO | URL
@verify_auth('CDE001')
def index():
    create_tables()

    print(f"[SERVIDOR] USUÁRIO: {session['user_name']}")
    return redirect(url_for('home'))


@app.route('/debug')
@verify_auth('DEV000')
def debug():
    return render_template('pages/debug-page.html')


@app.route('/home')
@verify_auth('CDE001')
def home():
    return render_template('pages/index/index.html', frase=get_frase())


@app.route('/home/tl')
@verify_auth('CDE001')
def home_tl():
    return render_template('pages/index/tl-index.html', frase=get_frase())


@app.route('/home/hp')
@verify_auth('CDE001')
def home_hp():
    return render_template('pages/index/hp-index.html', frase=get_frase())


@app.route('/in-dev')
@verify_auth('CDE001')
def in_dev():
    return render_template('pages/developing.html')


@app.route('/users')
@verify_auth('CDE016')
def users():
    create_tables()
    get_users()

    return render_template('pages/users/users.html', users=get_users())


@app.route('/api', methods=['GET', 'POST'])                                                                                             #* ROTA DE DATABASE MANAGER
@verify_auth('DEV000')
def api():
    if request.method == 'POST':
        query   = request.form['sql_query']
        dsn     = request.form['sel_schema']
        
        result, columns = db_query_connect(query, dsn)

        return render_template('pages/api.html', result=result, columns=columns, query=query, dsn=dsn)
    return render_template('pages/api.html')


@app.route('/login')                                                                                                                    #* ROTA PAGINA DE LOGIN
def pagina_login():
    return render_template('pages/login.html')


@app.route('/login', methods=['POST'])                                                                                                  #* ROTA DE SESSÃO LOGIN
def login():                                                                                                                            # TODO: função auxiliar
    if request.method == 'POST':
        if 'logged_in' not in session:
            login_user = str(request.form['login_user'])
            password   = str(request.form['password_user'])

            with sqlite3.connect(db_path) as connection:
                cursor = connection.cursor()
                cursor.execute('''
                    SELECT privilege_user, nome_user, sobrenome_user,
                           password_user, id_user, ult_acesso
                    FROM users
                    WHERE login_user = ?;
                ''', (login_user,))

                row = cursor.fetchone()

                if row is not None:
                    password_user = row[3]
                    if check_key(password_user, password):
                        privilege_user = row[0]
                        nome_user = row[1]
                        sobrenome_user = row[2]
                        id_user = row[4]
                        try:
                            session['user_initials'] = f'{nome_user[0]}{sobrenome_user[0]}'
                            session['user_name']     = f'{nome_user} {sobrenome_user}'
                        finally:
                            session['id_user']       = id_user
                            session['logged_in']     = True
                            session['privilegio']    = privilege_user

                            msg = f'''[LOG-IN]\n{id_user} - {nome_user} {sobrenome_user}\n{request.remote_addr}'''
                            tlg_msg(msg)

                            acesso = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            password = "12345"
                            if check_key(password_user, password):
                                alerta_tipo     = 'REDEFINIR (SENHA) \n'
                                alerta_mensagem = 'Você deve definir sua senha no seu primeiro acesso.'
                                alerta_mais     = '/users/reset-key'
                                url_return      = 'Digite sua nova senha...'

                                return render_template('components/menus/alert-input.html', alerta_tipo=alerta_tipo,
                                                       alerta_mensagem=alerta_mensagem,
                                                       alerta_mais=alerta_mais, url_return=url_return)
                            else:  # if ult_acesso:
                                with connection:
                                    cursor = connection.cursor()
                                    cursor.execute('''
                                        UPDATE users
                                        SET ult_acesso = ?
                                        WHERE id_user  = ?;
                                    ''', (acesso, id_user))

                                return redirect(url_for('index'))
                    else:   # if not check_key(password_user, password):
                        alerta_mensagem = 'A senha está incorreta. Tente novamente.'
                        return render_template('pages/login.html', alerta_mensagem=alerta_mensagem)

                else:  # if row is None:
                    alerta_mensagem = 'O usuário não foi encontrado. Tente novamente.'
                    return render_template('pages/login.html', alerta_mensagem=alerta_mensagem)
        else:   # if 'logged_in' in session:
            return redirect(url_for('index'))
    else:  # if not request.method == 'POST':
        return redirect(url_for('login'))


@app.route('/logout')                                                                                                                   #* ROTA DE SAÍDA DO USUÁRIO
@verify_auth('CDE001')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/users/reset-key', methods=['POST'])
@verify_auth('CDE001')
def reset_key():
    password        = request.form['input']
    password_user   = hash_key(password)
    id_user         = session.get('id_user')

    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute('''
            UPDATE users 
            SET password_user = ?
            WHERE id_user     = ?;
        ''',
        (password_user, id_user))

        connection.commit()

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

    return redirect(url_for('index'))


@app.route('/searching', methods=['POST'])
@verify_auth('CDE001')
def searching():
    codigo = re.sub(r'[^0-9;]', '', (request.form['cod_str_qr'].strip()))
    print(f'Código fornecido: {codigo}')
    
    if len(codigo) == 4 or len(codigo) == 0:
        desc_item, cod_item, cod_lote, cod_linha = 'ITEM NÃO CADASTRADO', '', '', ''
        return jsonify({'codITEM': cod_item, 'descITEM': desc_item, 'codLOTE': cod_lote, 'codLINHA': cod_linha})

    else:                                                                       #? VALIDAÇÃO P/ CÓDIGO INTERNO SEM ';'
        if len(codigo) == 6:
            codigo = codigo + ';'

        partes = codigo.split(';')
        cod_item = []

        if len(partes) == 1:
            cod_barra = partes[0]

            with sqlite3.connect(db_path) as connection:
                cursor = connection.cursor()
                cursor.execute('''
                    SELECT desc_item, cod_item
                    FROM itens
                    WHERE dun14 = ?
                    ORDER BY cod_item;
                ''',
                (cod_barra,))

                rows = cursor.fetchall()

                for row in rows:
                    codigos_itens = row[1]
                    cod_item.append(codigos_itens)
                    cod_item_qnt = len(cod_item)
                
                if cod_item:
                    with sqlite3.connect(db_path) as connection:                #// TODO: if cod_item (implementar após descobrir o caso de erro)
                        cursor = connection.cursor()
                        cursor.execute('''
                            SELECT desc_item    
                            FROM itens
                            WHERE cod_item = ?
                            ORDER BY cod_item;
                        ''',
                        (cod_item[0],))

                    row = cursor.fetchall()
                    print('[DEBUG] DESC_ITEM: ' + row[0][0])

                    if row:
                        desc_item = row[0][0]
                        if 'VINHO' in desc_item:
                            cod_lote = 'VINHO'
                        else:
                            cod_lote = ''
                else:
                    desc_item, cod_item, cod_lote = 'ITEM NÃO CADASTRADO', '', ''

                return jsonify({'codITEM': cod_item, 'descITEM': desc_item, 'codLOTE': cod_lote, 'codITEMqnt': cod_item_qnt})

        elif len(partes) == 2:
            codigos_itens = partes[0]
            cod_item.append(codigos_itens)

            if partes[1] != '':
                cod_lote = 'CS' + partes[1]
            else:
                cod_lote = ''

            with sqlite3.connect(db_path) as connection:
                cursor = connection.cursor()
                cursor.execute('''
                    SELECT desc_item
                    FROM itens
                    WHERE cod_item = ?;
                ''', 
                (codigos_itens,))

                resultado = cursor.fetchone()
                if resultado is not None:
                    desc_item = resultado[0]
                    if 'VINHO' in desc_item:
                        cod_lote = 'VINHO'
                else:
                    desc_item, cod_item, cod_lote = 'ITEM NÃO CADASTRADO', '', ''

                return jsonify({'codITEM': cod_item, 'codLOTE': cod_lote, 'descITEM': desc_item})

        else:
            desc_item, cod_item, cod_lote = 'ITEM NÃO CADASTRADO', '', ''
            return jsonify({'codITEM': cod_item, 'codLOTE': cod_lote, 'descITEM': desc_item})


@app.route('/mov')                                                                                                                      # ROTA DE MOVIMENTAÇÃO NO ESTOQUE (/mov)
@verify_auth('MOV002')
def mov():
    create_tables()
    end_lote = get_end_lote()

    return render_template('pages/mov/mov.html', saldo_atual=end_lote)


@app.route('/mov/historico')
@verify_auth('MOV003')
def historico():
    create_tables()
    page = request.args.get('page', 1, type=int)
    per_page = 20
    estoque, row_count = get_historico(page, per_page)
    total_pages = ceil(row_count / per_page)
    return render_template('pages/mov/mov-historico.html', estoque=estoque, page=page, total_pages=total_pages, max=max, min=min, row_count=row_count)


@app.route('/mov/historico/search', methods=['GET', 'POST'])
@verify_auth('MOV003')
def historico_search():
    create_tables()
    if request.method == 'POST':
        search_term = request.form['search_term']
        search_index = request.form['search_index']
        
        option_texts = {
            'cod_item': 'Produto (Código)',
            'desc_item': 'Produto (Descrição)',
            'endereco': 'Endereço',
            'operacao': 'Operação (Descrição)',
            'quantidade': 'Quantidade',
            'lote': 'Lote (Código)',
            'user_name': 'Usuário (Nome)',
            'timestamp': 'Horário (Data/Hora)'
        }

        search_row_text = option_texts.get(search_index, '')

        estoque = get_all_historico()
        filtered_estoque = [item for item in estoque if search_term.lower() in item[search_index].lower()]
        return render_template('pages/mov/mov-historico.html', estoque=filtered_estoque, search_term=search_term, page = 0, max=max, min=min, total_pages=0, search_row_text=search_row_text)
    return render_template('pages/mov/mov-historico.html', estoque=[], search_term="", page = 0, max=max, min=min, total_pages=0, search_row_text=search_row_text)



@app.route('/mov/faturado')
@verify_auth('MOV005')
def faturado():
    create_tables()
    end_lote = get_end_lote_fat()

    return render_template('pages/mov/mov-faturado.html', saldo_atual=end_lote)


@app.route('/mov/moving', methods=['POST'])                                                                                             # ROTA DE MOVIENTAÇÃO NO ESTOQUE (/mov/MOVING)
@verify_auth('MOV002')
def moving():
    numero          = int(request.form['end_number'])
    letra           = str(request.form['end_letra'])
    operacao        = str(request.form['operacao'])
    is_end_completo = bool(request.form.get('is_end_completo'))
    id_carga        = 0

    timestamp_br    = datetime.now(timezone(timedelta(hours=-3)))
    timestamp_out   = timestamp_br.strftime('%Y/%m/%d %H:%M:%S')
    timestamp_in    = (timestamp_br + timedelta(seconds=1)).strftime('%Y/%m/%d %H:%M:%S')

    print(f'OPERAÇÃO: {operacao}')

    if is_end_completo:                                                                                                                 # MOVIMENTA ENDEREÇO COMPLETO
        items = select_rua(letra, numero)
        print(f'ENDEREÇO COMPLETO ({letra}.{numero}): {items}')

    else:
        cod_item   = str(request.form['codsku'])
        lote_item  = str(request.form['lote'])
        quantidade = int(request.form['quantidade'])
        items      = [(cod_item, lote_item, quantidade)]                                                                                # MOVIMENTA ITEM ÚNICO
        print(f'ITEM ÚNICO ({letra}.{numero}): {items}')

        saldo_item  = int(get_saldo_item(numero, letra, cod_item, lote_item))
        if operacao in ('S', 'T', 'F') and quantidade > saldo_item:                                                                     #? IMPOSSIBILITA ESTOQUE NEGATIVO 
            alerta_tipo     = 'OPERAÇÃO CANCELADA \n'
            alerta_mensagem = 'O saldo do item selecionado é INSUFICIENTE. \n'
            alerta_mais     = ('''POSSÍVEIS SOLUÇÕES:
                            - Verifique se está movimentando o item correspondente.
                            - Verifique a quantidade de movimentação.
                            - Verifique a operação selecionada. ''')
            
            return render_template('components/menus/alert.html', alerta_tipo=alerta_tipo,
                                    alerta_mensagem=alerta_mensagem,
                                    alerta_mais=alerta_mais, url_return=url_for('mov'))

    if operacao == 'T':                                                                                                                 #* TRANSFERENCIA
        destino_letter  = str(request.form['destino_end_letra'])
        destino_number  = int(request.form['destino_end_number'])

        if items:
            for item in items:
                cod_item, lote_item, quantidade = item
                if quantidade > 0:
                    insert_historico(numero, letra, cod_item, lote_item, quantidade, 'TS', timestamp_out, id_carga)                     #? SAÍDA DO ENDEREÇO DE ORIGEM
                    insert_historico(destino_number, destino_letter, cod_item, lote_item, quantidade, 'TE', timestamp_in, id_carga)     #? ENTRADA NO ENDEREÇO DE DESTINO
                    print(f'{letra}.{numero} >> {destino_letter}.{destino_number}: ', cod_item, lote_item, quantidade)
        
    elif operacao == 'F':                                                                                                               #* FATURAMENTO
        id_carga = str(request.form['id_carga']) + str(request.form['id_carga_seq'])

        if items:
            for item in items:
                cod_item, lote_item, quantidade = item
                if quantidade > 0:
                    insert_historico(numero, letra, cod_item, lote_item, quantidade, operacao, timestamp_out, id_carga)
                    print(f'{letra}.{numero}: ', cod_item, lote_item, quantidade)

    elif operacao == 'E' or operacao == 'S':                                                                                            #* OPERAÇÃO PADRÃO (entrada 'E' ou saída 'S')
        insert_historico(numero, letra, cod_item, lote_item, quantidade, operacao, timestamp_out, id_carga)
        print(f'{letra}.{numero}: ', cod_item, lote_item, quantidade)
    
    else:                                                                                                                               #* OPERAÇÃO INVÁLIDA
        print(f'[ERRO] {letra}.{numero}: ', cod_item, lote_item, quantidade, ': OPERAÇÃO INVÁLIDA')

    return redirect(url_for('mov'))


@app.route('/get/clientes', methods=['GET'])                                                                                            # RETORNA FANTASIA CLIENTES (PARA SELECT2)
@verify_auth('CDE001')
def get_fant_clientes():
    with sqlite3.connect(db_path) as connection:                                                                                        # TODO: criar função auxiliar
        cursor = connection.cursor()
        cursor.execute('''
            SELECT DISTINCT fantasia_cliente 
            FROM clientes;
        ''')

        fant_clientes = [{
            'fantasia_cliente': row[0]
        } for row in cursor.fetchall()]

    return fant_clientes


@app.route('/envase', methods=['GET'])
@verify_auth('ENV006')
def envase():
    create_tables()
    envase_list = get_envase()

    return render_template('pages/envase/envase.html', envase=envase_list)


@app.route('/envase/calendar')
@verify_auth('ENV008')
def calendar_envase():
    create_tables()
    envase_list = get_envase()
    return render_template('pages/envase/envase-calendar.html', envase=envase_list)


@app.route('/envase/delete/<id_envase>')
@verify_auth('ENV007')
def delete_item(id_envase):
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute('''
            DELETE 
            FROM envase
            WHERE id_envase = ?;
        ''', 
        (id_envase,))

    return redirect(url_for('envase'))


@app.route('/envase/concl/<id_envase>')
@verify_auth('ENV006')
def conclude_item(id_envase):
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute('''
            UPDATE envase
            SET concluido = true
            WHERE id_envase = ?;
        ''',
        (id_envase,))

    return redirect(url_for('envase'))


@app.route('/envase/nao-concl/<id_envase>')
@verify_auth('ENV007')
def not_conclude_item(id_envase):
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute('''
            UPDATE envase
            SET concluido = false
            WHERE id_envase = ?;
        ''',
        (id_envase,))

    return redirect(url_for('envase'))


@app.route('/envase/edit', methods=['GET', 'POST'])
@verify_auth('ENV007')
def envase_edit():                                                                                                                      # TODO: criar função auxiliar
    if request.method == 'POST':

        req_id_envase   = request.form['id_envase']
        quantidade      = request.form['quantidade']
        data_entr_antec = request.form['data_antec']
        data_envase     = request.form['data_envase']
        observacao      = re.sub(r'\r\n|\r|\n|<br>', ' ', request.form['observacao'])

        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            cursor.execute('''
                UPDATE envase
                SET quantidade = ?,
                    data_entr_antec = ?,
                    data_envase = ?,
                    observacao = ?
                WHERE id_envase = ?;
            ''',
            (quantidade, data_entr_antec, data_envase, observacao, req_id_envase))

        return redirect(url_for('envase'))
    else:
        req_id_envase = request.args.get('id_envase')

        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            cursor.execute('''
                SELECT p.linha, c.fantasia_cliente, i.cod_item,
                            i.desc_item, p.quantidade, p.data_entr_antec,
                            p.data_envase, p.observacao, p.id_envase,
                            p.concluido
                FROM envase p
                JOIN itens i ON p.cod_item = i.cod_item
                JOIN clientes c ON p.cod_cliente = c.cod_cliente
                WHERE id_envase = ?;
            ''',
            (req_id_envase,))

            env_edit = [{
                'linha'      : row[0], 'fantasia_cliente': row[1], 'cod_item'       : row[2],
                'desc_item'  : row[3], 'quantidade'      : row[4], 'data_entr_antec': row[5],
                'data_envase': row[6], 'observacao'      : row[7], 'id_envase'      : row[8],
                'concluido'  : row[9]
            } for row in cursor.fetchall()]

        return render_template('pages/envase/envase-edit.html', env_edit=env_edit)


@app.route('/envase/insert', methods=['POST'])
@verify_auth('ENV006')
def insert_envase():                                                                                                                    # TODO: criar função auxiliar
    if request.method == 'POST':
        linha           = request.form['linha']
        cod_item        = request.form['codinterno']
        quantidade      = request.form['quantidade']
        data_entr_antec = request.form['data_antec']
        data_envase     = request.form['data_envase']
        cliente         = request.form['cliente']
        observacao      = re.sub(r'\r\n|\r|\n|<br>', ' ', request.form['observacao'])

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
                INSERT INTO envase (
                    linha, cod_cliente, cod_item,
                    quantidade, data_entr_antec, data_envase,
                    observacao, concluido ) 
                VALUES (
                    ?, ?, ?,
                    ?, ?, ?,
                    ?, false );
            ''',
            (linha, cod_cliente, cod_item, 
             quantidade, data_entr_antec, data_envase,
             observacao))
            
            connection.commit()
    return redirect(url_for('envase'))


@app.route('/processamento', methods=['GET'])
@verify_auth('PRC010')
def producao():
    create_tables()
    id_user = session.get('id_user')
    user_permissions = get_user_permissions(id_user)
    user_permissions = [item['id_perm'] for item in user_permissions]
    producao_list = get_producao()
    
    return render_template('pages/processamento/processamento.html', producao=producao_list, user_permissions=user_permissions)


@app.route('/processamento/calendar')
@verify_auth('PRC012')
def calendar_producao():
    create_tables()
    producao_list = get_producao()

    return render_template('pages/processamento/processamento-calendar.html', producao=producao_list)


@app.route('/processamento/delete/<id_producao>')
@verify_auth('PRC011')
def delete_producao(id_producao):
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute('''
            DELETE 
            FROM producao 
            WHERE id_producao = ?;
        ''', 
        (id_producao,))

    return redirect(url_for('producao'))


@app.route('/processamento/concl/<id_producao>')
@verify_auth('PRC010')
def conclude_producao(id_producao):
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute('''UPDATE producao
                          SET concluido = true
                          WHERE id_producao = ?;
                          ''', (id_producao,))
    return redirect(url_for('producao'))


@app.route('/processamento/nao-concl/<id_producao>')
@verify_auth('PRC011')
def not_conclude_producao(id_producao):
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute('''
            UPDATE producao
            SET concluido = false
            WHERE id_producao = ?;
        ''',
        (id_producao,))

    return redirect(url_for('producao'))


@app.route('/processamento/edit', methods=['GET', 'POST'])
@verify_auth('PRC011')
def producao_edit():
    create_tables()
    id_user = session.get('id_user')
    user_permissions = get_user_permissions(id_user)
    user_permissions = [item['id_perm'] for item in user_permissions]
    if request.method == 'POST':
        req_id_producao = request.form['id_producao']
        litros          = request.form['litros']
        data_entr_antec = request.form['data_antec']
        data_producao   = request.form['data_producao']
        observacao      = re.sub(r'\r\n|\r|\n|<br>', ' ', request.form['observacao'])

        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            cursor.execute('''
                UPDATE producao
                SET litros   = ?,
                    data_entr_antec = ?,
                    data_producao = ?,
                    observacao = ?
                WHERE id_producao = ?;
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
                    SELECT  p.linha, p.liq_linha, p.liq_cor, p.embalagem,
                            p.litros, p.data_entr_antec, p.data_producao,
                            p.observacao, p.id_producao, p.concluido,
                            p.liq_tipo
                    FROM producao p
                    WHERE ? = p.id_producao
                    ORDER BY p.data_producao;
                ''', 
                (req_id_producao,))

                prod_edit = [{
                    'linha'        : row[0], 'liq_linha' : row[1], 'liq_cor'        : row[2],
                    'embalagem'    : row[3], 'litros'    : row[4], 'data_entr_antec': row[5],
                    'data_producao': row[6], 'observacao': row[7], 'id_producao'    : row[8],
                    'concluido'    : row[9], 'liq_tipo'  : row[10]
                } for row in cursor.fetchall()]

        else:
            mode = 'onlyConcluded'
            prod_edit = get_producao()

        return render_template('pages/processamento/processamento-edit.html', prod_edit=prod_edit, user_permissions=user_permissions, mode=mode)


@app.route('/processamento/insert', methods=['POST'])
@verify_auth('PRC010')
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
        observacao      = re.sub(r'\r\n|\r|\n|<br>', ' ', request.form['observacao'])

        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            cursor.execute(''' 
                INSERT INTO producao (  
                    linha, liq_linha, liq_cor,
                    embalagem, litros, data_entr_antec,
                    data_producao, observacao, liq_tipo, 
                    concluido ) 
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


@app.route('/users/edit', methods=['POST', 'GET'])
@verify_auth('CDE016')
def users_edit():
    create_tables()

    req_id_user = request.args.get('id_user')
    if request.method == 'POST':
        pass

    else:
        user_permissions = get_user_permissions(req_id_user)
        permissions = get_permissions()
        return render_template('pages/users/users-edit.html', user_permissions=user_permissions,
                               permissions=permissions, req_id_user=req_id_user,
                               user_data=get_userdata(req_id_user))


@app.route('/users/remove-perm/<int:id_user>/<string:id_perm>', methods=['GET', 'POST'])
@verify_auth('CDE016')
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
@verify_auth('CDE016')
def add_permission(id_user, id_perm):
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute('''
            INSERT INTO user_permissions (
                id_user, id_perm ) 
            VALUES (
                ?, ? );
        ''', 
        (id_user, id_perm))

        connection.commit()

    return redirect(url_for('users_edit', id_user=id_user))


@app.route('/users/inserting', methods=['POST'])
@verify_auth('CDE016')
def cadastrar_usuario():
    if request.method == 'POST':

        login_user      = str(request.form['login_user'])
        nome_user       = str(request.form['nome_user'])
        sobrenome_user  = str(request.form['sobrenome_user'])
        privilege_user  = int(request.form['privilege_user'])
        data_cadastro   = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        password_user   = hash_key(request.form['password_user'])

        try:
            with sqlite3.connect(db_path) as connection:
                cursor = connection.cursor()
                cursor.execute('''
                    INSERT INTO users (
                        login_user, password_user, nome_user,
                        sobrenome_user, privilege_user, data_cadastro ) 
                    VALUES (?, ?, ?,
                            ?, ?, ? );
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
                            id_user, id_perm ) 
                        VALUES (
                            ?, ? );
                    ''',
                    (id_user, 'CDE001'))
                    connection.commit()

                    user_name = session.get('user_name')
                    id_user   = session.get('id_user')

                    msg = \
                    f'''
                    [CADASTRO]
                    {request.remote_addr}
                    {id_user} - {user_name} [+] {nome_user} {sobrenome_user} ({privilege_user})
                    '''
                    tlg_msg(msg)

        except sqlite3.IntegrityError as e:
            if 'UNIQUE constraint failed' in str(e):
                alerta_tipo     = 'CADASTRO (USUÁRIO) \n'
                alerta_mensagem = 'Não foi possível criar usuário... \n'
                alerta_mais     = ('''MOTIVO:
                               - Já existe um usuário com este login.''')
                return render_template('components/menus/alert.html', 
                                       alerta_tipo=alerta_tipo,
                                       alerta_mensagem=alerta_mensagem,
                                       alerta_mais=alerta_mais, 
                                       url_return=url_for('users'))
            else:
                print('Erro: ', e)
                alerta_tipo     = 'CADASTRO (USUÁRIO) \n'
                alerta_mensagem = 'Não foi possível criar usuário... \n'
                alerta_mais     = (f'''DESCRIÇÃO DO ERRO:
                               - {e}. \n''')
                return render_template('components/menus/alert.html', 
                                       alerta_tipo=alerta_tipo,
                                       alerta_mensagem=alerta_mensagem,
                                       alerta_mais=alerta_mais, 
                                       url_return=url_for('users'))
        else:
            return redirect(url_for('users'))
    return render_template('pages/users/users.html')


@app.route('/mov/carga/<int:id_carga>', methods=['GET', 'POST'])
@verify_auth('MOV006')
def carga_id(id_carga):
    item_query = ''
    result_local, columns_local = [], []
    if request.method == 'GET':
        cod_item = request.args.get('cod_item', '')
        print(cod_item)
        if cod_item:
            query = f'''
                SELECT  h.rua_numero, h.rua_letra, i.cod_item, 
                        i.desc_item, h.lote_item,
                        SUM(
                            CASE 
                            WHEN operacao = 'E'
                            OR operacao = 'TE'
                            THEN quantidade 
                            
                            WHEN operacao = 'S' 
                            OR operacao = 'TS' 
                            OR operacao = 'F' 
                            THEN (quantidade * -1)

                            ELSE (quantidade * 0)
                            END
                        ) as saldo
                FROM historico h

                JOIN itens i 
                ON h.desc_item = i.cod_item

                WHERE i.cod_item = "{str(cod_item)}"
                
                GROUP BY  h.rua_numero, h.rua_letra, 
                          h.desc_item, h.lote_item
                HAVING saldo != 0

                ORDER BY h.lote_item DESC, h.rua_letra ASC,
                         h.rua_numero ASC, i.desc_item ASC;
            '''
            dsn_name = 'SQLITE'
            dsn = dsn_name
            result_local, columns_local = db_query_connect(query, dsn)

            item_query = f'AND iped.ITEM = "{cod_item}"'


        #? SEARCH DE ITENS POR CARGA
        query = f'''
            SELECT  crg.CODIGO_GRUPOPED                   AS NRO_CARGA,
                    crg.NRO_PEDIDO                        AS NRO_PEDIDO,
                    (iped.NRO_PEDIDO || '.' || iped.SEQ)  AS NROPED_SEQ,
                    CAST(iped.ITEM AS VARCHAR(255))       AS COD_ITEM,
                    i.ITEM_DESCRICAO                      AS DESC_ITEM,
                    CAST(iped.QTDE_SOLICITADA AS INTEGER) AS QTDE_SOLIC
            FROM DB2ADMIN.ITEMPED iped

            JOIN DB2ADMIN.IGRUPOPE crg
            ON crg.NRO_PEDIDO = iped.NRO_PEDIDO
            AND crg.SEQ = iped.SEQ

            JOIN DB2ADMIN.HUGO_PIETRO_VIEW_ITEM i 
            ON i.ITEM = iped.ITEM

            WHERE crg.CODIGO_GRUPOPED = '{id_carga}' 
            AND iped.DT_EMISSAO BETWEEN (CURRENT DATE - 3 MONTHS)
            AND CURRENT DATE

            LIMIT 100;
        '''
        """ #! ANTIGA QUERY
            SELECT crg.CODIGO_GRUPOPED, iped.ITEM,
                   i.ITEM_DESCRICAO,
                   CAST(crg.QTDE AS INTEGER) AS QTDE_SOLICITADA
            FROM DB2ADMIN.IGRUPOPE crg
            JOIN DB2ADMIN.PEDIDO ped ON crg.NRO_PEDIDO = ped.NRO_PEDIDO
            JOIN DB2ADMIN.ITEMPED iped ON crg.RECNUM = iped.RECNUM
            JOIN DB2ADMIN.CLIENTE cl ON cl.CODIGO_CLIENTE = ped.CODIGO_CLIENTE
            JOIN DB2ADMIN.HUGO_PIETRO_VIEW_ITEM i ON i.ITEM = iped.ITEM
            WHERE crg.QTDE_FATUR != 0               -- apenas faturados
            -- AND iped.NRO_PEDIDO = ?              -- filtro por pedido
            AND crg.CODIGO_GRUPOPED = '{id_carga}'  -- filtro por carga
            AND ped.DT_EMISSAO BETWEEN (CURRENT DATE - 2 MONTHS) AND CURRENT DATE
            ORDER BY crg.CODIGO_GRUPOPED DESC, crg.NRO_PEDIDO, crg.SEQ;
        """
        dsn_name = 'HUGOPIET'
        dsn = dsn_name
        result, columns = db_query_connect(query, dsn)
        if columns:
            alert = f'Última atualização em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}'
            class_alert = 'success'

        else:
            alert = f'''{result[0][0]}'''
            class_alert = 'error'
        return render_template('pages/mov/mov-carga.html',
                               result=result, columns=columns, alert=alert,
                               class_alert=class_alert, id_carga=id_carga, cod_item=cod_item,
                               result_local=result_local, columns_local=columns_local)
    result = []
    return render_template('pages/mov/mov-carga.html', result=result, columns=columns)
        

@app.route('/mov/carga', methods=['GET', 'POST'])
@verify_auth('MOV006')
def cargas():                                                                                       #TODO: BOTÃO PARA TRAZER CARGAS
    if request.method == 'POST':
        query = '''
            SELECT DISTINCT 
                crg.CODIGO_GRUPOPED AS NRO_CARGA,
                crg.NRO_PEDIDO      AS NRO_PEDIDO,
                ped.CODIGO_CLIENTE  AS COD_CLIENTE,
                cl.FANTASIA         AS FANT_CLIENTE,
                iped.DT_EMISSAO     AS DT_EMISSAO,
                iped.DT_ENTREGA     AS DT_ENTREGA

            FROM DB2ADMIN.ITEMPED iped

            JOIN DB2ADMIN.IGRUPOPE crg
            ON crg.NRO_PEDIDO = iped.NRO_PEDIDO
            AND crg.SEQ = iped.SEQ

            JOIN DB2ADMIN.PEDIDO ped
            ON crg.NRO_PEDIDO = ped.NRO_PEDIDO

            JOIN DB2ADMIN.CLIENTE cl
            ON cl.CODIGO_CLIENTE = ped.CODIGO_CLIENTE

            JOIN DB2ADMIN.HUGO_PIETRO_VIEW_ITEM i 
            ON i.ITEM = iped.ITEM

            WHERE crg.QTDE_FATUR != 0
            AND iped.DT_EMISSAO BETWEEN (CURRENT DATE - 3 MONTHS)
            AND CURRENT DATE

            ORDER BY crg.CODIGO_GRUPOPED DESC, iped.DT_EMISSAO DESC;
        '''
        """ #! ANTIGA QUERY
            SELECT crg.CODIGO_GRUPOPED, crg.NRO_PEDIDO, crg.SEQ,
                   ped.CODIGO_CLIENTE, cl.FANTASIA, iped.ITEM,
                   ped.DT_EMISSAO
            FROM DB2ADMIN.IGRUPOPE crg
            JOIN DB2ADMIN.PEDIDO ped ON crg.NRO_PEDIDO = ped.NRO_PEDIDO
            JOIN DB2ADMIN.CLIENTE cl ON cl.CODIGO_CLIENTE = ped.CODIGO_CLIENTE
            JOIN DB2ADMIN.ITEMPED iped ON crg.RECNUM = iped.RECNUM
            WHERE crg.QTDE_FATUR != 0
            AND ped.DT_EMISSAO BETWEEN (CURRENT DATE - 2 MONTHS) AND CURRENT DATE
            ORDER BY crg.CODIGO_GRUPOPED DESC, crg.NRO_PEDIDO, crg.SEQ;
        """
        
        dsn_name = 'HUGOPIET'
        dsn = dsn_name
        result, columns = db_query_connect(query, dsn)
        if columns:
            alert = f'Última atualização em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}'
            class_alert = 'success'

        else:
            alert = f'''{result[0][0]}'''
            class_alert = 'error'
        return render_template('pages/mov/mov-carga.html', result=result, columns=columns, alert=alert, class_alert=class_alert)
    result = []
    return render_template('pages/mov/mov-carga.html', result=result)


@app.route('/produtos', methods=['GET', 'POST'])
@verify_auth('ITE005')
def produtos():
    itens = get_itens()
    if request.method == 'POST':
        query = '''
            SELECT i.ITEM, i.ITEM_DESCRICAO, i.GTIN_14
            FROM DB2ADMIN.HUGO_PIETRO_VIEW_ITEM i
            WHERE (
                   UNIDADE_DESCRICAO = 'CX' 
                OR UNIDADE_DESCRICAO = 'UN' 
                OR UNIDADE_DESCRICAO = 'FD'
            )
            AND (
                   GRUPO_DESCRICAO = 'PRODUTO ACABADO' 
                OR GRUPO_DESCRICAO = 'REVENDA'
            )
            AND NOT GTIN_14 = '';
        '''

        dsn_name = 'HUGOPIET'
        dsn = dsn_name
        result, columns = db_query_connect(query, dsn)

        if columns:
            alert = f'Última atualização em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}'
            class_alert = 'success'
            with sqlite3.connect(db_path) as connection:
                cursor = connection.cursor()
                cursor.execute('BEGIN TRANSACTION;')
                cursor.execute('DELETE FROM itens;')
                cursor.executemany('''
                    INSERT INTO itens (cod_item, desc_item, dun14)
                    VALUES (?,?,?);
                ''', result)
                
                connection.commit()
        else:
            """
            if request.method == 'POST':
                desc_item   = request.form['desc_item']
                cod_item    = request.form['cod_item']
                dun14       = request.form['cod_dun14']
                
                with sqlite3.connect(db_path) as connection:
                    cursor = connection.cursor()
                    cursor.execute('''
                        INSERT INTO itens
                        VALUES (?,?,?);
                    ''',
                    (cod_item, desc_item, dun14))

                    connection.commit()
                msg = f'''
                [CADASTRO ITEM] [+]
                {cod_item}
                {desc_item}
                ({dun14})
                '''
                tlg_msg(msg)
            
                return redirect(url_for('produtos'))
            """
            alert = f'''{result[0][0]}'''
            class_alert = 'error'
        itens = get_itens()
        return render_template('pages/produtos.html', itens=itens, alert=alert, class_alert=class_alert)
    return render_template('pages/produtos.html', itens=itens)


@app.route('/etiqueta', methods=['GET', 'POST'])
@verify_auth('OUT014')
def etiqueta():
    if request.method == 'POST':
        qr_text     = str(request.form['qr_text'])
        desc_item   = str(request.form['produto'])
        cod_item    = str(request.form['codsku'])
        lote        = str(request.form['lote_item'])

        return generate_etiqueta(qr_text, desc_item, cod_item, lote)

    return render_template('pages/etiqueta.html', produtos=produtos)


@app.route('/rotulo', methods=['GET', 'POST'])
@verify_auth('OUT015')
def rotulo():
    if request.method == 'POST':
        espessura_fita      = parse_float(request.form['espessura_fita'])
        diametro_inicial    = parse_float(request.form['diametro_inicial'])
        diametro_minimo     = parse_float(request.form['diametro_minimo'])
        espessura_papelao   = parse_float(request.form['espessura_papelao'])
        compr_rotulo        = parse_float(request.form['compr_rotulo'])
        comprimento_total   = 0     # INICIALIZA
        num_voltas          = 0     # INICIALIZA

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

            num_rotulos_str = f"{num_rotulos:_.0f}".replace('.', ',').replace('_', '.')
            comprimento_mtrs = f"{(comprimento_total / 1000):_.2f}".replace('.', ',').replace('_', '.')

            return jsonify({'num_rotulos_str': num_rotulos_str,
                            'num_voltas': num_voltas,
                            'comprimento_mtrs': comprimento_mtrs})
        else:
            return jsonify({'num_rotulos_str': 0,
                            'num_voltas': 0,
                            'comprimento_mtrs': "0,00"})

    return render_template('pages/rotulo.html')


@app.route('/buscar_linhas', methods=['POST'])
@verify_auth('ENV006')
def buscar_linhas():
    desc_item = request.form['produto']

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
                    print(f'EMBALAGEM {tipo} {volume}')
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

            return jsonify({'cod_linha': cod_linha})
        else:
            cod_linha = ''
            return jsonify({'codLINHA': cod_linha})


@app.route('/saldo')
@verify_auth('MOV004')
def saldo():
    saldo_visualization = get_saldo_view()
    return render_template('pages/estoque.html', saldo_visualization=saldo_visualization)


@app.route('/export_csv/<tipo>', methods=['GET'])
@verify_auth('CDE018')
def export_csv_tipo(tipo):                                                                                                              #* EXPORT .csv
    if tipo == 'historico':
        data = get_all_historico()
        filename = 'exp_historico'
    elif tipo == 'produtos':
        data = get_itens()
        filename = 'exp_produtos'
    elif tipo == 'saldo':
        data = get_end_lote()
        filename = 'exp_saldo_lote'
    elif tipo == 'faturado':
        data = get_end_lote_fat()
        filename = 'exp_faturado'
    elif tipo == 'estoque':
        data = get_saldo_view()
        filename = 'exp_estoque'
    elif tipo == 'envase':
        data = get_envase()
        filename = 'exp_prog_envase'
    elif tipo == 'producao':
        data = get_producao()
        filename = 'exp_prog_producao'
    else:
        alerta_tipo     = 'DOWNLOAD IMPEDIDO \n'
        alerta_mensagem = 'A tabela não tem informações suficientes para exportação. \n'
        alerta_mais     = ('''POSSÍVEIS SOLUÇÕES:
                       - Verifique se a tabela possui mais de uma linha.
                       - Contate o suporte. ''')
        return render_template('components/menus/alert.html', alerta_tipo=alerta_tipo, alerta_mensagem=alerta_mensagem,
                               alerta_mais=alerta_mais, url_return=url_for('index'))
    return export_csv(data, filename)


if __name__ == '__main__':                                                                                                              #! __MAIN__

    app.config['APP_VERSION'] = ['0.4.1', 'Junho/2024', False]

    # GET nome do diretório
    dir_os        = os.path.dirname(os.path.abspath(__file__))
    debug_dir     = os.getenv('DEBUG_DIR').split(';')
    main_exec_dir = os.getenv('MAIN_EXEC_DIR')

    # MISC
    exec_head   = \
        f'''                                                                     
                                                                     
        CCCCCCCCCCCC    DDDDDDDDDDDD           EEEEEEEEEEEEEEEEEEEEEE
     CCC:::::::::::C    D:::::::::::DDD        E::::::::::::::::::::E
   CC::::::::::::::C    D::::::::::::::DD      E::::::::::::::::::::E
  C::::::CCCCCCCCCCC    DDDDDDDDDDD::::::D     EEEEEEEEEEEEEEEEEEEEEE
 C:::::CC                          DD:::::D                          
C:::::C                              D:::::D                         
C:::::C                              D:::::D   EEEEEEEEEEEEEEEEEEEE  
C:::::C                              D:::::D   E::::::::::::::::::E  
C:::::C                              D:::::D   EEEEEEEEEEEEEEEEEEEE  
C:::::C                              D:::::D                         
 C:::::CC                          DD:::::D                          
  C::::::CCCCCCCCCCC    DDDDDDDDDDD::::::D     EEEEEEEEEEEEEEEEEEEEEE
   CC::::::::::::::C    D::::::::::::::DD      E::::::::::::::::::::E
     CCC:::::::::::C    D:::::::::::DDD        E::::::::::::::::::::E
        CCCCCCCCCCCC    DDDDDDDDDDDD           EEEEEEEEEEEEEEEEEEEEEE
                                                                     
        '''
    start_head  = \
        f'''
    * Started in: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
    * Versão CDE: {app.config['APP_VERSION'][0]} (beta) - {app.config['APP_VERSION'][1]}
    * Versão Python: {sys.version}
        '''
    error_foot  = \
        f'''
    [ERRO 002] 
    * Impossível executar, verifique se o arquivo está alocado corretamente.

    Pressione ENTER para sair...
            '''

    if dir_os in debug_dir:         # Se o user for listado dev, modo_exec = debug
        db_path = os.getenv('DEBUG_DB_PATH')
        port, debug = 5100, True
        app.config['APP_VERSION'][2] = True
        print(start_head)

    elif main_exec_dir in dir_os:   # Se o diretório atende ao local para produção, modo_exec = produção.
        db_path = os.getenv('DB_PATH')
        port, debug = 5005, False
        print(exec_head, start_head)

    else:                           # Se o diretório não atende aos requisitos plenos de funcionamento, não executa.
        print(error_foot)
        sys.exit(2)

    app.run(host='0.0.0.0', port=port, debug=debug)
