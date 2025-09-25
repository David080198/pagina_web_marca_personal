from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_mail import Message
from app.models.blog import BlogPost
from app.models.course import Course
from app.models.project import Project
from app.models.site_config import SiteConfig
from app.models.contact import ContactMessage
from app.extensions import db, mail

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    config = SiteConfig.query.first()
    featured_projects = Project.query.filter_by(published=True, featured=True).limit(3).all()
    featured_courses = Course.query.filter_by(published=True, featured=True).limit(3).all()
    recent_posts = BlogPost.query.filter_by(published=True).order_by(BlogPost.created_at.desc()).limit(3).all()
    
    return render_template('index.html', 
                         config=config,
                         featured_projects=featured_projects,
                         featured_courses=featured_courses,
                         recent_posts=recent_posts)

@main_bp.route('/investigacion')
def research():
    config = SiteConfig.query.first()
    research_projects = Project.query.filter_by(published=True, category='research').all()
    
    return render_template('research.html', 
                         config=config,
                         projects=research_projects)

@main_bp.route('/automatizaciones')
def automation():
    config = SiteConfig.query.first()
    automation_projects = Project.query.filter_by(published=True, category='automation').all()
    
    return render_template('automation.html', 
                         config=config,
                         projects=automation_projects)

@main_bp.route('/cursos')
def courses():
    config = SiteConfig.query.first()
    all_courses = Course.query.filter_by(published=True).all()
    
    return render_template('courses.html', 
                         config=config,
                         courses=all_courses)

@main_bp.route('/curso/<slug>')
def course_detail(slug):
    config = SiteConfig.query.first()
    course = Course.query.filter_by(slug=slug, published=True).first_or_404()
    
    return render_template('course_detail.html', 
                         config=config,
                         course=course)

@main_bp.route('/blog')
def blog():
    config = SiteConfig.query.first()
    page = request.args.get('page', 1, type=int)
    posts = BlogPost.query.filter_by(published=True).order_by(BlogPost.created_at.desc()).paginate(
        page=page, per_page=6, error_out=False)
    
    return render_template('blog.html', 
                         config=config,
                         posts=posts)

@main_bp.route('/blog/<slug>')
def blog_post(slug):
    config = SiteConfig.query.first()
    post = BlogPost.query.filter_by(slug=slug, published=True).first_or_404()
    
    return render_template('blog_post.html', 
                         config=config,
                         post=post)

@main_bp.route('/contacto', methods=['GET', 'POST'])
def contact():
    config = SiteConfig.query.first()
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject', 'Contacto desde la web')
        message = request.form.get('message')
        
        # Guardar mensaje en la base de datos
        contact_message = ContactMessage(
            name=name,
            email=email,
            subject=subject,
            message=message
        )
        db.session.add(contact_message)
        db.session.commit()
        
        # Enviar email (opcional)
        try:
            msg = Message(
                subject=f'[CodexSoto] {subject}',
                recipients=[config.contact_email or 'admin@codexsoto.com'],
                body=f'Nombre: {name}\nEmail: {email}\n\nMensaje:\n{message}'
            )
            mail.send(msg)
        except Exception as e:
            print(f"Error enviando email: {e}")
        
        flash('Mensaje enviado correctamente. Te contactaré pronto.', 'success')
        return redirect(url_for('main.contact'))
    
    return render_template('contact.html', config=config)

@main_bp.route('/proyecto/<slug>')
def project_detail(slug):
    config = SiteConfig.query.first()
    project = Project.query.filter_by(slug=slug, published=True).first_or_404()
    
    return render_template('project_detail.html', 
                         config=config,
                         project=project)
