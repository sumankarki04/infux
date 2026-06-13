from app import db
from app.models.user import User
from app.models.influencer import Influencer
from app.models.brand import Brand
from app.models.campaign import Campaign
from datetime import date, timedelta


def seed_data():
    if User.query.count() > 0:
        return

    # Admin
    admin = User(email='admin@infux.com', user_type='admin',
                 first_name='Admin', last_name='INFUX', city='Kathmandu')
    admin.set_password('admin123')
    db.session.add(admin)

    # Sample influencers
    influencer_data = [
        ('Suman', 'Karki',     'suman@infux.com',   'Tech',        120000, 15000, 0,     8000,  7.8),
        ('Priya', 'Shrestha',  'priya@infux.com',   'Fashion',     85000,  45000, 0,     12000, 9.2),
        ('Rohan', 'Thapa',     'rohan@infux.com',   'Food',        60000,  90000, 5000,  20000, 11.4),
        ('Anisha','Maharjan',  'anisha@infux.com',  'Travel',      200000, 30000, 8000,  15000, 5.6),
        ('Bikash','Rai',       'bikash@infux.com',  'Fitness',     40000,  110000,3000,  9000,  14.1),
        ('Nisha', 'Tamang',    'nisha@infux.com',   'Beauty',      95000,  75000, 0,     30000, 8.9),
    ]
    for fn, ln, em, niche, ig, tt, yt, fb, er in influencer_data:
        u = User(email=em, user_type='influencer', first_name=fn, last_name=ln, city='Kathmandu')
        u.set_password('pass123')
        db.session.add(u)
        db.session.flush()
        inf = Influencer(user_id=u.user_id, niche=niche,
                         instagram_handle=f'@{fn.lower()}_{niche.lower()}',
                         tiktok_handle=f'@{fn.lower()}tt',
                         instagram_followers=ig, tiktok_followers=tt,
                         youtube_subscribers=yt, facebook_followers=fb,
                         engagement_rate=er, verification_status='verified',
                         bio=f'{niche} content creator based in Nepal. Creating authentic content since 2020.',
                         creator_score=round(er * 0.4 + (ig + tt) / 100000 * 0.6, 1))
        db.session.add(inf)

    # Sample brands
    brand_data = [
        ('Maya Store',      'retail@maya.com',    'Retail',      'Leading Nepali fashion brand'),
        ('TechNep',         'hello@technep.com',  'Technology',  'Nepal\'s top tech gadget store'),
        ('YetiDrinks',      'info@yeti.com',      'F&B',         'Premium Himalayan beverages'),
        ('KathFoods',       'brands@kath.com',    'Food',        'Authentic Newari food brand'),
    ]
    for cname, em, industry, desc in brand_data:
        u = User(email=em, user_type='brand',
                 first_name=cname.split()[0], last_name='Team', city='Kathmandu')
        u.set_password('pass123')
        db.session.add(u)
        db.session.flush()
        br = Brand(user_id=u.user_id, company_name=cname,
                   industry=industry, description=desc, is_verified=True)
        db.session.add(br)
        db.session.flush()

        # Add sample campaign per brand
        c = Campaign(brand_id=br.brand_id,
                     title=f'{cname} Brand Awareness Campaign',
                     description=f'We are looking for authentic creators to promote {cname} on social media.',
                     platform='instagram',
                     niche=industry,
                     budget=25000,
                     deliverables='3 Instagram posts, 2 Stories, 1 Reel',
                     deadline=date.today() + timedelta(days=30),
                     min_followers=10000,
                     max_followers=500000,
                     location='Nepal',
                     status='open')
        db.session.add(c)

    db.session.commit()
