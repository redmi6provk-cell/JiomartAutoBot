import json
from database import SessionLocal
from models import Profile, Cookie
from datetime import datetime

def import_data():
    print("📥 Starting data import...")
    
    try:
        with open("backup_data.json", "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        print("❌ backup_data.json not found!")
        return

    db = SessionLocal()
    try:
        # Clear existing data if needed (Optional, but safer for re-run)
        # db.query(Cookie).delete()
        # db.query(Profile).delete()
        # db.commit()

        count = 0
        for p_item in data:
            # Check if profile already exists
            existing = db.query(Profile).filter(Profile.profile_number == p_item["profile_number"]).first()
            
            if not existing:
                new_profile = Profile(
                    profile_number=p_item["profile_number"],
                    profile_name=p_item["profile_name"],
                    extraction_time=datetime.fromisoformat(p_item["extraction_time"]) if p_item["extraction_time"] else None,
                    last_used=datetime.fromisoformat(p_item["last_used"]) if p_item["last_used"] else None,
                    created_at=datetime.fromisoformat(p_item["created_at"]) if p_item["created_at"] else None
                )
                db.add(new_profile)
                db.flush() # Get profile ID
                
                for c_item in p_item["cookies"]:
                    new_cookie = Cookie(
                        profile_id=new_profile.id,
                        cookies=c_item["cookies_json"],
                        created_at=datetime.fromisoformat(c_item["created_at"]) if c_item["created_at"] else None,
                        updated_at=datetime.fromisoformat(c_item["updated_at"]) if c_item["updated_at"] else None
                    )
                    db.add(new_cookie)
                
                count += 1
            else:
                # Update existing cookies if needed (Optional)
                print(f"⚠️ Profile {p_item['profile_number']} already exists, skipping.")

        db.commit()
        print(f"✅ Imported {count} new profiles successfully!")

    except Exception as e:
        print(f"❌ Import failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    import_data()
