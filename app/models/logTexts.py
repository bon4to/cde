from datetime import datetime
import sys

TAGS = {
    "INFO": "[INFO]",
    "STATUS": "[STATUS]",
    "ERROR": "[ERROR]"
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
{TAGS["INFO"]} CDE Version: {version} (beta) - {release_date}
{TAGS["INFO"]} Python Version: {sys.version}
{TAGS["STATUS"]} Starting in: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
"""


def log(tag_1, tag_2, text) -> None:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if not tag_2:
            print(f'{tag_1} {text}')
            return
        print(f'{tag_1} ({timestamp}) {tag_2} | {text}')
        return


error_header = f"""
{TAGS["ERROR"]} 
* Impossível executar, verifique se o arquivo está alocado corretamente.

Pressione ENTER para sair...
"""
