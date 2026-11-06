from flask import Flask, request, redirect, url_for, render_template, session
import psycopg2
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'un_super_secret_par_defaut')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')

def get_db():
    db_url = os.environ.get('DATABASE_URL')
    conn = psycopg2.connect(db_url, sslmode='require', connect_timeout=30)
    return conn

@app.route('/', methods=['GET', 'POST'])
def home():
    try:
        conn = get_db()
        cur = conn.cursor()
        
        # 1. Création de la table si elle n'existe pas
        cur.execute('''
            CREATE TABLE IF NOT EXISTS visiteurs (
                id SERIAL PRIMARY KEY,
                nom TEXT,
                message TEXT,
                date TEXT,
                likes INTEGER DEFAULT 0,
                photo TEXT
            )
        ''')
        
        # 2. LA LIGNE MAGIQUE : On ajoute la colonne si elle manque
        cur.execute('ALTER TABLE visiteurs ADD COLUMN IF NOT EXISTS photo TEXT;')
        conn.commit()
        
        if request.method == 'POST':
            nom = request.form.get('nom')
            message = request.form.get('message')
            photo = request.form.get('photo')
            if nom and message:
                date_actuelle = datetime.now().strftime("%d/%m/%Y à %H:%M")
                cur.execute('INSERT INTO visiteurs (nom, message, date, photo) VALUES (%s, %s, %s, %s)', (nom, message, date_actuelle, photo))
                conn.commit()
                return redirect(url_for('home'))

        recherche = request.args.get('search', '')
        if recherche:
            cur.execute('SELECT id, nom, message, date, likes, photo FROM visiteurs WHERE nom ILIKE %s OR message ILIKE %s ORDER BY likes DESC', 
                        ('%' + recherche + '%', '%' + recherche + '%'))
        else:
            cur.execute('SELECT id, nom, message, date, likes, photo FROM visiteurs ORDER BY likes DESC')
        
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        return render_template('index.html', visiteurs=rows, recherche=recherche)
        
    except Exception as e:
        return f"<div style='background:#000; color:red; padding:20px; font-family:sans-serif;'><h1>Erreur de connexion :</h1><p style='background:#333; padding:10px;'>{e}</p></div>"

@app.route('/login', methods=['GET', 'POST'])
def login():
    erreur = None
    if request.method == 'POST':
        if request.form.get('password') == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect(url_for('home'))
        else:
            erreur = "Mot de passe incorrect !"
    return render_template('login.html', erreur=erreur)

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('home'))

@app.route('/like/<int:id>')
def like(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('UPDATE visiteurs SET likes = likes + 1 WHERE id = %s', (id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('home'))

@app.route('/clear', methods=['POST'])
def clear():
    if not session.get('admin'): return redirect(url_for('home'))
    conn = get_db()
    cur = conn.cursor()
    cur.execute('DELETE FROM visiteurs')
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('home'))

@app.route('/delete/<int:id>')
def delete(id):
    if not session.get('admin'): return redirect(url_for('home'))
    conn = get_db()
    cur = conn.cursor()
    cur.execute('DELETE FROM visiteurs WHERE id = %s', (id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('home'))

@app.route('/edit/<int:id>')
def edit(id):
    if not session.get('admin'): return redirect(url_for('home'))
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT id, nom, message FROM visiteurs WHERE id = %s', (id,))
    visiteur = cur.fetchone()
    cur.close()
    conn.close()
    if visiteur:
        return render_template('edit.html', visiteur=visiteur)
    return redirect(url_for('home'))

@app.route('/update/<int:id>', methods=['POST'])
def update(id):
    if not session.get('admin'): return redirect(url_for('home'))
    nouveau_nom = request.form.get('nom')
    nouveau_message = request.form.get('message')
    date_actuelle = datetime.now().strftime("%d/%m/%Y à %H:%M (modifié)")
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute('UPDATE visiteurs SET nom = %s, message = %s, date = %s WHERE id = %s', (nouveau_nom, nouveau_message, date_actuelle, id))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('home'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)