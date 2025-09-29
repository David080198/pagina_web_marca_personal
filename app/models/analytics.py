from app.extensions import db
from datetime import datetime
import json

class PageView(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(45))  # IPv6 puede ser hasta 45 caracteres
    user_agent = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Usuario autenticado
    page = db.Column(db.String(255), nullable=False)
    referrer = db.Column(db.String(500))
    country = db.Column(db.String(100))
    device = db.Column(db.String(50))  # mobile, desktop, tablet
    browser = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relación con User
    user = db.relationship('User', backref='page_views')
    
    def __repr__(self):
        return f'<PageView {self.page} from {self.ip_address}>'

class VisitorStats(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, unique=True)
    unique_visitors = db.Column(db.Integer, default=0)
    page_views = db.Column(db.Integer, default=0)
    bounce_rate = db.Column(db.Float, default=0.0)
    avg_session_duration = db.Column(db.Float, default=0.0)  # en segundos
    top_pages = db.Column(db.Text)  # JSON con las páginas más visitadas
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_top_pages(self):
        if self.top_pages:
            return json.loads(self.top_pages)
        return []
    
    def set_top_pages(self, pages_dict):
        self.top_pages = json.dumps(pages_dict)
    
    def __repr__(self):
        return f'<VisitorStats {self.date}: {self.unique_visitors} visitors>'
