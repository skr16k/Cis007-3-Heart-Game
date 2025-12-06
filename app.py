from bottle import Bottle, request, response, template, redirect, static_file, abort
from models import init_db, create_user, get_user_by_username, get_user_by_id, record_score, list_users, delete_user, update_user, get_attempts_for_user, get_total_points_leaderboard
from utils.security import hash_password, verify_password, encode_session, decode_session
from services.heart_api import fetch_puzzle
from config import DB_PATH
import os, json, sqlite3, re

app = Bottle()

def get_session():
    tok = request.get_cookie('session')
    if not tok: return None
    return decode_session(tok)

def login_required(fn):
    def w(*a, **kw):
        if not get_session(): return redirect('/login')
        return fn(*a, **kw)
    return w

def admin_required(fn):
    def w(*a, **kw):
        s = get_session()
        if not s or s[2] != 1: abort(403, 'Admin only')
        return fn(*a, **kw)
    return w

@app.get('/static/<path:path>')
def static(path):
    return static_file(path, root=os.path.join(os.path.dirname(__file__), 'static'))

@app.get('/')
def home():
    return template('views/index', session=get_session())

@app.get('/register')
def register():
    return template('views/register', error=None)

@app.post('/register')
def register_post():
    u = request.forms.get('username','').strip()
    p = request.forms.get('password','')
    if len(u) < 3:
        return template('views/register', error='Username too short')
    # Password policy: at least 8 chars and includes a special character
    if len(p) < 8 or not re.search(r'[^A-Za-z0-9]', p):
        return template('views/register', error='Password must be at least 8 characters and include a special character')
    s,h = hash_password(p); ok = create_user(u,h,0,s)
    if not ok: return template('views/register', error='Username already exists')
    user = get_user_by_username(u); response.set_cookie('session', encode_session(user['id'],user['username'],user['is_admin']), httponly=True, secure=False)
    redirect('/profile')

@app.get('/login')
def login():
    return template('views/login', error=None)

@app.post('/login')
def login_post():
    u = request.forms.get('username','').strip()
    p = request.forms.get('password','')
    user = get_user_by_username(u)
    if not user or not verify_password(p, user['password_salt'], user['password_hash']):
        return template('views/login', error='Invalid credentials')
    response.set_cookie('session', encode_session(user['id'],user['username'],user['is_admin']), httponly=True, secure=False)
    redirect('/profile')

@app.get('/logout')
def logout():
    response.delete_cookie('session'); redirect('/')

@app.get('/leaderboard')
def leaderboard_page():
    return template('views/leaderboard', session=get_session(), rows=get_total_points_leaderboard(200))

@app.get('/api/puzzle')
@login_required
def api_puzzle():
    d = request.query.get('difficulty','easy')
    lvl = int(request.query.get('level','1'))
    data = fetch_puzzle(d,lvl); response.content_type = 'application/json'; return json.dumps(data)

@app.post('/api/submit')
@login_required
def api_submit():
    uid,un,adm = get_session()
    d = request.forms.get('difficulty','easy')
    lvl = int(request.forms.get('level','1'))
    ans = request.forms.get('answer','')
    corr = request.forms.get('correct','')
    correct = 1 if ans.strip()==str(corr).strip() else 0
    secs = int(request.forms.get('seconds_taken','0'))
    points = (20 + secs) if correct==1 else 0
    record_score(uid, d, lvl, secs, correct, points)
    response.content_type='application/json'; return json.dumps({'ok':True,'correct':correct,'points':points})

@app.get('/profile')
@login_required
def profile():
    s = get_session(); uid = s[0]
    return template('views/profile', session=s, attempts=get_attempts_for_user(uid), user=get_user_by_id(uid))

@app.get('/admin')
@admin_required
def admin_panel():
    return template('views/admin', session=get_session(), users=list_users(), msg=None)

@app.post('/admin/delete_user')
@admin_required
def admin_delete_user():
    delete_user(int(request.forms.get('user_id'))); redirect('/admin')

@app.post('/admin/create_user')
@admin_required
def admin_create_user():
    u = request.forms.get('username','').strip()
    p = request.forms.get('password','').strip()
    a = 1 if request.forms.get('is_admin')=='on' else 0
    if len(u) < 3:
        return template('views/admin', session=get_session(), users=list_users(), msg='Username too short')
    # Enforce same password policy as registration
    if len(p) < 8 or not re.search(r'[^A-Za-z0-9]', p):
        return template('views/admin', session=get_session(), users=list_users(), msg='Password must be at least 8 characters and include a special character')
    s,h = hash_password(p); ok = create_user(u,h,a,s)
    return template('views/admin', session=get_session(), users=list_users(), msg=('User created' if ok else 'Username exists'))

@app.get('/admin/edit/<uid:int>')
@admin_required
def admin_edit_user(uid):
    u = get_user_by_id(uid)
    if not u: abort(404,'User not found')
    return template('views/admin_edit', session=get_session(), u=u, error=None)

@app.post('/admin/update_user')
@admin_required
def admin_update_user():
    uid = int(request.forms.get('user_id'))
    newu = request.forms.get('username','').strip()
    is_admin = 1 if request.forms.get('is_admin')=='on' else 0
    newp = request.forms.get('password','').strip()
    if len(newu)<3:
        return template('views/admin_edit', session=get_session(), u=get_user_by_id(uid), error='Username too short')
    u = get_user_by_id(uid)
    if u and u['username']=='admin': is_admin = 1
    if newp:
        s,h = hash_password(newp); update_user(uid, username=newu, is_admin=is_admin, password_salt=s, password_hash=h)
    else:
        update_user(uid, username=newu, is_admin=is_admin)
    redirect('/admin')

if __name__=='__main__':
    if not os.path.exists(DB_PATH): open(DB_PATH,'a').close()
    init_db()
    con = sqlite3.connect(DB_PATH); cur = con.cursor(); cur.execute("SELECT id FROM users WHERE username='admin'"); row = cur.fetchone()
    if not row:
        s,h = hash_password('admin1234'); cur.execute('INSERT INTO users(username,password_salt,password_hash,is_admin) VALUES(?,?,?,1)',('admin',s,h)); print('Initialized DB. Admin login: admin / admin1234')
    con.commit(); con.close()
    app.run(host='0.0.0.0', port=8080, debug=True, reloader=False)
