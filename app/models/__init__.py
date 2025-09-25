# Importar todos los modelos para que estén disponibles
from .user import User
from .blog import BlogPost
from .course import Course
from .project import Project
from .site_config import SiteConfig
from .contact import ContactMessage

__all__ = ['User', 'BlogPost', 'Course', 'Project', 'SiteConfig', 'ContactMessage']
