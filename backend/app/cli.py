import argparse
from getpass import getpass

from app.auth import Role, provision_user
from app.database import initialize_database


def main() -> None:
    parser = argparse.ArgumentParser(description="Provision a FloodSense account.")
    parser.add_argument("--email", required=True, help="Account email")
    parser.add_argument("--role", required=True, choices=[role.value for role in Role])
    args = parser.parse_args()

    password = getpass("Account password (minimum 12 characters): ")
    confirmation = getpass("Confirm account password: ")
    if password != confirmation:
        parser.error("Passwords do not match.")
    initialize_database()
    user = provision_user(
        email=args.email,
        password=password,
        role=Role(args.role),
        actor=None,
    )
    print(f"Created {user.email} with role {user.role.value}.")


if __name__ == "__main__":
    main()
