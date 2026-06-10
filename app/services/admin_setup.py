import os
import sys
from datetime import UTC, datetime
from typing import Optional
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Add the project root to sys.path to allow importing 'app'
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.user import AccountStatus, User, UserRole
from app.services.supabase_client import get_supabase

def setup_admin_user():
    """
    Ensures an admin user exists in both Supabase Auth and the local database.
    """
    db = SessionLocal()
    supabase = get_supabase()

    # Get credentials from env
    admin_email = os.getenv("MM_MOTORS_ADMIN_EMAIL")
    admin_password = os.getenv("MM_MOTORS_ADMIN_PASSWORD")
    admin_name = os.getenv("MM_MOTORS_ADMIN_NAME", "MM Motors Admin")
    
    if not admin_email or not admin_password:
        print("Error: MM_MOTORS_ADMIN_EMAIL and MM_MOTORS_ADMIN_PASSWORD must be set in .env")
        return

    print(f"--- Admin Setup Process ---")
    print(f"Target Email: {admin_email}")

    try:
        # 1. Sync with Supabase Auth
        supabase_id = None
        try:
            # Check if user exists in Supabase
            # We list users using the admin API
            users_resp = supabase.auth.admin.list_users()
            existing_auth_user = next((u for u in users_resp if u.email == admin_email), None)
            
            if existing_auth_user:
                supabase_id = existing_auth_user.id
                print(f"Found existing Supabase user (ID: {supabase_id})")
                # Update role in metadata
                supabase.auth.admin.update_user_by_id(
                    supabase_id, 
                    {"user_metadata": {"name": admin_name, "role": "admin"}}
                )
                print("Updated Supabase metadata to role: admin")
            else:
                print("User not found in Supabase. Creating new Auth account...")
                new_auth_user = supabase.auth.admin.create_user({
                    "email": admin_email,
                    "password": admin_password,
                    "email_confirm": True,
                    "user_metadata": {"name": admin_name, "role": "admin"}
                })
                supabase_id = new_auth_user.user.id
                print(f"Created new Supabase user (ID: {supabase_id})")
                
        except Exception as e:
            print(f"Supabase Auth Error: {e}")
            return

        # 2. Sync with local Database
        existing_db_user = db.query(User).filter(User.email == admin_email).first()
        
        if existing_db_user:
            print(f"Found existing local record (ID: {existing_db_user.id})")
            # If ID changed (recreated in Supabase), we must update the record or recreate it
            if existing_db_user.id != supabase_id:
                print(f"Warning: ID mismatch. Local: {existing_db_user.id}, Supabase: {supabase_id}")
                print("Updating local record ID...")
                # SQLite/Postgres might not allow PK update easily, safer to delete and recreate
                db.delete(existing_db_user)
                db.commit()
                existing_db_user = None
            else:
                existing_db_user.role = UserRole.admin
                existing_db_user.name = admin_name
                existing_db_user.password_hash = hash_password(admin_password)
                existing_db_user.last_active = datetime.now(UTC)
                db.commit()
                print("Local record updated successfully.")

        if not existing_db_user:
            print("Creating new local user record...")
            new_user = User(
                id=supabase_id,
                name=admin_name,
                email=admin_email,
                phone="+92 300 0000000",
                role=UserRole.admin,
                status=AccountStatus.active,
                password_hash=hash_password(admin_password),
                address="Karachi, Pakistan",
                total_orders=0,
                total_paid=0,
                total_balance=0,
                registration_date=datetime.now(UTC),
                last_active=datetime.now(UTC),
            )
            db.add(new_user)
            db.commit()
            print("Local record created successfully.")

        print("---------------------------")
        print("Success: Admin user is now synced and set to 'admin' role.")

    finally:
        db.close()

if __name__ == "__main__":
    setup_admin_user()
