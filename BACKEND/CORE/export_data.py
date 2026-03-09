import json
from database import SessionLocal
from models import Profile, Cookie
from sqlalchemy.orm import joinedload

def export_data():
    print("📤 Starting data export...")
    db = SessionLocal()
    try:
        # Fetch all profiles with their cookies
        profiles = db.query(Profile).options(joinedload(Profile.cookies)).all()
        
        export_list = []
        for p in profiles:
            p_data = {
                "profile_number": p.profile_number,
                "profile_name": p.profile_name,
                "extraction_time": p.extraction_time.isoformat() if p.extraction_time else None,
                "last_used": p.last_used.isoformat() if p.last_used else None,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "cookies": []
            }
            
            for c in p.cookies:
                p_data["cookies"].append({
                    "cookies_json": c.cookies,
                    "created_at": c.created_at.isoformat() if c.created_at else None,
                    "updated_at": c.updated_at.isoformat() if c.updated_at else None
                })
            
            export_list.append(p_data)
            
        with open("backup_data.json", "w") as f:
            json.dump(export_list, f, indent=4)
            
        print(f"✅ Exported {len(export_list)} profiles to backup_data.json")
        
    except Exception as e:
        print(f"❌ Export failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    export_data()
