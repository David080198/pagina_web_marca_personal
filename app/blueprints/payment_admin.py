from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models.enrollment import CourseEnrollment, Payment, PaymentStatus, EnrollmentStatus
from app.models.user import User
from app.forms.enrollment_forms import PaymentApprovalForm
from functools import wraps
from datetime import datetime

# Crear blueprint para administración de pagos
payment_admin_bp = Blueprint('payment_admin', __name__, url_prefix='/admin/payments')

def admin_required(f):
    """Decorador para verificar que el usuario sea admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Acceso denegado. Se requieren privilegios de administrador.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@payment_admin_bp.route('/')
@login_required
@admin_required
def payment_dashboard():
    """Dashboard principal de administración de pagos"""
    # Estadísticas de pagos
    pending_payments = Payment.query.filter_by(status=PaymentStatus.PENDING_APPROVAL).count()
    approved_payments = Payment.query.filter_by(status=PaymentStatus.APPROVED).count()
    rejected_payments = Payment.query.filter_by(status=PaymentStatus.REJECTED).count()
    
    # Pagos recientes pendientes de aprobación
    recent_pending = Payment.query.filter_by(
        status=PaymentStatus.PENDING_APPROVAL
    ).order_by(Payment.submitted_at.desc()).limit(10).all()
    
    # Inscripciones activas recientes
    recent_enrollments = CourseEnrollment.query.filter_by(
        status=EnrollmentStatus.ACTIVE
    ).order_by(CourseEnrollment.activated_at.desc()).limit(5).all()
    
    stats = {
        'pending_payments': pending_payments,
        'approved_payments': approved_payments,
        'rejected_payments': rejected_payments,
        'total_payments': pending_payments + approved_payments + rejected_payments
    }
    
    return render_template('admin/payments/dashboard.html',
                         stats=stats,
                         recent_pending=recent_pending,
                         recent_enrollments=recent_enrollments)

@payment_admin_bp.route('/pending')
@login_required
@admin_required
def pending_payments():
    """Lista de pagos pendientes de aprobación"""
    page = request.args.get('page', 1, type=int)
    
    payments = Payment.query.filter_by(
        status=PaymentStatus.PENDING_APPROVAL
    ).order_by(Payment.submitted_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    
    return render_template('admin/payments/pending.html', payments=payments)

@payment_admin_bp.route('/all')
@login_required
@admin_required
def all_payments():
    """Lista de todos los pagos"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')
    
    query = Payment.query
    
    if status_filter != 'all':
        try:
            status_enum = PaymentStatus(status_filter)
            query = query.filter_by(status=status_enum)
        except ValueError:
            pass  # Ignorar filtros inválidos
    
    payments = query.order_by(Payment.submitted_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/payments/all.html', 
                         payments=payments, 
                         status_filter=status_filter)

