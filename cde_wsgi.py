import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("waitress")
logger.setLevel(logging.ERROR)


class TAGS:
    SERVIDOR = "[SERVIDOR]"
    GRANTED = "200"
    DENIED = "403"
    STATUS = "[STATUS]"
    ERRO = "[ERRO]"
    INFO = "[INFO]"


if __name__ == "__main__":
    from waitress import serve
    from cde import app

    port = 5005

    print(f"{TAGS.STATUS} Running on: localhost:{port}\n")
    serve(app, host="0.0.0.0", port=port)
