import argparse, getpass
from sqlalchemy import select
from .db import Session, User
from .security import hasher
from .main import initialize


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command", choices=["create-admin", "admin-exists", "import-project"]
    )
    parser.add_argument("--email")
    parser.add_argument("--path", default="/seed/project.json")
    args = parser.parse_args()
    if args.command == "import-project":
        from .project import import_project

        try:
            changed = import_project(args.path)
        except (ValueError, OSError):
            raise SystemExit(
                "Projektimport abgebrochen: Projekt/Medien ungültig oder Ziel nicht leer. Vorhandene Daten bleiben erhalten."
            )
        print(
            "Projekt importiert."
            if changed
            else "Kein neuer Projektimport erforderlich."
        )
        return
    if args.command == "admin-exists":
        initialize()
        with Session() as db:
            exists = db.scalar(
                select(User.id)
                .where(User.role == "admin", User.active == True)
                .limit(1)
            )
        raise SystemExit(0 if exists else 10)
    if not args.email:
        parser.error("--email ist für create-admin erforderlich")
    from pydantic import TypeAdapter, EmailStr

    email = str(TypeAdapter(EmailStr).validate_python(args.email)).lower()
    password = getpass.getpass("Neues Passwort (mindestens 12 Zeichen): ")
    if len(password) < 12:
        raise SystemExit("Passwort zu kurz")
    if password != getpass.getpass("Passwort wiederholen: "):
        raise SystemExit("Passwörter stimmen nicht überein")
    initialize()
    with Session() as db:
        if db.scalar(select(User).where(User.email == email)):
            raise SystemExit("Benutzer existiert bereits")
        db.add(User(email=email, password=hasher.hash(password), role="admin"))
        db.commit()
    print("Administrator angelegt. Anmeldung unter /admin.")


if __name__ == "__main__":
    main()
