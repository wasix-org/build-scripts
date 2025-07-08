from PIL import Image
from io import BytesIO

img = Image.new('RGB', (10, 10), color='blue')

def assert_save_and_load_image(format):
    buffer = BytesIO()
    img.save(buffer, format=format)
    buffer.seek(0)
    loaded_img = Image.open(buffer, formats=[format])
    assert loaded_img.size == (10, 10)

assert_save_and_load_image('GIF')
assert_save_and_load_image('WEBP')
assert_save_and_load_image('PNG')
assert_save_and_load_image('JPEG')
assert_save_and_load_image('BMP')
assert_save_and_load_image('TIFF')