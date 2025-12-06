import random,time,requests
from config import HEART_API_ENDPOINTS

def fetch_puzzle(difficulty,level):
    params={'difficulty':difficulty,'level':level,'ts':int(time.time())}
    for url in HEART_API_ENDPOINTS:
        try:
            r=requests.get(url,params=params,timeout=8)
            if r.ok:
                data=r.json(); raw_q=data.get('question') or data.get('puzzle'); raw_img=data.get('image') or data.get('img') or data.get('url');
                image_url=raw_img; question_text=raw_q or 'Heart Puzzle'
                if isinstance(question_text,str) and question_text.lower().endswith(('.png','.jpg','.jpeg')):
                    image_url=question_text; question_text='Solve the puzzle shown:'
                return {'question':question_text,'image':image_url or None,'answer':data.get('answer') or data.get('solution') or None,'meta':{'source':url,'difficulty':difficulty,'level':level}}
        except Exception:
            continue
    a,b=random.randint(1,9),random.randint(1,9)
    return {'question':f'If ♥ is {a} and ♦ is {b}, what is ♥ + ♦ ?','image':None,'answer':a+b,'mock':True,'meta':{'error':'fallback','difficulty':difficulty,'level':level}}
