"""Decode generated PNGs and verify signed checkpoint URLs. pip install zxing-cpp"""
import json,sys,os
from pathlib import Path
from urllib.parse import urlparse,parse_qs
import zxingcpp
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'api'))
from runtime import load_environment
import os
os.environ.update(load_environment())
from app.services.qr_signer import verify_checkpoint_qr
root=Path(sys.argv[1] if len(sys.argv)>1 else 'qr')
for row in json.loads((root/'manifest.json').read_text()):
    result=zxingcpp.read_barcode(Image.open(root/row['png']))
    assert result and result.text==row['payload'],row['png']
    if result.text.startswith('http'):
        token=parse_qs(urlparse(result.text).query)['token'][0]
        if token.startswith('YK1:CP:'):assert verify_checkpoint_qr(token,row.get('key_version',1))[0],row['png']
        else:assert token.startswith('YK1:') and len(token.split(':')[1])==6
print('QR decode round trip passed for every poster and pass.')
