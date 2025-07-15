import textwrap, io, base64, qrcode
from PIL import Image, ImageDraw, ImageFont

from app.models import logTexts

IMAGE_SIZE = (400, 400)

@staticmethod
# cria qrcode
def qr_code(qr_text):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=5,
        border=5,
    )
    qr.add_data(qr_text)
    qr.make(fit=True)
    qr_image = qr.make_image(fill_color='black', back_color='white')
    qr_image = qr_image.convert('RGB')
    return qr_image

@staticmethod
def generate(qr_text, desc_item, cod_item, cod_lote) -> str:
    """
    gera uma etiqueta com QR Code e descrição.
    retorna a imagem em base64.
    """
    img = _create_base_image()
    qr_image = qr_code(qr_text)

    _paste_qr_code(img, qr_image)
    _draw_text(img, cod_item, desc_item, cod_lote)

    return _image_to_base64(img)


@staticmethod
def _create_base_image():
    """cria a imagem base limpa."""
    return Image.new('RGB', IMAGE_SIZE, color='white')


@staticmethod
def _paste_qr_code(img, qr_image):
    """adiciona o QR Code na imagem centralizada."""
    width, height = img.size
    qr_width, qr_height = qr_image.size

    # redimensiona o QR Code se necessário
    if qr_width > width or qr_height > height:
        qr_image = qr_image.resize((width // 2, height // 2))

    qr_x = (width - qr_width) // 2
    qr_y = (height - qr_height) // 2
    # Specify the box with (left, top, right, bottom) coordinates
    box = (qr_x, qr_y, qr_x + qr_width, qr_y + qr_height)
    img.paste(qr_image, box)


@staticmethod
def _draw_text(img, cod_item, desc_item, cod_lote):
    """desenha os textos na imagem."""
    draw = ImageDraw.Draw(img)
    width, height = img.size

    # configura fonte
    try:
        font_path = "static/fonts/arialbd.ttf"
        font_large = ImageFont.truetype(font_path, 30)
        font_small = ImageFont.truetype(font_path, 24)
    except:
        # usa fonte padrão da biblioteca
        logTexts.log("Erro ao carregar fonte Arial, é recomendável baixar e utilizar a fonte 'arialbd.ttf'")
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # desenha o código do lote
    cod_lote_text = f'LOTE: {cod_lote}'
    lote_bbox = draw.textbbox((0, 0), cod_lote_text, font=font_large)
    lote_x = (width - (lote_bbox[2] - lote_bbox[0])) // 2
    lote_y = height // 1.5
    draw.text((lote_x, lote_y), cod_lote_text, fill='black', font=font_large)

    # desenha a descrição do item em múltiplas linhas
    desc_text = f'{cod_item} - {desc_item}'
    lines = textwrap.wrap(desc_text, width=30)
    y_text = height - height // 4.6

    for line in lines:
        text_width, text_height = draw.textbbox((0, 0), line, font=font_small)[2:]
        line_x = (width - text_width) // 2
        draw.text((line_x, y_text), line, fill='black', font=font_small)
        y_text += text_height


@staticmethod
def _image_to_base64(img):
    """converte a imagem para base64."""
    img_io = io.BytesIO()
    img.save(img_io, format='PNG')
    img_io.seek(0)
    return base64.b64encode(img_io.getvalue()).decode()
