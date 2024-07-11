import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('waitress')
logger.setLevel(logging.ERROR)

if __name__ == '__main__':
    from waitress import serve
    from cde import app

    port = 5005
    
    print(f'[STATUS] Running on: http://192.168.1.20:{port}\n')
    serve(app, host='0.0.0.0', port=port)