from pathlib import Path
import io
import qrcode
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

FONTS=Path(__file__).parents[1]/'fonts'
def poster(name, hindi, subtitle, token):
    img=Image.new('RGB',(2480,3508),'#F3EFE6');d=ImageDraw.Draw(img)
    def line(text,y,size=70,hi=False,color='#1B2620'):
        font=ImageFont.truetype(str(FONTS/('NotoSansDevanagari.ttf' if hi else 'DejaVuSans.ttf')),size)
        while d.textbbox((0,0),text,font=font)[2]>2200:
            size-=2;font=ImageFont.truetype(str(FONTS/('NotoSansDevanagari.ttf' if hi else 'DejaVuSans.ttf')),size)
        d.text((1240,y),text,fill=color,font=font,anchor='mt')
    d.rectangle((100,100,2380,3408),outline='#2F4B3A',width=8)
    line('YATRA KAVACH',230,100,color='#2F4B3A');line('यात्रा कवच',380,95,True)
    d.line((240,560,2240,560),fill='#C4541A',width=12)
    line(name,700,95);line(hindi,865,90,True);line(subtitle,1040,60)
    qr=qrcode.make(token,error_correction=qrcode.constants.ERROR_CORRECT_M).convert('RGB')
    qr=qr.resize((1320,1320),Image.Resampling.NEAREST);img.paste(qr,(580,1230))
    line('Scan to check in',2690,90);line('चेक इन के लिए स्कैन करें',2840,80,True)
    line('Emergency / 112 / 108',3050,75,color='#2F4B3A');line('Simulated demo data · Indicative data',3250,45)
    return img

def pdf_bytes(image):
    out=io.BytesIO();c=canvas.Canvas(out,pagesize=(595.276,841.89));c.drawImage(ImageReader(image),0,0,width=595.276,height=841.89);c.showPage();c.save();return out.getvalue()
