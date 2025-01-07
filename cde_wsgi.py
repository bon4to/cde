import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('waitress')
logger.setLevel(logging.ERROR)

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
    GRANTED  = f'{ANSI.CYAN}200{ANSI.RESET}'
    DENIED   = f'{ANSI.RED}403{ANSI.RESET}'
    STATUS   = f'{ANSI.GREEN}[STATUS]{ANSI.RESET}'
    ERRO     = f'{ANSI.RED}[ERRO]{ANSI.RESET}'
    INFO     = f'{ANSI.BLUE}[INFO]{ANSI.RESET}'


if __name__ == '__main__':
    from waitress import serve
    from cde import app

    port = 5005
    
    print(f'{TAGS.STATUS} Running on: localhost:{port}\n')
    serve(app, host='0.0.0.0', port=port)