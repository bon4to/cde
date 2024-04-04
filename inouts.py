import textwrap
import requests
import sqlite3
import qrcode
import base64
import io
import re
import os
import sys

from flask import Flask, Response, request, redirect, render_template, url_for, jsonify, session, abort
from datetime import datetime, timezone, timedelta
from PIL import Image, ImageDraw, ImageFont
from passlib.hash import pbkdf2_sha256
from dotenv import load_dotenv
from functools import wraps
from math import pi


app = Flask(__name__)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=90)

# dotENV
load_dotenv()
db_path = os.getenv('DB_PATH')
app.secret_key = os.getenv('SECRET_KEY')


# preAPI
def tlg_msg(msg):
    bot_token = os.getenv('TLG_BOT_TOKEN')
    chat_id = os.getenv('TLG_CHAT_ID')
    url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
    params = {'chat_id': chat_id, 'text': msg}
    response = requests.post(url, params=params)
    return response.json()


@app.before_request
def renew_session():
    session.modified = True


@app.before_request
def check_session_expiry():
    if 'last_active' in session:
        last_active = session.get('last_active')
        expiration_time = app.config['PERMANENT_SESSION_LIFETIME']
        if isinstance(last_active, datetime):
            utc_now = datetime.now(timezone.utc)
            if (utc_now - last_active) > expiration_time:
                session.clear()
                return redirect(url_for('login'))
    session['last_active'] = datetime.now(timezone.utc)


@app.before_request
def check_ip():
    client_ip = request.remote_addr
    blacklist = os.getenv('BLACKLIST')
    if client_ip in blacklist:
        msg = f'{client_ip} na Blacklist.'
        tlg_msg(msg)
        abort(403)


def verify_aut_priv(must_privlg):
    def decorator(f):
        @wraps(f)
        def decorador(*args, **kwargs):
            if 'logged_in' in session:
                if session.get('privilegio') <= must_privlg:
                    return f(*args, **kwargs)
                else:
                    alerta_tipo = 'SEM PERMISSÕES \n'
                    alerta_mensagem = 'Você não tem permissão para acessar esta página.\n'
                    alerta_mais = ('''SOLUÇÕES:
                                   - Solicite ao seu supervisor um novo nível de acesso.
                                   ''')
                    return render_template('components/menus/alert.html', alerta_tipo=alerta_tipo, alerta_mensagem=alerta_mensagem,
                                           alerta_mais=alerta_mais, url_return=url_for('index'))
            else:
                return redirect(url_for('login'))
        return decorador
    return decorator


