import os
from dotenv import load_dotenv
load_dotenv()
import psycopg2

url = os.environ['DATABASE_URL']
conn = psycopg2.connect(url, connect_timeout=10)
cur = conn.cursor()
cur.execute("""
    SELECT
        (SELECT COUNT(*) FROM influencers WHERE verification_status='verified') as v_inf,
        (SELECT COUNT(*) FROM brands WHERE is_verified=true) as v_brands,
        (SELECT COUNT(*) FROM campaigns) as campaigns,
        (SELECT COUNT(*) FROM users) as users,
        (SELECT COUNT(*) FROM notifications) as notifications
""")
row = cur.fetchone()
print(f"Verified influencers: {row[0]}")
print(f"Verified brands:      {row[1]}")
print(f"Campaigns:            {row[2]}")
print(f"Total users:          {row[3]}")
print(f"Notifications:        {row[4]}")
conn.close()
