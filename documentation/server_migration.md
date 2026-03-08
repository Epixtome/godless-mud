Summary of Migration Steps
On Windows (Local):

Run @exportzone all in-game. This ensures your data/zones/*.json files match your current database.
Create a .gitignore file in your project root (if you haven't already) and add:
text
data/world.db*
__pycache__/
*.pyc
Commit and push the code and the JSON files to Git.
On Linux (Google Cloud):

git pull your repo.
Run the server (python godless_mud.py).
The server will see that world.db is missing.
It will automatically run the migration script, reading your JSON files and building a Linux-compatible world.db.