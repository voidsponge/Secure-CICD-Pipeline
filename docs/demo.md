# Démo : le pipeline bloque une faille

Cette démo montre en deux minutes que le pipeline fait son travail.

## 1. Créer une branche avec une injection SQL

```bash
git checkout -b demo/sql-injection
```

Dans `app/__init__.py`, remplacer la requête paramétrée de `get_note` par une concaténation,
et changer la route pour accepter du texte :

```python
@app.get("/notes/<note_id>")
def get_note(note_id):
    row = get_db().execute(
        f"SELECT id, title, body FROM notes WHERE id = {note_id}"  # VULNÉRABLE
    ).fetchone()
```

## 2. Ajouter un faux secret

```bash
echo 'AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"' >> app/config.py
```

## 3. Ouvrir la pull request

```bash
git add -A && git commit -m "demo: introduce vulnerabilities"
git push -u origin demo/sql-injection
```

## Ce qui se passe

- **Ruff** signale `S608` (requête SQL construite par interpolation de chaîne).
- **Semgrep** signale une requête SQL formatée avec une entrée utilisateur.
- **CodeQL** trace le flux de `note_id` depuis l'URL jusqu'à `execute()` et commente la ligne.
- **Gitleaks** détecte la clé AWS.
- Le bouton **Merge** reste grisé tant que les contrôles sont rouges.

Pensez à faire des captures d'écran de la PR pour le portfolio, puis fermez-la sans merger
et supprimez la branche. Comme Gitleaks scanne l'historique, ne mergez jamais cette branche.