# GERADOR DE TABELAS
def create_tables():
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()

        # TABELA DE ITENS
        cursor.execute('''CREATE TABLE IF NOT EXISTS itens (
                            cod_item INTEGER(6) PRIMARY KEY,
                            desc_item VARCHAR(100),
                            dun14 INTEGER(14)
                            
                        )''')

        # TABELA DE PROGRAMAÇÃO DO ENVASE
        cursor.execute('''CREATE TABLE IF NOT EXISTS envase (
                            id_envase INTEGER PRIMARY KEY AUTOINCREMENT,
                            linha INTEGER(3),
                            cod_cliente INTEGER(10),
                            cod_item VARCHAR(6),
                            quantidade INTEGER,
                            data_entr_antec DATETIME,
                            data_envase DATETIME,
                            observacao VARCHAR(100),
                            concluido BOOLEAN

                        )''')

        # TABELA DE PROGRAMAÇÃO DA PRODUCAO
        cursor.execute('''CREATE TABLE IF NOT EXISTS producao (
                            id_producao INTEGER PRIMARY KEY AUTOINCREMENT,
                            linha INTEGER(3),
                            liq_tipo VARCHAR(10),
                            liq_linha VARCHAR(30),
                            liq_cor VARCHAR(30),
                            embalagem VARCHAR(10),
                            litros INTEGER,
                            data_entr_antec DATETIME,
                            data_producao DATETIME,
                            observacao VARCHAR(100),
                            concluido BOOLEAN

                        )''')

        # TABELA DE CLIENTES
        cursor.execute('''CREATE TABLE IF NOT EXISTS clientes (
                            cod_cliente INTEGER(10) PRIMARY KEY,
                            razao_cliente VARCHAR(100),
                            fantasia_cliente VARCHAR(100),
                            cidade_cliente VARCHAR(100),
                            estado_cliente VARCHAR(2)
                            
                        )''')

        # TABELA DE USUÁRIOS
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                            id_user INTEGER PRIMARY KEY AUTOINCREMENT,
                            login_user VARCHAR(30) UNIQUE,
                            password_user TEXT,
                            nome_user VARCHAR(100),
                            sobrenome_user VARCHAR(100),
                            privilege_user INTEGER(2),
                            data_cadastro DATETIME,
                            ult_acesso DATETIME
                            
                        )''')

        # TABELA DE PRIVILÉGIOS
        cursor.execute('''CREATE TABLE IF NOT EXISTS aux_privilege (
                            id_priv INTEGER(2) PRIMARY KEY,
                            desc_priv VARCHAR(30)

                        )''')

        # TABELA HISTÓRICO
        cursor.execute('''CREATE TABLE IF NOT EXISTS historico (
                            id_mov INTEGER PRIMARY KEY AUTOINCREMENT,
                            rua_numero INTEGER(6),
                            rua_letra  VARCHAR(10),
                            desc_item  VARCHAR(100),
                            lote_item  VARCHAR(8),
                            quantidade INTEGER,
                            operacao   VARCHAR(15),
                            user_name  VARCHAR(30),
                            time_mov   DATETIME
                            
                        )''')

        connection.commit()


# NOME DA ROTA
@app.context_processor
def inject_page():
    current_page = request.path
    if 'logged_in' in session:
        user_name = session.get('user_name')
        id_user = session.get('id_user')
        print(f"{id_user} - [{user_name}] | ", current_page)
    return {'current_page': current_page}


# RETORNA APENAS DESCRIÇÃO DO ITEM
def get_desc_itens():
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute('''SELECT DISTINCT desc_item
                          FROM itens
                          ORDER BY desc_item''')
        desc_item = [row[0] for row in cursor.fetchall()]
    return desc_item


# RETORNA TODOS OS PARÂMETROS DO ITEM
def get_itens():
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute('''SELECT DISTINCT *
                          FROM itens
                          ORDER BY desc_item''')
        itens = [{'cod_item': row[0], 'desc_item': row[1], 'dun14': row[2]} for row in cursor.fetchall()]
    return itens


# RETORNA TABELA DE PROGRAMAÇÃO
def get_producao():
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute('''SELECT  p.id_producao, p.linha, p.liq_linha,
                                  p.liq_cor, p.embalagem, p.litros,
                                  p.data_entr_antec, p.data_producao, p.observacao,
                                  p.concluido, p.liq_tipo
                          FROM producao p
                          ORDER BY p.data_producao;''')
        producao = [
            {'id_producao': row[0], 'linha': row[1], 'liq_linha': row[2], 'liq_cor': row[3], 'embalagem': row[4],
             'litros': row[5], 'data_entr_antec': row[6], 'data_producao': row[7], 'observacao': row[8],
             'concluido': row[9], 'liq_tipo': row[10]} for row in cursor.fetchall()
        ]
    return producao


def get_envase():
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute('''SELECT  p.id_envase, p.linha, c.fantasia_cliente,
                                  i.cod_item, i.desc_item, p.quantidade,
                                  p.data_entr_antec, p.data_envase, p.observacao,
                                  p.concluido
                          FROM envase p
                          JOIN itens i ON p.cod_item = i.cod_item
                          JOIN clientes c ON p.cod_cliente = c.cod_cliente
                          ORDER BY p.data_envase;''')
        envase = [{'id_envase': row[0], 'linha': row[1], 'fantasia_cliente': row[2],
                   'cod_item': row[3], 'desc_item': row[4], 'quantidade': row[5],
                   'data_entr_antec': row[6], 'data_envase': row[7],
                   'observacao': row[8], 'concluido': row[9]}
                  for row in cursor.fetchall()]
    return envase


# RETORNA MOVIMENTAÇÕES
def get_historico():
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute('''SELECT h.rua_numero, h.rua_letra, h.desc_item,
                                 h.lote_item, h.quantidade, h.operacao,
                                 h.user_name, h.time_mov
                          FROM historico h
                          ORDER BY time_mov DESC
        ''')
        estoque = [{
            'numero': row[0], 'letra': row[1], 'produto': row[2], 'lote': row[3], 'quantidade': row[4],
            'operacao': row[5], 'user_name': row[6], 'timestamp': row[7]
        } for row in cursor.fetchall()]
    return estoque


# RETORNA DADOS DOS USUÁRIOS
def get_users():
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute('''
            SELECT u.nome_user, u.sobrenome_user, ap.desc_priv,
                   u.ult_acesso, u.id_user
            FROM users u
            JOIN aux_privilege ap ON u.privilege_user = ap.id_priv
            ORDER BY u.ult_acesso DESC
        ''')

        users = [{
            'user_name': f'{row[0]} {row[1]}', 'privilegio': row[2], 'ult_acesso': row[3], 'cod_user': row[4],
        } for row in cursor.fetchall()]

    return users


def get_end_lote():
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute('''
            SELECT rua_numero, rua_letra, desc_item, lote_item, SUM(CASE 
                WHEN operacao = 'entrada' OR operacao = 'transf_entrada' THEN quantidade 
                WHEN operacao = 'saída' OR operacao = 'transf_saída' THEN (quantidade * -1)
                ELSE (quantidade * 0)
            END) as saldo
            FROM historico
            GROUP BY rua_numero, rua_letra, desc_item, lote_item
            HAVING saldo != 0
            ORDER BY desc_item
        ''')

        saldo_atual = [{
                'numero': row[0], 'letra': row[1], 'produto': row[2], 'lote': row[3], 'saldo': row[4]
            } for row in cursor.fetchall()]

    return saldo_atual


# HASH KEY
def hash_key(password):
    return pbkdf2_sha256.hash(password)


# CHECK HASHED KEY
def check_key(hashed_password, password):
    return pbkdf2_sha256.verify(password, hashed_password)


# FUNCTIONS
def get_saldo_for_export():
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute('''
            SELECT desc_item, saldo, time_mov
            FROM (
                SELECT desc_item, 
                       time_mov,
                       SUM(CASE 
                              WHEN operacao IN ('entrada', 'transf_entrada') THEN quantidade 
                              WHEN operacao IN ('saída', 'transf_saída') THEN (quantidade * -1)
                              ELSE (quantidade * -1)
                           END) as saldo,
                       ROW_NUMBER() OVER(PARTITION BY desc_item ORDER BY time_mov DESC) as rn
                FROM historico
                GROUP BY desc_item
                HAVING saldo != 0
            ) t
            WHERE rn = 1
            ORDER BY desc_item
        ''')

        saldo_export = [
            {'produto': row[0], 'saldo': row[1], 'timestamp': row[2]} for row in cursor.fetchall()
        ]

    return saldo_export


def get_saldo_item(numero, letra, produto, lote):
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute('''
            SELECT COALESCE(SUM(CASE 
                WHEN operacao = 'entrada' OR operacao = 'transf_entrada' THEN quantidade 
                WHEN operacao = 'saída' OR operacao = 'transf_saída' THEN (quantidade * -1)
                ELSE (quantidade * -1)
            END), 0) as saldo
            FROM historico
            WHERE rua_numero = ? AND rua_letra = ? AND desc_item = ? AND lote_item = ?
        ''', (numero, letra, produto, lote))
        saldo_item = cursor.fetchone()[0]
    return saldo_item


def get_saldo_view():
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute('''
            SELECT t.desc_item, t.saldo, t.time_mov
            FROM (
                SELECT desc_item,
                       SUM(CASE
                            WHEN operacao IN ('entrada', 'transf_entrada') THEN quantidade
                            WHEN operacao IN ('saída', 'transf_saída') THEN (quantidade * -1)
                            ELSE (quantidade * -1)
                        END) as saldo,
                       MAX(time_mov) as time_mov,
                       ROW_NUMBER() OVER(PARTITION BY desc_item ORDER BY MAX(time_mov) DESC) as rn
                FROM historico
                GROUP BY desc_item
                HAVING saldo != 0
            ) t
            WHERE rn = 1
            ORDER BY t.desc_item;
        ''')

        saldo_visualization = [
            {'produto': row[0], 'saldo': row[1], 'timestamp': row[2]} for row in cursor.fetchall()
        ]
        print(saldo_visualization)
    return saldo_visualization


def qr_code(qr_text):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_text)
    qr.make(fit=True)
    qr_image = qr.make_image(fill_color='black', back_color='white')

    return qr_image


# ROTAS
@app.route('/')
@verify_aut_priv(5)
def index():
    create_tables()

    print(f"[SERVIDOR] USUÁRIO: {session['user_name']}")
    return redirect(url_for('home'))


@app.route('/home')
@verify_aut_priv(5)
def home():
    return render_template('pages/index.html')


@app.route('/in-dev')
@verify_aut_priv(5)
def in_dev():
    return render_template('pages/developing.html')


def get_ult_acesso():
    id_user = session.get('id_user')
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute('''
            SELECT ult_acesso
            FROM users
            WHERE id_user = ?
        ''', (id_user,))
        row = cursor.fetchone()

        if row:
            ult_acesso = row[1]
            print(f"{ult_acesso}")
        else:
            ult_acesso = None
            print(f"{ult_acesso}")

        return ult_acesso


@app.route('/login')
def pagina_login():
    return render_template('pages/login.html')


@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        if 'logged_in' not in session:
            login_user = request.form['login_user']
            password = request.form['password_user']

            with sqlite3.connect(db_path) as connection:
                cursor = connection.cursor()
                cursor.execute('''
                    SELECT privilege_user, nome_user, sobrenome_user,
                           password_user, id_user, ult_acesso
                    FROM users
                    WHERE login_user = ?
                ''', (login_user,))

                row = cursor.fetchone()

                if row is not None:
                    password_user = row[3]
                    if check_key(password_user, password):
                        privilege_user = row[0]
                        nome_user = row[1]
                        sobrenome_user = row[2]
                        id_user = row[4]
                        ult_acesso = row[5]
                        try:
                            session['user_initials'] = nome_user[0] + sobrenome_user[0]
                            session['user_name'] = f'{nome_user} {sobrenome_user}'
                        finally:
                            session['id_user'] = id_user
                            session['logged_in'] = True
                            session['privilegio'] = privilege_user

                            msg = f'''[LOG-IN]\n{id_user} - {nome_user} {sobrenome_user}\n{request.remote_addr}'''
                            tlg_msg(msg)

                            acesso = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                            if ult_acesso is None:
                                alerta_tipo = 'REDEFINIR (SENHA) \n'
                                alerta_mensagem = 'Você deve definir sua senha no seu primeiro acesso.'
                                alerta_mais = '/users/reset-key'
                                url_return = 'Digite sua nova senha...'

                                return render_template('components/menus/alert-input.html', alerta_tipo=alerta_tipo,
                                                       alerta_mensagem=alerta_mensagem,
                                                       alerta_mais=alerta_mais, url_return=url_return)
                            else:  # if ult_acesso:
                                with connection:
                                    cursor = connection.cursor()
                                    cursor.execute('''
                                        UPDATE users
                                        SET ult_acesso = ?
                                        WHERE id_user = ?
                                    ''', (acesso, id_user))

                                return redirect(url_for('index'))
                    else:  # if not check_key(password_user, password):
                        alerta_tipo = 'LOGIN (SENHA) \n'
                        alerta_mensagem = 'Não foi possível entrar na sua conta... \n'
                        alerta_mais = ('''MOTIVO:
                                       - A senha está incorreta. ''')
                        return render_template('components/menus/alert.html', alerta_tipo=alerta_tipo, alerta_mensagem=alerta_mensagem,
                                               alerta_mais=alerta_mais, url_return=url_for('login'))
                else:  # if row is None:
                    alerta_tipo = 'LOGIN (USUÁRIO) \n'
                    alerta_mensagem = 'Não foi possível entrar na sua conta... \n'
                    alerta_mais = ('''MOTIVO:
                                   - O usuário não está cadastrado. \n''')
                    return render_template('components/menus/alert.html', alerta_tipo=alerta_tipo, alerta_mensagem=alerta_mensagem,
                                           alerta_mais=alerta_mais, url_return=url_for('login'))
        else:  # if 'logged_in' in session:
            return redirect(url_for('index'))
    else:  # if not request.method == 'POST':
        return redirect(url_for('login'))


# ROTA DE SAÍDA DO USUÁRIO
@app.route('/logout')
def logout():
    session.clear()

    return redirect(url_for('login'))


# ROTA DE MOVIENTAÇÃO NO ESTOQUE
@app.route('/mov')
@verify_aut_priv(3)
def mov():

    create_tables()
    end_lote = get_end_lote()
    return render_template('pages/mov.html', saldo_atual=end_lote)


# RETORNA FANTASIA CLIENTES (PARA SELECT2)
@app.route('/get/clientes', methods=['GET'])
def get_fant_clientes():
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute('SELECT DISTINCT fantasia_cliente FROM clientes')

        fant_clientes = [
            {'fantasia_cliente': row[0]} for row in cursor.fetchall()
        ]

    return fant_clientes


@app.route('/envase', methods=['GET'])
@verify_aut_priv(3)
def envase():
    create_tables()
    envase = get_envase()
    return render_template('pages/envase.html', envase=envase)


@app.route('/envase/calendar')
@verify_aut_priv(4)
def calendar_envase():
    create_tables()
    envase = get_envase()
    return render_template('pages/envase-calendar.html', envase=envase)


@app.route('/envase/delete/<id_envase>')
@verify_aut_priv(2)
def delete_item(id_envase):
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute('''DELETE FROM envase WHERE id_envase = ?''', (id_envase,))

    return redirect(url_for('envase'))


@app.route('/envase/concl/<id_envase>')
@verify_aut_priv(2)
def conclude_item(id_envase):
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute('''UPDATE envase
                          SET concluido = true
                          WHERE id_envase = ?''', (id_envase,))

    return redirect(url_for('envase'))


@app.route('/envase/nao-concl/<id_envase>')
@verify_aut_priv(2)
def not_conclude_item(id_envase):
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute('''UPDATE envase
                          SET concluido = false
                          WHERE id_envase = ?''', (id_envase,))

    return redirect(url_for('envase'))


@app.route('/envase/edit', methods=['GET', 'POST'])
@verify_aut_priv(2)
def envase_edit():
    create_tables()

    if request.method == 'POST':

        req_id_envase = request.form['id_envase']
        quantidade = request.form['quantidade']
        data_entr_antec = request.form['data_antec']
        data_envase = request.form['data_envase']
        observacao = request.form['observacao']

        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            cursor.execute('''UPDATE envase
                            SET quantidade = ?,
                                data_entr_antec = ?,
                                data_envase = ?,
                                observacao = ?
                            WHERE id_envase = ?;''', (quantidade, data_entr_antec, data_envase,
                                                      observacao, req_id_envase))
        return redirect(url_for('envase'))
    else:
        req_id_envase = request.args.get('id_envase')

        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            cursor.execute('''SELECT p.linha, c.fantasia_cliente, i.cod_item,
                                     i.desc_item, p.quantidade, p.data_entr_antec,
                                     p.data_envase, p.observacao, p.id_envase,
                                     p.concluido
                            FROM envase p
                            JOIN itens i ON p.cod_item = i.cod_item
                            JOIN clientes c ON p.cod_cliente = c.cod_cliente
                            WHERE id_envase = ?''', (req_id_envase,))

            env_edit = [{'linha': row[0], 'fantasia_cliente': row[1], 'cod_item': row[2],
                         'desc_item': row[3], 'quantidade': row[4], 'data_entr_antec': row[5],
                         'data_envase': row[6], 'observacao': row[7], 'id_envase': row[8],
                         'concluido': row[9]} for row in cursor.fetchall()]

        return render_template('pages/envase-edit.html', env_edit=env_edit)


@app.route('/envase/insert', methods=['POST'])
@verify_aut_priv(2)
def insert_envase():
    if request.method == 'POST':

        linha = request.form['linha']
        sku = request.form['codinterno']
        observacao = request.form['observacao']
        quantidade = request.form['quantidade']
        data_entr_antec = request.form['data_antec']
        data_envase = request.form['data_envase']
        cliente = request.form['cliente']

        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            cursor.execute('''SELECT cod_cliente FROM clientes WHERE fantasia_cliente = ?''', (cliente,))

            row = cursor.fetchone()
            cod_cliente = row[0] if row else None

        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            cursor.execute('''INSERT INTO envase (linha, cod_cliente, cod_item,
                                                  quantidade, data_entr_antec, data_envase,
                                                  observacao) 
                            VALUES (?, ?, ?, ?, ?, ?, ?)''', (linha, cod_cliente, sku,
                                                              quantidade, data_entr_antec, data_envase,
                                                              observacao))
            connection.commit()
    return redirect(url_for('envase'))


# PRODUÇÃO
@app.route('/producao', methods=['GET'])
@verify_aut_priv(3)
def producao():
    create_tables()
    producao = get_producao()
    return render_template('pages/producao.html', producao=producao)


@app.route('/producao/calendar')
@verify_aut_priv(4)
def calendar_producao():
    create_tables()
    producao = get_producao()
    return render_template('pages/producao-calendar.html', producao=producao)


@app.route('/producao/delete/<id_producao>')
@verify_aut_priv(2)
def delete_producao(id_producao):
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute('''DELETE 
                          FROM producao 
                          WHERE id_producao = ?
                          ''', (id_producao,))
    return redirect(url_for('producao'))


@app.route('/producao/concl/<id_producao>')
@verify_aut_priv(2)
def conclude_producao(id_producao):
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute('''UPDATE producao
                          SET concluido = true
                          WHERE id_producao = ?''', (id_producao,))
    return redirect(url_for('producao'))


@app.route('/producao/nao-concl/<id_producao>')
@verify_aut_priv(2)
def not_conclude_producao(id_producao):
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute('''UPDATE producao
                          SET concluido = false
                          WHERE id_producao = ?''', (id_producao,))
    return redirect(url_for('producao'))


@app.route('/producao/edit', methods=['GET', 'POST'])
@verify_aut_priv(2)
def producao_edit():
    create_tables()
    if request.method == 'POST':
        req_id_producao = request.form['id_producao']
        litros = request.form['litros']
        data_entr_antec = request.form['data_antec']
        data_producao = request.form['data_producao']
        observacao = request.form['observacao']

        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            cursor.execute('''UPDATE producao
                            SET litros   = ?,
                                data_entr_antec = ?,
                                data_producao = ?,
                                observacao = ?
                            WHERE id_producao = ?;''', (litros, data_entr_antec, data_producao,
                                                        observacao, req_id_producao))
        return redirect(url_for('producao'))
    else:
        req_id_producao = request.args.get('id_producao')

        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            cursor.execute('''SELECT p.linha, p.liq_linha, p.liq_cor, p.embalagem,
                                     p.litros, p.data_entr_antec, p.data_producao,
                                     p.observacao, p.id_producao, p.concluido,
                                     p.liq_tipo
                            FROM producao p
                            WHERE ? = p.id_producao
                            ORDER BY p.data_producao;''', (req_id_producao,))

            prod_edit = [{'linha': row[0], 'liq_linha': row[1], 'liq_cor': row[2],
                          'embalagem': row[3], 'litros': row[4], 'data_entr_antec': row[5],
                          'data_producao': row[6], 'observacao': row[7], 'id_producao': row[8],
                          'concluido': row[9], 'liq_tipo': row[10]} for row in cursor.fetchall()]

        return render_template('pages/producao-edit.html', prod_edit=prod_edit)


@app.route('/producao/insert', methods=['POST'])
@verify_aut_priv(2)
def insert_producao():
    if request.method == 'POST':

        linha = request.form['linha']
        liq_tipo = request.form['liq_tipo']
        liq_linha = request.form['liq_linha']
        liq_cor = request.form['liq_cor']
        embalagem = request.form['embalagem']
        litros = request.form['litros']
        data_entr_antec = request.form['data_antec']
        data_producao = request.form['data_producao']
        observacao = request.form['observacao']

        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            cursor.execute('''INSERT INTO producao (linha, liq_linha, liq_cor,
                                                    embalagem, litros, data_entr_antec,
                                                    data_producao, observacao, liq_tipo) 
                              VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', (linha, liq_linha, liq_cor,
                                                                      embalagem, litros, data_entr_antec,
                                                                      data_producao, observacao, liq_tipo))
            connection.commit()

    return redirect(url_for('producao'))


