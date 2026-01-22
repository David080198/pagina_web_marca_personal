"""
Blueprint de Lecciones de Cursos - CODEXSOTO
=============================================
Sistema de lecciones con progreso y contenido multimedia
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import login_required, current_user
from app.extensions import db
from app.models.lesson import CourseSection, Lesson, LessonProgress, LessonType
from app.models.course import Course
from app.models.enrollment import CourseEnrollment, EnrollmentStatus
from app.models.certificate import Certificate
from functools import wraps

lessons_bp = Blueprint('lessons', __name__)


def enrollment_required(f):
    """Decorador que requiere inscripción activa al curso"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        course_slug = kwargs.get('course_slug')
        
        if not course_slug:
            abort(404)
        
        course = Course.query.filter_by(slug=course_slug).first_or_404()
        
        if not current_user.is_authenticated:
            flash('Debes iniciar sesión para acceder al contenido del curso.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        
        # Admin siempre tiene acceso
        if current_user.is_admin:
            kwargs['course'] = course
            kwargs['enrollment'] = None
            return f(*args, **kwargs)
        
        # Verificar inscripción
        enrollment = CourseEnrollment.query.filter_by(
            user_id=current_user.id,
            course_id=course.id
        ).first()
        
        if not enrollment or not enrollment.can_access_course():
            flash('Necesitas inscribirte en este curso para acceder al contenido.', 'warning')
            return redirect(url_for('main.course_detail', slug=course_slug))
        
        kwargs['course'] = course
        kwargs['enrollment'] = enrollment
        return f(*args, **kwargs)
    return decorated_function


@lessons_bp.route('/course/<course_slug>/learn')
@login_required
@enrollment_required
def course_player(course_slug, course, enrollment):
    """Vista principal del reproductor de curso"""
    # Obtener estructura del curso
    sections = CourseSection.query.filter_by(
        course_id=course.id,
        is_published=True
    ).order_by(CourseSection.order).all()
    
    # Obtener progreso del usuario
    user_progress = {}
    if enrollment:
        progress_records = LessonProgress.query.filter_by(
            enrollment_id=enrollment.id
        ).all()
        user_progress = {p.lesson_id: p for p in progress_records}
    
    # Encontrar la siguiente lección a ver
    next_lesson = None
    for section in sections:
        for lesson in section.lessons:
            if lesson.is_published:
                progress = user_progress.get(lesson.id)
                if not progress or not progress.is_completed:
                    next_lesson = lesson
                    break
        if next_lesson:
            break
    
    # Si no hay siguiente, usar la primera
    if not next_lesson and sections and sections[0].lessons:
        next_lesson = sections[0].lessons[0]
    
    return render_template('lessons/course_player.html',
                          course=course,
                          sections=sections,
                          enrollment=enrollment,
                          user_progress=user_progress,
                          current_lesson=next_lesson)


@lessons_bp.route('/course/<course_slug>/lesson/<lesson_slug>')
@login_required
@enrollment_required
def lesson_view(course_slug, lesson_slug, course, enrollment):
    """Vista de una lección específica"""
    lesson = Lesson.query.filter_by(
        course_id=course.id,
        slug=lesson_slug,
        is_published=True
    ).first_or_404()
    
    # Verificar si es preview o requiere inscripción
    if not lesson.is_preview and not lesson.can_access(current_user, enrollment):
        flash('No tienes acceso a esta lección.', 'warning')
        return redirect(url_for('main.course_detail', slug=course_slug))
    
    # Obtener o crear progreso
    progress = LessonProgress.get_or_create(
        user_id=current_user.id,
        lesson_id=lesson.id,
        enrollment_id=enrollment.id if enrollment else None
    )
    
    # Actualizar último acceso
    progress.last_accessed_at = db.func.now()
    db.session.commit()
    
    # Obtener estructura del curso para sidebar
    sections = CourseSection.query.filter_by(
        course_id=course.id,
        is_published=True
    ).order_by(CourseSection.order).all()
    
    # Progreso de todas las lecciones
    user_progress = {}
    if enrollment:
        progress_records = LessonProgress.query.filter_by(
            enrollment_id=enrollment.id
        ).all()
        user_progress = {p.lesson_id: p for p in progress_records}
    
    # Lección anterior y siguiente
    all_lessons = Lesson.query.filter_by(
        course_id=course.id,
        is_published=True
    ).order_by(Lesson.section_id, Lesson.order).all()
    
    current_index = next((i for i, l in enumerate(all_lessons) if l.id == lesson.id), 0)
    prev_lesson = all_lessons[current_index - 1] if current_index > 0 else None
    next_lesson = all_lessons[current_index + 1] if current_index < len(all_lessons) - 1 else None
    
    return render_template('lessons/lesson_view.html',
                          course=course,
                          lesson=lesson,
                          sections=sections,
                          enrollment=enrollment,
                          progress=progress,
                          user_progress=user_progress,
                          prev_lesson=prev_lesson,
                          next_lesson=next_lesson)


@lessons_bp.route('/course/<course_slug>/lesson/<lesson_slug>/complete', methods=['POST'])
@login_required
@enrollment_required
def complete_lesson(course_slug, lesson_slug, course, enrollment):
    """Marcar lección como completada"""
    lesson = Lesson.query.filter_by(
        course_id=course.id,
        slug=lesson_slug
    ).first_or_404()
    
    progress = LessonProgress.get_or_create(
        user_id=current_user.id,
        lesson_id=lesson.id,
        enrollment_id=enrollment.id if enrollment else None
    )
    
    progress.complete()
    
    # Verificar si completó el curso
    if enrollment and enrollment.progress_percentage >= 100:
        # Emitir certificado automáticamente
        certificate = Certificate.issue_for_enrollment(enrollment)
        if certificate:
            flash('¡Felicitaciones! Has completado el curso. Tu certificado está disponible.', 'success')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True,
            'course_progress': enrollment.progress_percentage if enrollment else 100,
            'completed': True
        })
    
    flash('Lección completada', 'success')
    return redirect(url_for('lessons.lesson_view', course_slug=course_slug, lesson_slug=lesson_slug))


