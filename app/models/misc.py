import calendar
import requests, random, os

from flask import Flask, Response, request, redirect, render_template, url_for, jsonify, session, abort
from datetime import datetime, timezone, timedelta
from passlib.hash import pbkdf2_sha256

from app.utils import cdeapp
from app.models import dbUtils, estoqueUtils, logTexts as lt


db_path = cdeapp.config.get_db_path()
debug = cdeapp.config.get_debug()

@staticmethod
def days_to_expire(date_fab: str, months: int, cod_lote: str) -> tuple[int, str | None]:
        if not months or not cod_lote or 'CS' not in cod_lote:
            return 0, "N/A" # sem prazo de validade, ou não informado

        date_fab = date_fab.replace('-', '/')
        date_fab = datetime.strptime(date_fab, "%Y/%m/%d %H:%M:%S")

        total_months = date_fab.month + months
        year = date_fab.year + (total_months - 1) // 12
        month = (total_months - 1) % 12 + 1

        last_day = calendar.monthrange(year, month)[1]
        day = min(date_fab.day, last_day)

        expiration_date = date_fab.replace(year=year, month=month, day=day)
        remaining = (expiration_date - datetime.today()).days

        return remaining, None
    
    
@staticmethod
def parse_date_to_html_input(date: str) -> str:
    date, _ = date.split(' ')
    return date.replace('/', '-')


@staticmethod
# busca frase para /index
def get_frase() -> str:
    with open('static/frases.txt', 'r', encoding='utf-8') as file:
        frases = file.readlines()
        frase = random.choice(frases).strip()
        if not frase:
        # frase padrão
            frase = 'Seja a mudança que você deseja ver no mundo.'
    return frase


@staticmethod
# converte timestamp para formato do database
def parse_db_datetime(timestamp):
    if not timestamp:
        timestamp = datetime.now(timezone(timedelta(hours=-3)))
    elif isinstance(timestamp, str):
        timestamp = datetime.strptime(timestamp, '%Y-%m-%d')
        timestamp = timestamp.replace(tzinfo=timezone(timedelta(hours=-3)))
    
    return timestamp.strftime('%Y/%m/%d %H:%M:%S')


@staticmethod
# retorna timestamp
def get_timestamp() -> str:
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


@staticmethod
# adiciona dias À data informada
def add_days_to_datetime_str(date_str, qtde_days) -> str:

    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    
    new_date_obj = date_obj + timedelta(days=qtde_days)
    
    new_date_str = new_date_obj.strftime('%Y-%m-%d')
    
    return new_date_str


@staticmethod
# mensagem do telegram
def telegram_msg(msg):
    if not session.get('user_grant') == 1:
        if debug == True:
            lt.debug_log('[ERRO] A mensagem não pôde ser enviada em modo debug')
            return False
        
        bot_token = os.getenv('TLG_BOT_TOKEN')
        chat_id   = os.getenv('TLG_CHAT_ID')

        url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
        params = {'chat_id': chat_id, 'text': msg}

        if requests.post(url, params=params):
            return True
    return False


@staticmethod
# hash da senha
def hash_key(password) -> str:
    return pbkdf2_sha256.hash(password)


@staticmethod
# parse p/ float
def parse_float(value) -> float:
    try:
        return float(value.replace(',', '.'))
    except ValueError:
        return 0.0


@staticmethod
# verifica senha no banco de hash
def password_check(id_user, password) -> bool:
    query = '''
        SELECT password_user
        FROM users
        WHERE id_user = {a};
    '''.format(a=id_user)
    
    dsn = 'LOCAL'
    result, _ = dbUtils.query(query, dsn)

    if result:
        db_password = result[0]
        return check_key(db_password, password)
    return False


@staticmethod
# verifica senha no banco de hash
def check_key(hashed_pwd, pwd) -> bool:
    return pbkdf2_sha256.verify(pwd, hashed_pwd)


class CSVUtils:
    @staticmethod
    # csv para integraçÃo erp
    def iterate_csv_data_erp(data) -> str:
        csv_data = ''
        for item in data:
            line = ';'.join(map(str, item.values()))
            csv_data += f'"{line}"\n'
        return csv_data


    @staticmethod
    # corpo csv padrao
    def iterate_csv_data(data) -> str:
        csv_data = ''
        for item in data:
            line = ';'.join(map(str, item.values()))
            csv_data += f'{line}\n'
        return csv_data


    @staticmethod
    # adiciona cabecalho para csv
    def add_headers(data):
        if data and len(data) > 0:
            headers = ';'.join(data[0].keys())
            return f'{headers}\n'
        return ''

    
    @staticmethod    
    # retorna tabela de saldo
    def get_export_promob():
        sql_balance_template = estoqueUtils.sql_balance_template

        query = '''
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
        '''.format(a=sql_balance_template)
        
        dsn = 'LOCAL'
        result, _ = dbUtils.query(query, dsn)

        inv_data = None
        if result:
            inv_data = [{
                'cod_item': row[1],
                'deposito': int(5), #TODO: create a menu to choose this
                'qtde'    : row[2]
            } for row in result ]

        return inv_data

    
    @staticmethod
    # construtor de csv
    def export_csv(data, filename, include_headers=True):
        if data and len(data) > 0:
            csv_data = ''
            if not include_headers:
                csv_data += CSVUtils.iterate_csv_data_erp(data)
            else:
                csv_data += CSVUtils.add_headers(data)
                csv_data += CSVUtils.iterate_csv_data(data)

            csv_filename = Response(csv_data, content_type='text/csv')
            csv_filename.headers['Content-Disposition'] = f'attachment; filename={filename}.csv'

            return csv_filename
        else:
            alert_type = 'DOWNLOAD IMPEDIDO \n'
            alert_msge = 'A tabela não tem informações suficientes para exportação. \n'
            alert_more = ('''
                POSSÍVEIS SOLUÇÕES:
                • Verifique se a tabela possui mais de uma linha.
                • Contate o suporte. 
            ''')
            return render_template(
                'components/menus/alert.j2', 
                alert_type=alert_type, 
                alert_msge=alert_msge, 
                alert_more=alert_more, 
                url_return=url_for('index')
            )
