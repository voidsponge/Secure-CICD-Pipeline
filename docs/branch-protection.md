# Protection de la branche `main`

Dans **Settings → Rules → Rulesets → New branch ruleset** (ou **Settings → Branches**) :

1. **Target** : la branche par défaut (`main`).
2. Cocher **Require a pull request before merging**.
3. Cocher **Require status checks to pass** et ajouter :
   - `Lint et tests`
   - `Secrets (Gitleaks)`
   - `SAST (Semgrep)`
   - `Dépendances (pip-audit)`
   - `Image Docker (Trivy)`
   - `Analyse CodeQL (python)` et `Analyse CodeQL (actions)`
4. Cocher **Require code scanning results** avec CodeQL, seuil *High or higher*.
5. Cocher **Block force pushes**.

Les noms des checks n'apparaissent dans la liste qu'après leur premier passage :
poussez une première fois, puis configurez la règle.

Pensez aussi à activer, dans **Settings → Code security** :

- **Dependabot alerts** et **Dependabot security updates** ;
- **Secret scanning** et **Push protection** (bloque le push d'un secret avant même la CI).
