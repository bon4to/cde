import sqlite3

from app.utils import cdeapp
from app.models import dbUtils, logTexts, misc

db_path = cdeapp.config.get_db_path()

sql_balance_template = dbUtils.QueryManager.get(query_id=1)
"""
SQL query template used to calculate the current inventory balance.
The balance is computed by summing transaction quantities:
- 'E' (Entrada) transactions add to the balance (+).
- 'S' (Saída) transactions subtract from the balance (-).

Example:
    t1: quantity = 30 AND operation = 'E' => +30
    t2: quantity = 20 AND operation = 'S' => -20
"""


@staticmethod
def get_item_inv_locations(cod_item=None):
    """
    Retrieves all storage addresses that contain the specified item.

    For each matching address, the function computes additional metadata such as
    item expiration, balance, batch number, etc.

    Args:
        cod_item (str, optional): Code of the item to search for. If not provided or False, 
            returns an empty result. #TODO: use a string.

    Returns:
        tuple:
            - list[dict]: List of addresses containing the item with detailed metadata.
            - list: Column headers corresponding to the database query result.

    Side Effects:
        - Calls `misc.days_to_expire` for each result row.

    Example:
        >>> result, columns = get_item_inv_locations('ITEM123')

    Notes:
        - Adds a space at the end of 'address' to improve exact search results.
        - Returns empty lists if `cod_item` is not provided.
    """
    if cod_item:
        query = dbUtils.QueryManager.get(
            query_id = 2,
            calc = sql_balance_template,
            b = str(cod_item)
        )
        
        dsn = 'LOCAL'
        result_local, columns_local = dbUtils.query(query, dsn)
        
        result = []
        for row in result_local:
            validade, err = misc.days_to_expire(date_fab=row[6], months=row[7], cod_lote=row[4])
            if err != None:
                validade = err
            result.append({
                # itera letra e numero da rua com um '.'
                'address': f'{row[0]}.{row[1]} ', 
                # adiciona espaço vazio no final para melhorar busca de resultados exatos
                #   exemplo:
                #    'A.1'  -> ['A.1', 'A.10', 'A.100']
                #    'A.1 ' -> ['A.1 ']
                'cod_item': row[2], 'desc_item': row[3], 'cod_lote': row[4], 
                'saldo'   : row[5], 'date_fab' : row[6], 'item_expire_months': row[7],
                'validade': validade
            })
        
        return result, columns_local
    else:
        return [], []


@staticmethod
def get_item_loss(month_str: str, year_str: str):
    query = dbUtils.QueryManager.get(
        query_id = 3,
        year = str(year_str),
        month = str(month_str)
    )
    
    dsn = 'API'
    result, columns = dbUtils.query(query, dsn, source=2)
    
    return result, columns


@staticmethod
# RETORNA TABELA DE SALDO
def get_saldo_view(timestamp=False):
    if timestamp:
        timestamp = misc.add_days_to_datetime_str(timestamp, 1)
    timestamp = misc.parse_db_datetime(timestamp)
    
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
        '''.format(a=sql_balance_template), (timestamp,))

        result = [{
            'cod_item': row[0], 'desc_item': row[1], 
            'saldo'   : row[2], 'ult_mov'  : row[3]
        } for row in cursor.fetchall()]

    return result


@staticmethod
# BUSCA SALDO COM UM FILTRO (PRESET)
def get_saldo_preset(index, timestamp=False):
    itens = get_preset_itens(index)
    
    if not itens:
        return []
    
    if timestamp:
        timestamp = misc.add_days_to_datetime_str(timestamp, 1)
    timestamp = misc.parse_db_datetime(timestamp)
    
    # prepara uma string de placeholders sql (ex.: ?, ?, ?...)
    # e coloca na query
    placeholders = ','.join(['?'] * len(itens))
    
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
    '''.format(a=sql_balance_template, b=placeholders)

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
def get_first_mov(cod_item: str, cod_lote: str):
    query = f'''
        SELECT time_mov
        FROM tbl_transactions
        WHERE cod_item = '{cod_item}'
        AND lote_item = '{cod_lote}'
        ORDER BY time_mov ASC
        LIMIT 1;
    '''
    dsn = 'LOCAL'
    result, _ = dbUtils.query(query, dsn)
    return result


