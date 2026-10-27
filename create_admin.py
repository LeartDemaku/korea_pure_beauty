# create_admin.py
# Krijon një llogari administratori nga terminali.
# Ky është i vetmi vend ku mund të krijohet një admin: faqja web nuk e lejon më,
# sepse aty kushdo mund të bëhej administrator.
# Përdorimi:  python create_admin.py
from getpass import getpass

import auth
import database


def main() -> None:
    database.init_database()
    print("🌸 Korea Pure Beauty — Krijimi i llogarisë së administratorit")
    print(f"   Administratorë ekzistues: {database.count_admins()}\n")

    username = input("Username i ri: ").strip()
    # getpass e fsheh fjalëkalimin ndërsa shkruhet (nuk shfaqet në ekran)
    password = getpass(f"Fjalëkalimi (të paktën {auth.ADMIN_MIN_PASSWORD_LENGTH} karaktere): ")
    confirm = getpass("Konfirmo fjalëkalimin: ")

    if password != confirm:
        print("❌ Fjalëkalimet nuk përputhen.")
        return

    success, message = auth.register_user(username, password, role='admin')
    print(("✅ " if success else "❌ ") + message)


if __name__ == '__main__':
    main()