@payment_admin_bp.route('/review/<int:payment_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def review_payment(payment_id):
    """Revisar y aprobar/rechazar un pago"""
    payment = Payment.query.get_or_404(payment_id)
    
    if payment.status != PaymentStatus.PENDING_APPROVAL:
        flash('Este pago ya ha sido procesado', 'warning')
        return redirect(url_for('payment_admin.payment_dashboard'))
    
    form = PaymentApprovalForm()
    
    if form.validate_on_submit():
        if form.action.data == 'approve':
            # Aprobar pago
            payment.approve(current_user.id, form.admin_notes.data)
            flash(f'Pago aprobado correctamente. Inscripción activada.', 'success')
        elif form.action.data == 'reject':
            # Rechazar pago
            payment.reject(current_user.id, form.rejection_reason.data, form.admin_notes.data)
            flash(f'Pago rechazado. El usuario será notificado.', 'info')
        
        db.session.commit()
        return redirect(url_for('payment_admin.pending_payments'))
    
    return render_template('admin/payments/review.html', 
                         payment=payment, 
                         form=form)

@payment_admin_bp.route('/enrollments')
@login_required
@admin_required
def enrollments_overview():
    """Vista general de inscripciones"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')
    
    query = CourseEnrollment.query
    
    if status_filter != 'all':
        try:
            status_enum = EnrollmentStatus(status_filter)
            query = query.filter_by(status=status_enum)
        except ValueError:
            pass
    
    enrollments = query.order_by(CourseEnrollment.enrolled_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/payments/enrollments.html',
                         enrollments=enrollments,
                         status_filter=status_filter)

@payment_admin_bp.route('/statistics')
@login_required
@admin_required
def payment_statistics():
    """Estadísticas detalladas de pagos e inscripciones"""
    from sqlalchemy import func
    from datetime import datetime, timedelta
    
    # Estadísticas por mes (últimos 6 meses)
    six_months_ago = datetime.now() - timedelta(days=180)
    
    monthly_stats = db.session.query(
        func.date_trunc('month', Payment.submitted_at).label('month'),
        func.count(Payment.id).label('count'),
        Payment.status
    ).filter(
        Payment.submitted_at >= six_months_ago
    ).group_by(
        func.date_trunc('month', Payment.submitted_at),
        Payment.status
    ).all()
    
    # Estadísticas por método de pago
    payment_methods = db.session.query(
        Payment.payment_method,
        func.count(Payment.id).label('count')
    ).group_by(Payment.payment_method).all()
    
    # Cursos más populares
    popular_courses = db.session.query(
        CourseEnrollment.course_id,
        func.count(CourseEnrollment.id).label('enrollments')
    ).group_by(CourseEnrollment.course_id).order_by(
        func.count(CourseEnrollment.id).desc()
    ).limit(10).all()
    
    return render_template('admin/payments/statistics.html',
                         monthly_stats=monthly_stats,
                         payment_methods=payment_methods,
                         popular_courses=popular_courses)

# API Endpoints
@payment_admin_bp.route('/api/quick-approve/<int:payment_id>', methods=['POST'])
@login_required
@admin_required
def api_quick_approve(payment_id):
    """API para aprobación rápida de pago"""
    payment = Payment.query.get_or_404(payment_id)
    
    if payment.status != PaymentStatus.PENDING_APPROVAL:
        return jsonify({'success': False, 'message': 'Pago ya procesado'}), 400
    
    try:
        payment.approve(current_user.id, 'Aprobación rápida desde dashboard')
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Pago aprobado correctamente',
            'enrollment_status': payment.enrollment.status.value
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@payment_admin_bp.route('/api/payment-stats')
@login_required
@admin_required
def api_payment_stats():
    """API para obtener estadísticas en tiempo real"""
    stats = {
        'pending': Payment.query.filter_by(status=PaymentStatus.PENDING_APPROVAL).count(),
        'approved_today': Payment.query.filter(
            Payment.status == PaymentStatus.APPROVED,
            Payment.processed_at >= datetime.now().date()
        ).count(),
        'active_enrollments': CourseEnrollment.query.filter_by(status=EnrollmentStatus.ACTIVE).count()
    }
    
    return jsonify(stats)

@payment_admin_bp.route('/approve/<int:payment_id>', methods=['POST'])
@login_required
@admin_required
def approve_payment(payment_id):
    """API para aprobar un pago"""
    payment = Payment.query.get_or_404(payment_id)
    
    if payment.status != PaymentStatus.PENDING_APPROVAL:
        return jsonify({'success': False, 'message': 'Pago ya procesado'}), 400
    
    try:
        payment.approve(current_user.id, 'Aprobado desde lista de pagos')
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Pago aprobado correctamente'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@payment_admin_bp.route('/reject/<int:payment_id>', methods=['POST'])
@login_required
@admin_required
def reject_payment(payment_id):
    """API para rechazar un pago"""
    payment = Payment.query.get_or_404(payment_id)
    
    if payment.status != PaymentStatus.PENDING_APPROVAL:
        return jsonify({'success': False, 'message': 'Pago ya procesado'}), 400
    
    data = request.get_json()
    reason = data.get('reason', 'Sin especificar') if data else 'Sin especificar'
    
    try:
        payment.reject(current_user.id, reason)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Pago rechazado correctamente'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
