import sqlite3,os
from config import DB_PATH

def get_conn():
    c=sqlite3.connect(DB_PATH,check_same_thread=False); c.row_factory=sqlite3.Row; return c

def init_db():
    c=get_conn(); cur=c.cursor(); cur.executescript(open(os.path.join(os.path.dirname(DB_PATH),'schema.sql'),'r',encoding='utf-8').read());
    cur.execute('PRAGMA table_info(scores)'); cols=[r[1] for r in cur.fetchall()]
    if 'points' not in cols:
        cur.execute('ALTER TABLE scores ADD COLUMN points INTEGER NOT NULL DEFAULT 0')
    c.commit(); c.close()

def create_user(u,h,adm=0,s=''):
    try:
        c=get_conn(); cur=c.cursor(); cur.execute('INSERT INTO users(username,password_salt,password_hash,is_admin) VALUES(?,?,?,?)',(u,s,h,adm)); c.commit(); return True
    except sqlite3.IntegrityError:
        return False
    finally:
        c.close()

def get_user_by_username(u):
    c=get_conn(); cur=c.cursor(); cur.execute('SELECT * FROM users WHERE username=?',(u,)); r=cur.fetchone(); c.close(); return r

def get_user_by_id(i):
    c=get_conn(); cur=c.cursor(); cur.execute('SELECT * FROM users WHERE id=?',(i,)); r=cur.fetchone(); c.close(); return r

def list_users():
    c=get_conn(); cur=c.cursor(); cur.execute('SELECT id,username,is_admin,created_at FROM users ORDER BY id DESC'); rows=cur.fetchall(); c.close(); return rows

def update_user(i,*,username=None,is_admin=None,password_salt=None,password_hash=None):
    sets=[]; vals=[]
    if username is not None: sets.append('username=?'); vals.append(username)
    if is_admin is not None: sets.append('is_admin=?'); vals.append(is_admin)
    if password_salt is not None: sets.append('password_salt=?'); vals.append(password_salt)
    if password_hash is not None: sets.append('password_hash=?'); vals.append(password_hash)
    if not sets: return
    vals.append(i)
    c=get_conn(); cur=c.cursor(); cur.execute(f"UPDATE users SET {', '.join(sets)} WHERE id=?",vals); c.commit(); c.close()

def delete_user(i):
    c=get_conn(); cur=c.cursor(); cur.execute('DELETE FROM users WHERE id=?',(i,)); c.commit(); c.close()

def record_score(uid,diff,level,secs,correct,points):
    c=get_conn(); cur=c.cursor(); cur.execute('INSERT INTO scores(user_id,difficulty,level,seconds_taken,correct,points) VALUES(?,?,?,?,?,?)',(uid,diff,level,secs,correct,points)); c.commit(); c.close()

def get_attempts_for_user(uid):
    c=get_conn(); cur=c.cursor(); cur.execute('SELECT difficulty,level,seconds_taken,correct,points,created_at FROM scores WHERE user_id=? ORDER BY created_at DESC',(uid,)); rows=cur.fetchall(); c.close(); return rows

def get_total_points_leaderboard(limit=100):
    c=get_conn(); cur=c.cursor(); cur.execute('SELECT u.id as user_id,u.username,COALESCE(SUM(s.points),0) as total_points,MAX(s.created_at) as last_played FROM users u LEFT JOIN scores s ON s.user_id=u.id GROUP BY u.id,u.username ORDER BY total_points DESC,last_played DESC LIMIT ?', (limit,)); rows=cur.fetchall(); c.close(); return rows
