from waitress import serve
from cde import app

print('Running on http://0.0.0.0:8000')

if __name__ == '__main__':
    serve(app, host='0.0.0.0', port=8000)
