import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('waitress')
logger.setLevel(logging.ERROR)

class ANSI:
    RESET = "\u001b[0m"
    BOLD = "\u001b[1m"
    RED = "\u001b[31m"
    GREEN = "\u001b[32m"
    YELLOW = "\u001b[33m"
    BLUE = "\u001b[34m"
    MAGENTA = "\u001b[35m"
    CYAN = "\u001b[36m"
    WHITE = "\u001b[37m"


class TAGS:
    SERVIDOR = f'{ANSI.MAGENTA}[SERVIDOR]{ANSI.RESET}'
    GRANTED  = f'{ANSI.CYAN}200{ANSI.RESET}'
    DENIED   = f'{ANSI.RED}403{ANSI.RESET}'
    STATUS   = f'{ANSI.GREEN}[STATUS]{ANSI.RESET}'
    ERRO     = f'{ANSI.RED}[ERRO]{ANSI.RESET}'
    INFO     = f'{ANSI.BLUE}[INFO]{ANSI.RESET}'


if __name__ == '__main__':
    from waitress import serve
    from cde import app

    port = 5005
    
    print(f'{TAGS.STATUS} Running on: http://192.168.1.20:{port}\n')
    serve(app, host='0.0.0.0', port=port)