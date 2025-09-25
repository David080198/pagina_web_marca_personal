from app.extensions import db
from datetime import datetime

class SiteConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    site_name = db.Column(db.String(100), default='CodexSoto')
    site_description = db.Column(db.Text, default='Investigación en IA y Automatizaciones')
    primary_color = db.Column(db.String(7), default='#3b82f6')
    secondary_color = db.Column(db.String(7), default='#1e40af')
    dark_mode = db.Column(db.Boolean, default=False)
    hero_title = db.Column(db.String(200), default='David Soto')
    hero_subtitle = db.Column(db.String(500), default='Especialista en IA y Automatizaciones')
    about_text = db.Column(db.Text, default='Investigador especializado en inteligencia artificial.')
    contact_email = db.Column(db.String(120))
    linkedin_url = db.Column(db.String(255))
    github_url = db.Column(db.String(255))
    twitter_url = db.Column(db.String(255))
    youtube_url = db.Column(db.String(255))
    instagram_url = db.Column(db.String(255))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<SiteConfig {self.site_name}>'
