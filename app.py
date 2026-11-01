from flask import Flask, request, redirect, url_for, render_template, session
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'un_super_secret_pour_les_sessions'

def get_db():
    return sqlite3.connect('base.db')

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        nom = request.form.get('nom')
        message = request.form.get('message')
        if nom and message:
            date_actuelle = datetime.now().strftime("%d/%m/%Y à %H:%M")
            conn = get_db()
            conn.execute('INSERT INTO visiteurs (nom, message, date) VALUES (?, ?, ?)', (nom, message, date_actuelle))
            conn.commit()
            conn.close()
            return redirect(url_for('home'))

    recherche = request.args.get('search', '')
    conn = get_db()
    conn.execute('CREATE TABLE IF NOT EXISTS visiteurs (nom TEXT, message TEXT, date TEXT, likes INTEGER DEFAULT 0)')
    
    if recherche:
        query = 'SELECT rowid, nom, message, date, likes FROM visiteurs WHERE nom LIKE ? OR message LIKE ? ORDER BY likes DESC'
        params = ('%' + recherche + '%', '%' + recherche + '%')
        rows = conn.execute(query, params).fetchall()
    else:
        rows = conn.execute('SELECT rowid, nom, message, date, likes FROM visiteurs ORDER BY likes DESC').fetchall()
    
    conn.close()
    return render_template('index.html', visiteurs=rows, recherche=recherche)

@app.route('/login', methods=['GET', 'POST'])
def login():
    erreur = None
    if request.method == 'POST':
        if request.form.get('password') == 'admin123':
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
    conn.execute('UPDATE visiteurs SET likes = likes + 1 WHERE rowid = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('home'))

@app.route('/clear', methods=['POST'])
def clear():
    if not session.get('admin'): return redirect(url_for('home'))
    conn = get_db()
    conn.execute('DELETE FROM visiteurs')
    conn.commit()
    conn.close()
    return redirect(url_for('home'))

@app.route('/delete/<int:id>')
def delete(id):
    if not session.get('admin'): return redirect(url_for('home'))
    conn = get_db()
    conn.execute('DELETE FROM visiteurs WHERE rowid = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('home'))

@app.route('/edit/<int:id>')
def edit(id):
    if not session.get('admin'): return redirect(url_for('home'))
    conn = get_db()
    visiteur = conn.execute('SELECT rowid, nom, message FROM visiteurs WHERE rowid = ?', (id,)).fetchone()
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
    conn.execute('UPDATE visiteurs SET nom = ?, message = ?, date = ? WHERE rowid = ?', (nouveau_nom, nouveau_message, date_actuelle, id))
    conn.commit()
    conn.close()
    return redirect(url_for('home'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
