# Importar todos los modelos para que estén disponibles
from .user import User
from .blog import BlogPost
from .course import Course
from .project import Project
from .site_config import SiteConfig
from .contact import ContactMessage
from .analytics import PageView, VisitorStats
from .enrollment import CourseEnrollment, Payment, EnrollmentStatus, PaymentStatus, PaymentMethod
from .comment import Comment
from .favorite import Favorite
from .like import Like

# Nuevos modelos - CODEXSOTO Platform
from .subscription import Subscription, SubscriptionPayment, SubscriptionPlan, SubscriptionStatus
from .article import Article, ArticleCategory, ArticleLike, ArticleDifficulty
from .newsletter import NewsletterSubscriber, NewsletterCampaign, NewsletterSend
from .lesson import CourseSection, Lesson, LessonProgress, LessonType
from .certificate import Certificate, CertificateTemplate

__all__ = [
    # Modelos base
    'User',
    'BlogPost',
    'Course',
    'Project',
    'SiteConfig',
    'ContactMessage',
    'PageView',
    'VisitorStats',
    'CourseEnrollment',
    'Payment',
    'Comment',
    'Favorite',
    'Like',
    
    # Enums de enrollment
    'EnrollmentStatus',
    'PaymentStatus',
    'PaymentMethod',
    
    # Suscripciones
    'Subscription',
    'SubscriptionPayment',
    'SubscriptionPlan',
    'SubscriptionStatus',
    
    # Artículos técnicos
    'Article',
    'ArticleCategory',
    'ArticleLike',
    'ArticleDifficulty',
    
    # Newsletter
    'NewsletterSubscriber',
    'NewsletterCampaign',
    'NewsletterSend',
    
    # Lecciones
    'CourseSection',
    'Lesson',
    'LessonProgress',
    'LessonType',
    
    # Certificados
    'Certificate',
    'CertificateTemplate',
]