@app.route('/users/reset-key', methods=['POST'])
@verify_aut_priv(4)
def reset_key():
    password = request.form['input']
    password_user = hash_key(password)

    id_user = session.get('id_user')

    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute('''UPDATE users 
                          SET password_user = ?
                          WHERE id_user = ?''',
                       (password_user, id_user))
        connection.commit()

    with sqlite3.connect(db_path) as connection:
        acesso = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor = connection.cursor()
        cursor.execute('''
            UPDATE users
            SET ult_acesso = ?
            WHERE id_user = ?
        ''', (acesso, id_user))

    return redirect(url_for('index'))


@app.route('/users')
@verify_aut_priv(2)
def users():
    create_tables()
    get_users()

    return render_template('pages/users.html', users=get_users())


@app.route('/users/inserting', methods=['POST'])
@verify_aut_priv(2)
def cadastrar_usuario():
    if request.method == 'POST':

        login_user = request.form['login_user']
        nome_user = request.form['nome_user']
        sobrenome_user = request.form['sobrenome_user']
        privilege_user = request.form['privilege_user']
        data_cadastro = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # HASH PASSWORD
        password = request.form['password_user']
        password_user = hash_key(password)

        try:
            with sqlite3.connect(db_path) as connection:
                cursor = connection.cursor()
                cursor.execute('''INSERT INTO users (login_user, password_user, nome_user,
                                                     sobrenome_user, privilege_user, data_cadastro) 
                                   VALUES (?, ?, ?, ?, ?, ?)''', (login_user, password_user, nome_user,
                                                                  sobrenome_user, privilege_user, data_cadastro))
                connection.commit()

                user_name = session.get('user_name')
                id_user = session.get('id_user')
                privilegio = session.get('privilegio')

                msg = f'''[CADASTRO]\n{request.remote_addr}\n{id_user} - {user_name} [+] {nome_user} {sobrenome_user} ({privilegio})'''
                tlg_msg(msg)

        except sqlite3.IntegrityError as e:
            if 'UNIQUE constraint failed' in str(e):
                alerta_tipo = 'CADASTRO (USUÁRIO) \n'
                alerta_mensagem = 'Não foi possível criar usuário... \n'
                alerta_mais = ('''MOTIVO:
                               - Já existe um usuário com este login.''')
                return render_template('components/menus/alert.html', alerta_tipo=alerta_tipo, alerta_mensagem=alerta_mensagem,
                                       alerta_mais=alerta_mais, url_return=url_for('users'))
            else:
                print("Erro desconhecido:", e)
                alerta_tipo = 'CADASTRO (USUÁRIO) \n'
                alerta_mensagem = 'Não foi possível criar usuário... \n'
                alerta_mais = (f'''DESCRIÇÃO DO ERRO:
                               - {e}. \n''')
                return render_template('components/menus/alert.html', alerta_tipo=alerta_tipo, alerta_mensagem=alerta_mensagem,
                                       alerta_mais=alerta_mais, url_return=url_for('users'))
        else:
            return redirect(url_for('users'))
    return render_template('pages/users.html')


