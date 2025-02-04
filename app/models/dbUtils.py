import sqlite3

@staticmethod
# GERADOR DE TABELAS
def create_tables(database) -> None:
    with sqlite3.connect(database) as connection:
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