@lessons_bp.route('/course/<course_slug>/lesson/<lesson_slug>/progress', methods=['POST'])
@login_required
@enrollment_required
def update_progress(course_slug, lesson_slug, course, enrollment):
    """Actualizar progreso de video/lección"""
    lesson = Lesson.query.filter_by(
        course_id=course.id,
        slug=lesson_slug
    ).first_or_404()
    
    data = request.get_json()
    
    progress = LessonProgress.get_or_create(
        user_id=current_user.id,
        lesson_id=lesson.id,
        enrollment_id=enrollment.id if enrollment else None
    )
    
    # Actualizar según tipo de progreso
    if 'video_position' in data:
        progress.update_video_progress(
            position=data['video_position'],
            duration=data.get('video_duration')
        )
    
    if 'time_spent' in data:
        progress.add_time_spent(data['time_spent'])
    
    return jsonify({
        'success': True,
        'progress': progress.progress_percent,
        'is_completed': progress.is_completed
    })


@lessons_bp.route('/course/<course_slug>/lesson/<lesson_slug>/quiz/submit', methods=['POST'])
@login_required
@enrollment_required
def submit_quiz(course_slug, lesson_slug, course, enrollment):
    """Enviar respuestas de quiz"""
    lesson = Lesson.query.filter_by(
        course_id=course.id,
        slug=lesson_slug,
        lesson_type=LessonType.QUIZ
    ).first_or_404()
    
    data = request.get_json()
    answers = data.get('answers', {})
    
    # Calcular puntuación
    import json
    quiz_data = json.loads(lesson.quiz_data or '{"questions": []}')
    correct = 0
    total = len(quiz_data.get('questions', []))
    
    for i, question in enumerate(quiz_data.get('questions', [])):
        if str(i) in answers and answers[str(i)] == question.get('correct'):
            correct += 1
    
    score = (correct / total * 100) if total > 0 else 0
    
    # Registrar intento
    progress = LessonProgress.get_or_create(
        user_id=current_user.id,
        lesson_id=lesson.id,
        enrollment_id=enrollment.id if enrollment else None
    )
    
    progress.submit_quiz(answers, score)
    
    return jsonify({
        'success': True,
        'score': score,
        'correct': correct,
        'total': total,
        'passed': score >= lesson.passing_score,
        'passing_score': lesson.passing_score
    })


@lessons_bp.route('/course/<course_slug>/lesson/<lesson_slug>/notes', methods=['GET', 'POST'])
@login_required
@enrollment_required
def lesson_notes(course_slug, lesson_slug, course, enrollment):
    """Guardar/obtener notas de la lección"""
    lesson = Lesson.query.filter_by(
        course_id=course.id,
        slug=lesson_slug
    ).first_or_404()
    
    progress = LessonProgress.get_or_create(
        user_id=current_user.id,
        lesson_id=lesson.id,
        enrollment_id=enrollment.id if enrollment else None
    )
    
    if request.method == 'POST':
        data = request.get_json()
        progress.notes = data.get('notes', '')
        db.session.commit()
        
        return jsonify({'success': True})
    
    return jsonify({
        'notes': progress.notes or ''
    })


# ========== API Endpoints ==========

@lessons_bp.route('/api/course/<course_slug>/curriculum')
def api_curriculum(course_slug):
    """API: Obtener estructura del curso"""
    course = Course.query.filter_by(slug=course_slug, published=True).first_or_404()
    
    sections = CourseSection.query.filter_by(
        course_id=course.id,
        is_published=True
    ).order_by(CourseSection.order).all()
    
    curriculum = []
    for section in sections:
        section_data = section.to_dict(include_lessons=False)
        section_data['lessons'] = []
        
        for lesson in section.lessons:
            if lesson.is_published:
                lesson_data = lesson.to_dict()
                # Solo incluir contenido si es preview
                if lesson.is_preview:
                    lesson_data['content'] = lesson.content
                    lesson_data['video_embed_url'] = lesson.get_video_embed_url()
                curriculum_lesson = lesson_data
                section_data['lessons'].append(curriculum_lesson)
        
        curriculum.append(section_data)
    
    return jsonify({
        'course': {
            'id': course.id,
            'title': course.title,
            'slug': course.slug
        },
        'curriculum': curriculum,
        'total_lessons': sum(len(s['lessons']) for s in curriculum),
        'total_duration': sum(s['duration'] for s in curriculum)
    })


@lessons_bp.route('/api/course/<course_slug>/progress')
@login_required
def api_course_progress(course_slug):
    """API: Obtener progreso del usuario en el curso"""
    course = Course.query.filter_by(slug=course_slug).first_or_404()
    
    enrollment = CourseEnrollment.query.filter_by(
        user_id=current_user.id,
        course_id=course.id
    ).first()
    
    if not enrollment:
        return jsonify({
            'enrolled': False,
            'progress': 0,
            'completed_lessons': []
        })
    
    progress_records = LessonProgress.query.filter_by(
        enrollment_id=enrollment.id
    ).all()
    
    return jsonify({
        'enrolled': True,
        'enrollment_status': enrollment.status.value,
        'can_access': enrollment.can_access_course(),
        'progress': enrollment.progress_percentage,
        'completed_lessons': [p.lesson_id for p in progress_records if p.is_completed],
        'lessons_progress': [p.to_dict() for p in progress_records]
    })
