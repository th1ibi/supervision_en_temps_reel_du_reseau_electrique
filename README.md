# supervision_en_temps_reel_du_reseau_electrique



---

## ⚙️ Installation des dépendances

### 📁 Backend – Création d’un environnement virtuel Python (`venv`)

1. **Se placer dans le dossier `backend`** :

   ```bash
   cd backend
   ```

2. **Créer l’environnement virtuel** :

   ```bash
   python -m venv venv
   ```

3. **Activer l’environnement virtuel** :

   * Sur **Windows** :

     ```bash
     venv\Scripts\activate
     ```
   * Sur **Linux/macOS** :

     ```bash
     source venv/bin/activate
     ```

4. **(Optionnel) Installer les dépendances si `requirements.txt` existe** :

   ```bash
   pip install -r requirements.txt
   ```

5. **(Optionnel) Sauvegarder les nouvelles dépendances** :

   ```bash
   pip freeze > requirements.txt
   ```

> Une fois activé, vous verrez le nom de l’environnement virtuel affiché dans votre terminal comme ceci : `(venv)`.

---

### 🌐 Frontend – Installation des dépendances Node.js

1. **Se placer dans le dossier `frontend`** :

   ```bash
   cd frontend
   ```

2. **Vérifier que le fichier `package.json` est présent**, puis lancer l’installation des dépendances :

   * Avec **npm** :

     ```bash
     npm install
     ```

   * Ou avec **yarn** :

     ```bash
     yarn install
     ```

3. Cela va automatiquement créer un dossier `node_modules/` et un fichier `package-lock.json` ou `yarn.lock`.

4. **(Optionnel) Lancer le projet en développement** :

   ```bash
   npm start
   ```

   ou

   ```bash
   npm run dev
   ```

---

> ✅ **Bonnes pratiques :**
>
> * N’ajoutez **jamais** les dossiers `venv/` et `node_modules/` dans le dépôt Git.
> * Assurez-vous que les fichiers `.gitignore` dans `backend/` et `frontend/` les incluent :
>
>   ```
>   venv/
>   node_modules/
>   ```

---

