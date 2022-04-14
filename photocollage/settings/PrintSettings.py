from PIL import ImageFont
import os, getpass
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

IMAGE_WITH_BLEED_SIZE = (2625, 3375)

FONT_FOLDER = os.path.join('/Users', getpass.getuser(), 'GoogleDrive', 'Fonts')

TEXT_FONT = ImageFont.truetype(os.path.join(FONT_FOLDER, "open-sans", "OpenSans-Bold.ttf"), 100)
SIGNIKA_TEXT_FONT = ImageFont.truetype(os.path.join(FONT_FOLDER, "Signika", "Signika-Bold.ttf"), 100)

pdfmetrics.registerFont(TTFont('Signika', 'Signika-Bold.ttf'))

