from datetime import datetime
import sys

from app.utils import cdeapp

TAGS = {
    1: "[CDE]",
    2: "[INF]",
    3: "[ERR]",
    4: "[STATUS]"
}

cde_header = """
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
"""


def start_header(version, release_date):
    return f"""
{TAGS.get(1)} CDE Version: {version} (beta) - {release_date}
{TAGS.get(2)} Python Version: {sys.version}
{TAGS.get(2)} Starting in: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
"""


def log(tag_i: int, text: str, tag_2: str="") -> None:
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    tag = TAGS.get(tag_i, '[CDE]') 
    
    if not tag_2:
        print(f'{tag} ({timestamp}) | {text}')
        return
    print(f'{tag} ({timestamp}) {tag_2} | {text}')
    return


@staticmethod
def debug_log(text: str) -> None:
    debug = cdeapp.config.get_debug()
    if debug:
        print(f'[DBG] {text}')


error_header = f"""
* Impossível executar, verifique se o arquivo está alocado corretamente.

Pressione ENTER para sair...
"""
