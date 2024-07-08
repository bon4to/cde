import os
import subprocess
from datetime import datetime
import zipfile

REPO_URL = "https://github.com/bon4to/cde.git"
CLONE_DIR = "C:/Users/analista.dados/Desktop/Updater"
BACKUP_DIR = os.path.join(CLONE_DIR, "backup")


def clone_or_pull_repo():
    if os.path.exists(CLONE_DIR):
        if os.path.exists(os.path.join(CLONE_DIR, '.git')):
            subprocess.run(["git", "-C", CLONE_DIR, "pull"], check=True)
        else:
            raise Exception(f"{CLONE_DIR} existe mas não é um repositório Git válido.")
    else:
        subprocess.run(["git", "clone", REPO_URL, CLONE_DIR], check=True)


def create_backup():
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)

    backup_name = os.path.join(BACKUP_DIR, f"cde-backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip")
    
    with zipfile.ZipFile(backup_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(CLONE_DIR):
            if '.git' in dirs:
                dirs.remove('.git')
            if 'backup' in dirs:
                dirs.remove('backup')
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, os.path.relpath(file_path, CLONE_DIR))

    print(f"Backup created: {backup_name}")


def main():
    try:
        create_backup()
    except Exception as e:
        input(f"Error during backup: {e}")
    else:
        try:
            clone_or_pull_repo()
        except Exception as e:
            input(f"Error during update: {e}")
    finally:
        input("Update and backup process completed.")


if __name__ == "__main__":
    main()
