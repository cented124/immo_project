import argparse, getpass
from sqlalchemy import select
from .db import Session, User, LoginSession, Audit
from sqlalchemy import delete
from .security import hasher
from .main import initialize


def reset_admin_password(email, password):
    """Requires shell access to this installation; no public recovery endpoint."""
    if not 12 <= len(password) <= 200:
        raise ValueError("Das Passwort muss 12 bis 200 Zeichen enthalten")
    with Session() as db:
        row = db.scalar(select(User).where(User.email == email.lower(), User.role == "admin", User.active == True))
        if not row:
            raise ValueError("Kein aktiver Administrator mit dieser E-Mail vorhanden")
        row.password = hasher.hash(password)
        db.execute(delete(LoginSession).where(LoginSession.user_id == row.id))
        db.add(Audit(actor=row.email, action="Administratorpasswort lokal wiederhergestellt; Sitzungen beendet"))
        db.commit()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command", choices=["create-admin", "admin-exists", "import-project", "reset-admin-password"]
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
    if args.command == "reset-admin-password" and not args.email:
        args.email = input("E-Mail des vorhandenen Administrators: ").strip()
    if not args.email:
        parser.error("--email ist für create-admin erforderlich")
    from pydantic import TypeAdapter, EmailStr

    email = str(TypeAdapter(EmailStr).validate_python(args.email)).lower()
    password = getpass.getpass("Neues Passwort (mindestens 12 Zeichen): ")
    if not 12 <= len(password) <= 200:
        raise SystemExit("Passwort muss 12 bis 200 Zeichen enthalten")
    if password != getpass.getpass("Passwort wiederholen: "):
        raise SystemExit("Passwörter stimmen nicht überein")
    initialize()
    if args.command == "reset-admin-password":
        try:
            reset_admin_password(email, password)
        except ValueError as error:
            raise SystemExit(str(error))
        print("Passwort wiederhergestellt. Bitte STARTEN.cmd oeffnen und neu anmelden.")
        return
    with Session() as db:
        if db.scalar(select(User).where(User.email == email)):
            raise SystemExit("Benutzer existiert bereits")
        db.add(User(email=email, password=hasher.hash(password), role="admin"))
        db.commit()
    print("Administrator angelegt. Anmeldung unter /admin.")


if __name__ == "__main__":
    main()