@staticmethod
# RETORNA ENDEREÇAMENTO POR LOTES
def get_inv_address_with_batch(timestamp=False):
    if timestamp:
        timestamp = misc.add_days_to_datetime_str(timestamp, 1)
    timestamp = misc.parse_db_datetime(timestamp)
    
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute('''
            SELECT  
                h.rua_letra, h.rua_numero, 
                i.cod_item, i.desc_item, h.lote_item,
                {a} as saldo,
                (
                    SELECT time_mov
                    FROM tbl_transactions
                    WHERE cod_item = i.cod_item
                    AND lote_item = h.lote_item
                    ORDER BY time_mov ASC
                    LIMIT 1
                ) as first_mov,
                i.validade
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
            ;'''.format(a=sql_balance_template),(timestamp,)
        )

        result = []
        for row in cursor.fetchall():
            validade, err = misc.days_to_expire(date_fab=row[6], months=row[7], cod_lote=row[4])
            if err != None:
                validade = err
            
            validade_str = ''
            validade_perc_str = 0
            if type(validade) == int:
                validade_str = f"{(float(validade) / 30.44):.1f} / {row[7]} meses"
                validade_perc_str = float(f"{(float(validade) / 30.44 / row[7] * 100):.1f}")
            
            result.append({
                # itera letra e numero da rua com um '.'
                'address': f'{row[0]}.{row[1]} ', 
                # adiciona espaço vazio no final para melhorar busca de resultados exatos
                #   exemplo:
                #    'A.1'  -> ['A.1', 'A.10', 'A.100']
                #    'A.1 ' -> ['A.1 ']
                'cod_item': row[2], 'desc_item': row[3], 'cod_lote': row[4], 
                'saldo'   : row[5], 'date_fab' : row[6], 'item_expire_months': row[7],
                'validade': validade, 'validade_str': validade_str, 'validade_perc_str': validade_perc_str
            })
    return result


@staticmethod
# RETORNA ENDEREÇAMENTO POR LOTES
def get_inv_report(timestamp=False):
    if timestamp:
        timestamp = misc.add_days_to_datetime_str(timestamp, 1)
    timestamp = misc.parse_db_datetime(timestamp)
    
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute('''
            WITH base AS (
                SELECT  
                    h.rua_letra,
                    h.rua_numero, 
                    i.cod_item, 
                    i.desc_item, 
                    h.lote_item,

                    {a} saldo,

                    (
                        SELECT REPLACE(time_mov, '/', '-')
                        FROM tbl_transactions
                        WHERE cod_item = i.cod_item
                        AND lote_item = h.lote_item
                        ORDER BY time_mov ASC
                        LIMIT 1
                    ) AS first_mov_raw,

                    i.validade

                FROM tbl_transactions h
                JOIN itens i ON h.cod_item = i.cod_item
                
                GROUP BY 
                    h.rua_numero, h.rua_letra, 
                    h.cod_item, h.lote_item
            )

            SELECT 
                rua_letra,
                rua_numero,
                cod_item,
                desc_item,
                lote_item,
                saldo,
                first_mov_raw AS first_mov,
                validade,
                CASE 
                    WHEN validade IS NOT NULL 
                    THEN datetime(first_mov_raw, '+' || validade || ' months')
                    ELSE 'N/A'
                END AS data_vencimento

            FROM base
            WHERE saldo != 0
            
            ORDER BY 
                rua_letra ASC, rua_numero ASC,
                desc_item ASC
                ;'''.format(a=sql_balance_template),
        )

        result = []
        for row in cursor.fetchall():
            validade, err = misc.days_to_expire(date_fab=row[6], months=row[7], cod_lote=row[4])
            if err != None:
                validade = err
            
            validade_str = ''
            validade_perc_str = 0
            validade_meses = 0
            if type(validade) == int:
                validade_meses = float(validade) / 30.44 # approximadamente 30.44 dias por mes
                validade_str = f"{(validade_meses):.1f} / {row[7]} meses"
                validade_perc_str = float(f"{(validade_meses / row[7] * 100):.1f}")
            
            # checa se a data de vencimento existe
            date_venc = row[8]
            
            if date_venc == None:
                date_venc = 'N/A'
            
            result.append({
                # itera letra e numero da rua com um '.'
                'address': f'{row[0]}.{row[1]} ', 
                # adiciona espaço vazio no final para melhorar busca de resultados exatos
                #   exemplo:
                #    'A.1'  -> ['A.1', 'A.10', 'A.100']
                #    'A.1 ' -> ['A.1 ']
                'cod_item': row[2], 'desc_item': row[3], 'cod_lote': row[4], 
                'saldo'   : row[5], 'date_fab' : row[6], 'item_expire_months': row[7],
                'validade': validade, 'validade_str': validade_str, 'validade_perc_str': validade_perc_str, 
                'validade_meses': float(validade_meses), 'date_venc': date_venc
            })
    return result


@staticmethod
# RETORNA ENDEREÇAMENTO DE FATURADOS POR LOTES
def get_inv_address_with_batch_fat():
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()
        cursor.execute('''
            SELECT  
                h.rua_letra, h.rua_numero, i.cod_item,
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
            # itera letra e numero da rua com um '.'
            'address': f'{row[0]}.{row[1]} ',
            # adiciona espaço vazio no final para melhorar busca de resultados exatos
            #   exemplo:
            #    'A.1'  -> ['A.1', 'A.10', 'A.100']
            #    'A.1 ' -> ['A.1 ']
            'cod_item' : row[2],
            'desc_item': row[3], 'cod_lote': row[4], 'saldo'   : row[7],
            'id_carga' : row[5], 'id_req'  : row[6], 'time_mov': row[8]
        } for row in cursor.fetchall()]
    return result


@staticmethod
# RETORNA SALDO DO ITEM NO ENDEREÇO FORNECIDO
def get_saldo_item(rua_numero, rua_letra, cod_item, cod_lote):
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
        '''.format(a=sql_balance_template), (rua_numero, rua_letra, cod_item, cod_lote))
        saldo_item = cursor.fetchone()[0]
    return saldo_item
