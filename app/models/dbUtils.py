import re
import sqlite3, os, requests, pyodbc
from dotenv import load_dotenv

from app.utils import cdeapp
from app.models import logTexts

# carrega o .env
load_dotenv()


def get_file_text(dir) -> str:
    try:
        with open(dir, "r") as file:
            return file.read().strip()
    except Exception as e:
        logTexts.log(3, e)
        return ""


class QueryManager:
    """
    Classe responsável por carregar e manipular queries SQL dinâmicas.
    """

    # Dicionário onde as queries serão armazenadas
    QUERIES = {}

    @classmethod
    def load_queries(cls, file_path: str):
        """
        Carrega as queries do arquivo para o dicionário QUERIES, permitindo múltiplas linhas.

        Parâmetros:
            file_path (str): Caminho do arquivo contendo as queries.
        """
        with open(file_path, "r", encoding="utf-8") as file:
            lines = file.readlines()

        queries = {}
        current_id = None
        current_query = []

        for line in lines:
            line = line.strip()

            if not line:  # Ignora linhas vazias
                continue

            if re.match(r"^\d+\s*:", line):  # Nova query encontrada
                if (
                    current_id is not None
                ):  # Salva a query anterior antes de iniciar uma nova
                    queries[current_id] = " ".join(current_query).strip()

                parts = line.split(":", 1)
                current_id = int(parts[0].strip())  # Pega o ID
                current_query = [parts[1].strip()]  # Começa uma nova query

            else:
                if current_id is not None:  # Continua a query anterior
                    current_query.append(line)

        if current_id is not None:  # Salva a última query
            queries[current_id] = " ".join(current_query).strip()

        cls.QUERIES = queries

    @staticmethod
    def get_all_queries() -> dict:
        return QueryManager.QUERIES

    @staticmethod
    def get(query_id: int, **variables) -> str:
        """
        Retorna uma query SQL formatada dinamicamente com os valores fornecidos.

        Parâmetros:
            query_id (int): O identificador da query armazenada no dicionário QUERIES.
            **variables: Argumentos nomeados que representam os valores a serem inseridos na query (passar conforme o nome definido dentro da query).

        Retorno:
            str: A query SQL formatada com os valores substituídos.

        Exceções:
            ValueError: Se o 'query_id' não existir no dicionário QUERIES.
        """
        QueryManager.load_queries("db/queries/queries.txt")

        query = QueryManager.QUERIES.get(query_id)

        if not query:
            raise ValueError(f"Query ID {query_id} not found")

        if "{" in query and variables:
            return query.format(**{k: v for k, v in variables.items()})

        return query


@staticmethod
# conexão e consulta no banco de dados
def query(query: str, method: str, source: int = 1):
    # TODO: criar métodos de mesclar consultas (ex: dadosNOE + dadosHP)

    # Timeout padrão para conexões externas (em segundos)
    API_TIMEOUT = int(os.getenv("API_TIMEOUT", 30))
    ODBC_TIMEOUT = int(os.getenv("ODBC_TIMEOUT", 15))
    if method == "API":
        # busca na api configurada
        url, headers = new_api_connection()
        data = {"query": query, "source": source}
        try:
            response = requests.post(
                url, headers=headers, json=data, timeout=API_TIMEOUT
            )

            if response.status_code == 200:
                try:
                    response_data = response.json()

                    # verifica se a resposta possui as chaves esperadas
                    if (
                        isinstance(response_data, dict)
                        and "columns" in response_data
                        and "data" in response_data
                    ):
                        # extrai colunas e dados
                        columns = response_data["columns"]
                        data = response_data["data"]

                        # converte 'data' em uma lista de listas para exibição tabular
                        result = [
                            [item.get(col, "") for col in columns] for item in data
                        ]

                        # sanitiza a lista result
                        result = [
                            [
                                str(item).strip() if item is not None else ""
                                for item in row
                            ]
                            for row in result
                        ]

                        # retorna as linhas e colunas
                        return result, columns
                    else:
                        logTexts.debug_log(
                            f"Formato inesperado da resposta: {response_data}"
                        )
                        return [[f"Erro: Formato inesperado da resposta da API"]], []

                except ValueError:
                    logTexts.debug_log(
                        f"Resposta inválida (não é JSON): {response.text}"
                    )
                    return [[f"Erro: Resposta inválida da API"]], []
            else:
                logTexts.debug_log(
                    f"Erro na API: {response.status_code} - {response.reason}"
                )
                return [[f"Erro HTTP {response.status_code}: {response.reason}"]], []

        except requests.exceptions.Timeout as e:
            logTexts.debug_log(f"Timeout na requisição à API: {str(e)}")
            return [
                [f"Erro: Timeout - A API não respondeu em {API_TIMEOUT} segundos."]
            ], []

        except requests.exceptions.ConnectionError as e:
            logTexts.debug_log(f"API offline ou inacessível: {str(e)}")
            return [[f"Erro: A API está offline ou inacessível no momento."]], []

        except Exception as e:
            logTexts.debug_log(f"Erro de conexão com a API: {str(e)}")
            return [[f"Erro: {str(e)}"]], []

    elif method == "ODBC-DRIVER":
        # busca nas DSNs configuradas (Fonte de Dados ODBC)
        # get user credentials
        user, password = get_odbc_user_credentials()

        dsn = source  # TODO: criar metodo que busca dns no .env conforme source
        try:
            connection = pyodbc.connect(
                f"DSN={dsn}", uid=user, pwd=password, timeout=ODBC_TIMEOUT
            )
            cursor = connection.cursor()
            cursor.execute(query)
            columns = [str(column[0]) for column in cursor.description]
            result = cursor.fetchall()

            cursor.close()
            connection.close()
        except pyodbc.OperationalError as e:
            logTexts.log(3, "Timeout ou erro de conexão ODBC:", str(e))
            result = [[f"Erro: Timeout na conexão com o banco de dados."]]
            columns = []
        except Exception as e:
            logTexts.log(3, "Erro ao enviar solicitação:", str(e))
            result = [[f"Erro de consulta: {e}"]]
            columns = []

    elif method == "LOCAL":
        # busca no arquivo local (.db)
        try:
            with sqlite3.connect(cdeapp.config.get_db_path()) as connection:
                cursor = connection.cursor()
                cursor.execute(query)

                # só pega os nomes das colunas se forem SELECTs
                if cursor.description:
                    columns = [str(column[0]) for column in cursor.description]
                    result = cursor.fetchall()
                else:
                    columns = []
                    result = [
                        ["Query executada com sucesso"]
                    ]  # Para INSERTs, UPDATEs, DELETEs
        except Exception as e:
            logTexts.debug_log(f"Erro ao enviar solicitação: {str(e)}")
            result = [[f"Erro de consulta: {e}"]]
            columns = []

    else:
        result = [[f"MÉTODO INVÁLIDO: {method}"]]
        columns = []

    return result, columns