@app.route('/mov/historico')
@verify_aut_priv(4)
def historico():
    create_tables()
    estoque = get_historico()

    return render_template('pages/historico.html', estoque=estoque)


@app.route('/produtos', methods=['GET', 'POST'])
@verify_aut_priv(4)
def produtos():
    if request.method == 'POST':
        desc_item = request.form['desc_item']
        cod_item = request.form['cod_item']
        dun14 = request.form['cod_dun14']

        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            cursor.execute('INSERT INTO itens VALUES (?,?,?)', (cod_item, desc_item, dun14))
            connection.commit()

        return redirect(url_for('produtos'))

    itens = get_itens()
    return render_template('pages/produtos.html', itens=itens)


@app.route('/etiqueta', methods=['GET', 'POST'])
@verify_aut_priv(3)
def etiqueta():
    if request.method == 'POST':

        # REQUESTS
        qr_text = request.form['qr_text']
        desc = request.form['desc']
        sku = request.form['sku']
        lote = request.form['lote']

        # PARAMETROS
        width = 400
        height = 400
        img = Image.new('RGB', (width, height), color='white')

        # QR CODE
        qr_image = qr_code(qr_text)
        qr_width, qr_height = qr_image.size
        img.paste(qr_image, ((width - qr_width) // 2, (height - qr_height) // 2))

        # LOTE E SKU
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype('arial.ttf', 30)

        lote_bbox = draw.textbbox((0, 0), lote, font=font)
        lote_width = lote_bbox[2] - lote_bbox[0]
        draw.text(((width - lote_width) // 2, height // 6.4), lote, fill='black', font=font)

        sku_bbox = draw.textbbox((0, 0), sku, font=font)
        sku_width = sku_bbox[2] - sku_bbox[0]
        draw.text(((width - sku_width) // 2, height - height // 4.2), sku, fill='black', font=font)

        text = desc
        font = ImageFont.truetype('arial.ttf', 20)
        lines = textwrap.wrap(text, width=30)
        y_text = height - height // 6.5
        for line in lines:
            text_width, text_height = draw.textbbox((0, 0), line, font=font)[2:]
            draw.text(((width - text_width) // 2, y_text), line, font=font, fill='black')
            y_text += text_height

        img_io = io.BytesIO()
        img.save(img_io, format='PNG')
        img_io.seek(0)

        img_base64 = base64.b64encode(img_io.getvalue()).decode()

        return img_base64

    return render_template('pages/etiqueta.html', produtos=produtos)


def parse_float(value):
    try:
        return float(value.replace(',', '.'))
    except ValueError:
        return 0


@app.route('/rotulo', methods=['GET', 'POST'])
@verify_aut_priv(4)
def rotulo():
    if request.method == 'POST':
        espessura_fita = parse_float(request.form['espessura_fita'])
        diametro_inicial = parse_float(request.form['diametro_inicial'])
        diametro_minimo = parse_float(request.form['diametro_minimo'])
        espessura_papelao = parse_float(request.form['espessura_papelao'])
        compr_rotulo = parse_float(request.form['compr_rotulo'])
        comprimento_total = 0
        num_voltas = 0

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

            return jsonify({ 'num_rotulos_str': num_rotulos_str,
                             'num_voltas': num_voltas,
                             'comprimento_mtrs': comprimento_mtrs})
        else:
            return jsonify({'num_rotulos_str': 0,
                            'num_voltas': 0,
                            'comprimento_mtrs': "0,00"})

    return render_template('pages/rotulo.html')


@app.route('/buscar_linhas', methods=['POST'])
@verify_aut_priv(3)
def buscar_linhas():
    desc_item = request.form['produto']
    print(f'BUSCANDO LINHA...\nDESCRIÇÃO LIDA: {desc_item}')

    def encontrar_embalagem(desc_item):
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
        tipo_embal, lit_embal = encontrar_embalagem(desc_item)
        if tipo_embal:
            with sqlite3.connect(db_path) as connection:
                cursor = connection.cursor()
                cursor.execute('''SELECT DISTINCT cod_linha
                                  FROM aux_linha
                                  WHERE lit_embal = ?
                                  AND tipo_embal = ?
                              ''', (lit_embal, tipo_embal))

                cod_linha = cursor.fetchall()

                print('OPERAÇÃO BEM SUCEDIDA')

                return jsonify({'cod_linha': cod_linha})
            pass
        else:
            cod_linha = ''
            print('DESCRIÇÃO INVÁLIDA: IMPOSSÍVEL PROSSEGUIR...')
            return jsonify({'codLINHA': cod_linha})


@app.route('/searching', methods=['POST'])
@verify_aut_priv(3)
def searching():
    codigo = request.form['cod_str_qr'].strip()

    print(f'BUSCANDO ITEM...\nCÓDIGO LIDO: {codigo}')

    codigo = re.sub(r'[^0-9;]', '', codigo)

    if len(codigo) == 4 or len(codigo) == 0:
        print('CÓDIGO INVÁLIDO: IMPOSSÍVEL PROSSEGUIR...')
        desc_item = 'ITEM NÃO CADASTRADO'
        cod_item = ''
        cod_lote = ''
        cod_linha = ''

        return jsonify({'codITEM': cod_item, 'descITEM': desc_item, 'codLOTE': cod_lote, 'codLINHA': cod_linha})

    else:

        # VALIDAÇÃO P/ CÓDIGO INTERNO SEM ';'
        if len(codigo) == 6:
            print('CÓDIGO SKU SEM ";": REALIZANDO VALIDAÇÃO...')
            codigo = codigo + ';'

        partes = codigo.split(';')
        cod_item = []

        print(partes)
        if len(partes) == 1:
            print('CODE TYPE: DUN14')
            cod_barra = partes[0]

            with sqlite3.connect(db_path) as connection:
                cursor = connection.cursor()
                cursor.execute('''
                            SELECT desc_item, cod_item
                            FROM itens
                            WHERE dun14 = ?
                        ''', (cod_barra,))

                rows = cursor.fetchall()

                for row in rows:
                    codigos_itens = row[1]
                    cod_item.append(codigos_itens)

                if row:
                    desc_item = row[0]

                    if 'VINHO' in desc_item:
                        cod_lote = 'VINHO'
                    else:
                        cod_lote = ''

                else:
                    desc_item = 'ITEM NÃO CADASTRADO'
                    cod_item = ''
                    cod_lote = ''

                print(f'''OPERAÇÃO BEM SUCEDIDA.
                LOTE: {cod_lote} 
                SKU's: {cod_item}
                DESCRIÇÃO: {desc_item}''')

                return jsonify({'codITEM': cod_item, 'descITEM': desc_item, 'codLOTE': cod_lote})

        elif len(partes) == 2:
            print('CODE TYPE: QR-CODE')
            codigos_itens = partes[0]

            cod_item.append(codigos_itens)

            if partes[1] != '':
                cod_lote = 'CS' + partes[1]
            else:
                cod_lote = ''

            with (sqlite3.connect(db_path) as connection):
                cursor = connection.cursor()
                cursor.execute('''
                            SELECT desc_item
                            FROM itens
                            WHERE cod_item = ?
                        ''', (codigos_itens,))

                desc_item = cursor.fetchone()[0]

                if 'VINHO' in desc_item:
                    cod_lote = 'VINHO'

                print(f'''RETORNANDO CÓDIGOS: 
                LOTE: {cod_lote}
                SKU's: {cod_item} 
                DESCRIÇÃO: {desc_item}''')

                return jsonify({'codITEM': cod_item, 'codLOTE': cod_lote, 'descITEM': desc_item})

        else:
            print('OPERAÇÃO FALHOU: O CÓDIGO FORNECIDO NAO ATENDEU AOS REQUISITOS')

            desc_item = 'ITEM NÃO CADASTRADO'
            cod_item = ''
            cod_lote = ''

            return jsonify({'codITEM': cod_item, 'codLOTE': cod_lote, 'descITEM': desc_item})


@app.route('/redirected', methods=['POST'])
def redirected():
    if 'controle_estoque' in request.form:
        return redirect(url_for('mov'))

    elif 'historico_movimentacao' in request.form:
        return redirect(url_for('historico'))

    elif 'saldo_itens' in request.form:
        return redirect(url_for('saldo'))

    return render_template('pages/index.html')


@app.route('/mov/moving', methods=['POST'])
@verify_aut_priv(3)
def moving():

    numero = request.form['numero']
    letra = request.form['letra']
    produto = request.form['produto']
    lote = request.form['lote']
    quantidade = int(request.form['quantidade'])
    operacao = request.form['operacao']
    timestamp_br = datetime.now(timezone(timedelta(hours=-3)))
    timestamp_out = timestamp_br.strftime('%Y/%m/%d %H:%M:%S')
    timestamp_in = (timestamp_br + timedelta(seconds=1)).strftime('%Y/%m/%d %H:%M:%S')
    saldo_item = get_saldo_item(numero, letra, produto, lote)

    if 'logged_in' in session:

        # VERIFICA SE RESULTARÁ NEGATIVO
        if operacao in ('saída', 'transferencia') and quantidade > saldo_item:
            alerta_tipo = 'OPERAÇÃO CANCELADA \n'
            alerta_mensagem = 'O saldo do item selecionado é INSUFICIENTE. \n'
            alerta_mais = ('''POSSÍVEIS SOLUÇÕES:
                           - Verifique se o código do item corresponde à sua descrição.
                           - Verifique a quantidade de movimentação.
                           - Verifique a operação selecionada. ''')
            return render_template('components/menus/alert.html', alerta_tipo=alerta_tipo, alerta_mensagem=alerta_mensagem,
                                   alerta_mais=alerta_mais, url_return=url_for('mov'))

        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            print(f'Debugging: Operação: {operacao}')

            if operacao == 'transferencia':
                destino_letra = request.form['destino_letter']
                destino_numero = request.form['destino_number']

                # SAÍDA DO ENDEREÇO DE ORIGEM
                cursor.execute('''INSERT INTO historico 
                               (rua_numero, rua_letra, desc_item, lote_item, quantidade, operacao, user_name, time_mov)
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                               (numero, letra, produto, lote, quantidade,
                                'transf_saída', session['user_name'], timestamp_out))

                # ENTRADA NO ENDEREÇO DE DESTINO
                cursor.execute('''INSERT INTO historico 
                               (rua_numero, rua_letra, desc_item, lote_item, quantidade, operacao, user_name, time_mov)
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                               (destino_numero, destino_letra, produto, lote, quantidade,
                                'transf_entrada', session['user_name'], timestamp_in))

            else:
                # OPERAÇÃO PADRÃO (entrada ou saída)
                cursor.execute('''INSERT INTO historico 
                               (rua_numero, rua_letra, desc_item, lote_item, quantidade, operacao, user_name, time_mov)
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                               (numero, letra, produto, lote, quantidade,
                                operacao, session['user_name'], timestamp_out))

            connection.commit()

        return redirect(url_for('mov'))
    return redirect(url_for('login'))


@app.route('/saldo')
@verify_aut_priv(4)
def saldo():
    saldo_visualization = get_saldo_view()
    return render_template('pages/saldo.html', saldo_visualization=saldo_visualization)


def export_csv(data, filename):
    if data and len(data) > 0:
        csv_data = ';'.join(data[0].keys()) + '\n'
        for item in data:
            csv_data += ';'.join(map(str, item.values())) + '\n'

        response = Response(csv_data, content_type='text/csv')
        response.headers['Content-Disposition'] = f'attachment; filename={filename}.csv'

        return response
    else:
        alerta_tipo = 'DOWNLOAD IMPEDIDO \n'
        alerta_mensagem = 'A tabela não tem informações o suficiente para exportação. \n'
        alerta_mais = ('''POSSÍVEIS SOLUÇÕES:
                       - Verifique se a tabela possui mais de uma linha.
                       - Contate o suporte. ''')
        return render_template('components/menus/alert.html', alerta_tipo=alerta_tipo, alerta_mensagem=alerta_mensagem,
                               alerta_mais=alerta_mais, url_return=url_for('index'))


@app.route('/export_csv/<tipo>', methods=['GET'])
def export_csv_tipo(tipo):

    if tipo == 'historico':
        data = get_historico()
        filename = 'exp_historico'
    elif tipo == 'produtos':
        data = get_itens()
        filename = 'exp_produtos'
    elif tipo == 'saldo':
        data = get_end_lote()
        filename = 'exp_saldo_lote'
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
        alerta_tipo = 'DOWNLOAD IMPEDIDO \n'
        alerta_mensagem = 'A tabela não tem informações o suficiente para exportação. \n'
        alerta_mais = ('''POSSÍVEIS SOLUÇÕES:
                       - Verifique se a tabela possui mais de uma linha.
                       - Contate o suporte. ''')
        return render_template('components/menus/alert.html', alerta_tipo=alerta_tipo, alerta_mensagem=alerta_mensagem,
                               alerta_mais=alerta_mais, url_return=url_for('index'))
    return export_csv(data, filename)


# ROTA PRINCIPAL
if __name__ == '__main__':
    # Pega o nome do diretório
    dir_os = os.path.dirname(os.path.abspath(__file__))

    if 'vAtual' in dir_os:
        # Se o diretório contém 'vAtual', modo = desenvolvedor.
        port = 5090
        debug = True
    elif 'CDEHP_Server$' in dir_os:
        # Se o diretório contém 'CDEHP_Server$', modo = usuário.
        port = 5005
        debug = False
    else:
        # Se o diretório não contém 'vAtual' ou 'CDEHP_Server$', não executa.
        input('''
        [ERRO 1] 
        O arquivo não pode ser executado, verifique se o arquivo está alocado corretamente.
        Pressione ENTER para sair.
        ''')
        sys.exit(2)

    app.run(host='0.0.0.0', port=port, debug=debug)