@staticmethod
def new_api_connection():
    db_api = os.getenv("DB_API")
    url = f"http://{db_api}/query"
    headers = {"Content-Type": "application/json"}

    return url, headers


@staticmethod
def get_odbc_user_credentials():
    uid_pwd = os.getenv("DB_USER").split(";")
    return uid_pwd[0], uid_pwd[1]


@staticmethod
# GERADOR DE TABELAS
def create_tables(database) -> None:
    with sqlite3.connect(database) as connection:
        cursor = connection.cursor()

        # TABELA DE PROGRAMAÇÃO DO ENVASE
        cursor.execute(
            """
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
        """
        )

        # TABELA DE PROGRAMAÇÃO DA PROCESSAMENTO
        cursor.execute(
            """
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
        """
        )

        # TABELA HISTÓRICO
        cursor.execute(
            """
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
        """
        )

        # TABELA DE CLIENTES
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS clientes (
                cod_cliente      INTEGER(10) PRIMARY KEY,
                razao_cliente    VARCHAR(100),
                fantasia_cliente VARCHAR(100),
                cidade_cliente   VARCHAR(100),
                estado_cliente   VARCHAR(30)
            );
        """
        )

        # TABELA DE CARGAS PENDENTES
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tbl_carga_incomp (
                id_log        INTEGER PRIMARY KEY AUTOINCREMENT,
                id_carga      INTEGER(6),
                cod_item      VARCHAR(6),
                qtde_atual    INTEGER(20),
                qtde_solic    INTEGER(20),
                flag_pendente BOOLEAN DEFAULT TRUE
            );
        """
        )

        # TABELA DE STATUS DE CARGAS
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tbl_carga_status (
                id_log        INTEGER PRIMARY KEY AUTOINCREMENT,
                id_carga      INTEGER(6),
                status        VARCHAR(20),
                justificativa TEXT,
                id_user       INTEGER,
                timestamp     DATETIME DEFAULT CURRENT_TIMESTAMP,
                flag_ativo    BOOLEAN DEFAULT TRUE
            );
        """
        )

        # TABELA DE USUÁRIOS
        cursor.execute(
            """
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
        """
        )

        # TABELA DE PERMISSÕES DE USUÁRIO
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS user_permissions (
                id_user INTEGER, 
                id_perm VARCHAR(6)
            );
        """
        )

        # TABELA DE ITENS
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS itens (
                cod_item   VARCHAR(6) PRIMARY KEY,
                desc_item  VARCHAR(100),
                dun14      INTEGER(14),
                flag_ativo BOOLEAN DEFAULT TRUE
            );
        """
        )

        # TABELA AUXILIAR DE PRIVILÉGIOS
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS aux_privilege (
                id_priv   INTEGER(2) PRIMARY KEY,
                desc_priv VARCHAR(30) UNIQUE
            );
        """
        )

        # TABELA AUXILIAR DE PERMISSÕES
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS aux_permissions (
                id_perm   VARCHAR(6) PRIMARY KEY,
                desc_perm VARCHAR(100)
            );
        """
        )

        # TABELA AUXILIAR DE LINHAS
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS aux_linha (
                cod_linha  INTEGER(3),
                tipo_embal VARCHAR(10),
                lit_embal  VARCHAR(10)
            );
        """
        )

        connection.commit()
    return None


@staticmethod
# consulta tabelas do schema
def db_get_tables(dsn):
    try:
        if dsn == "ODBC-DRIVER":
            query_str = """
                SELECT TABNAME
                FROM SYSCAT.TABAUTH
                WHERE GRANTEE = 'CDEADMIN'
                AND SELECTAUTH = 'Y';
            """
        if dsn == "API":
            query_str = """
                SELECT TABNAME
                FROM SYSCAT.TABAUTH
                WHERE GRANTEE = 'CDEADMIN'
                AND SELECTAUTH = 'Y';
            """
        elif dsn == "LOCAL":
            query_str = """
                SELECT name 
                FROM sqlite_master 
                WHERE type = 'table' 
                    AND name NOT LIKE 'sqlite_%'
                ORDER BY name;
            """
        else:
            return [[f"DSN desconhecida: {dsn}"]]

    except Exception as e:
        return [[f"Erro de consulta: {e}"]]

    return query(query_str, dsn)[0]
