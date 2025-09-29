from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from datetime import datetime

from app.extensions import db
from app.models.user import User
from app.models.course import Course
from app.models.enrollment import CourseEnrollment, Payment, PaymentMethod, EnrollmentStatus, PaymentStatus
from app.forms.enrollment_forms import CourseEnrollmentForm, PaymentForm
from app.utils.file_upload import save_uploaded_file

enrollment_bp = Blueprint('enrollment', __name__, url_prefix='/enrollment')

@enrollment_bp.route('/enroll/<int:course_id>', methods=['GET', 'POST'])
@login_required
def enroll_course(course_id):
    """Inscribirse a un curso"""
    # Verificar que el curso existe
    course = Course.query.filter_by(id=course_id, published=True).first_or_404()
    
    # Verificar si ya está inscrito
    existing_enrollment = CourseEnrollment.query.filter_by(
        user_id=current_user.id,
        course_id=course_id
    ).first()
    
    if existing_enrollment:
        if existing_enrollment.status == EnrollmentStatus.ACTIVE:
            flash('Ya estás inscrito en este curso', 'info')
            return redirect(url_for('main.course_detail', slug=course.slug))
        elif existing_enrollment.status == EnrollmentStatus.PENDING_PAYMENT:
            flash('Tienes una inscripción pendiente de pago', 'warning')
            return redirect(url_for('enrollment.my_enrollments'))
    
    form = CourseEnrollmentForm()
    
    # Set the course_id in the form for both GET and POST requests
    if request.method == 'GET':
        form.course_id.data = course_id
    
    print(f"DEBUG: Request method: {request.method}")
    print(f"DEBUG: Form data: {request.form}")
    print(f"DEBUG: Form course_id: {form.course_id.data}")
    print(f"DEBUG: Form errors: {form.errors}")
    print(f"DEBUG: Form validate: {form.validate_on_submit()}")
    
    if form.validate_on_submit():
        try:
            # Crear nueva inscripción con estado "Validando Pago" ya que se está enviando comprobante
            enrollment = CourseEnrollment(
                user_id=current_user.id,
                course_id=course_id,
                phone=form.phone.data,
                student_notes=form.student_notes.data,
                enrolled_price=course.price,
                status=EnrollmentStatus.PAYMENT_PENDING_APPROVAL
            )
            
            db.session.add(enrollment)
            db.session.flush()  # Para obtener el ID sin hacer commit
            
            # Guardar el comprobante de pago
            receipt_filename = None
            if form.payment_receipt.data:
                # Crear directorio si no existe
                upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'payment_receipts')
                os.makedirs(upload_dir, exist_ok=True)
                
                # Generar nombre único para el archivo
                filename = secure_filename(form.payment_receipt.data.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                receipt_filename = f"receipt_{enrollment.id}_{timestamp}_{filename}"
                
                # Guardar archivo
                file_path = os.path.join(upload_dir, receipt_filename)
                form.payment_receipt.data.save(file_path)
            
            # Crear registro de pago
            payment = Payment(
                enrollment_id=enrollment.id,
                amount=course.price,
                currency='MXN',
                payment_method=PaymentMethod.BANK_TRANSFER,
                status=PaymentStatus.PENDING_APPROVAL,
                proof_of_payment_path=receipt_filename,
                transaction_reference=form.transfer_reference.data,
                bank_account_used=form.bank_account_used.data,
                payment_notes=f"Emisor: {form.transfer_sender_name.data}, Monto: {form.transfer_amount.data}",
                submitted_at=datetime.utcnow()
            )
            
            db.session.add(payment)
            db.session.commit()
            
            flash('¡Inscripción enviada correctamente! Tu comprobante de transferencia está siendo revisado y te notificaremos cuando sea aprobado.', 'success')
            return redirect(url_for('enrollment.my_enrollments'))
            
        except Exception as e:
            db.session.rollback()
            print(f"Error processing enrollment: {e}")
            flash('Hubo un error al procesar tu inscripción. Por favor intenta de nuevo.', 'error')
            return redirect(url_for('enrollment.enroll_course', course_id=course_id))
    
    return render_template('enrollment/enroll.html', 
                         course=course, 
                         form=form)

@enrollment_bp.route('/payment-instructions/<int:enrollment_id>', methods=['GET', 'POST'])
@login_required
def payment_instructions(enrollment_id):
    """Mostrar instrucciones de pago y procesar comprobante de transferencia bancaria"""
    enrollment = CourseEnrollment.query.filter_by(
        id=enrollment_id,
        user_id=current_user.id
    ).first_or_404()
    
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            sender_name = request.form.get('sender_name', '').strip()
            transfer_reference = request.form.get('transfer_reference', '').strip()
            bank_used = request.form.get('bank_used', '').strip()
            transfer_amount = request.form.get('transfer_amount', '').strip()
            transfer_date = request.form.get('transfer_date', '').strip()
            transfer_time = request.form.get('transfer_time', '').strip()
            additional_comments = request.form.get('additional_comments', '').strip()
            
            # Validar campos obligatorios
            if not all([sender_name, transfer_reference, bank_used, transfer_amount, transfer_date]):
                flash('Por favor completa todos los campos obligatorios', 'error')
                return render_template('enrollment/payment_instructions.html', enrollment=enrollment)
            
            # Validar archivo
            if 'payment_receipt' not in request.files:
                flash('Por favor selecciona un comprobante de pago', 'error')
                return render_template('enrollment/payment_instructions.html', enrollment=enrollment)
            
            file = request.files['payment_receipt']
            if file.filename == '':
                flash('Por favor selecciona un comprobante de pago', 'error')
                return render_template('enrollment/payment_instructions.html', enrollment=enrollment)
            
            # Validar tipo de archivo
            allowed_extensions = {'png', 'jpg', 'jpeg', 'pdf'}
            if not ('.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
                flash('Formato de archivo no válido. Solo se permiten: PNG, JPG, JPEG, PDF', 'error')
                return render_template('enrollment/payment_instructions.html', enrollment=enrollment)
            
            # Guardar archivo
            filename = secure_filename(f"comprobante_{enrollment_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file.filename.rsplit('.', 1)[1].lower()}")
            
            # Crear directorio si no existe
            upload_dir = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), 'comprobantes')
            os.makedirs(upload_dir, exist_ok=True)
            
            file_path = os.path.join(upload_dir, filename)
            file.save(file_path)
            
            # Actualizar el pago existente o crear uno nuevo
            payment = Payment.query.filter_by(enrollment_id=enrollment_id).first()
            
            if payment:
                # Actualizar pago existente
                payment.transfer_sender_name = sender_name
                payment.transfer_reference = transfer_reference
                payment.bank_account_used = bank_used
                payment.transfer_amount = float(transfer_amount)
                payment.payment_receipt_path = file_path
                payment.additional_notes = f"Fecha: {transfer_date} {transfer_time}. {additional_comments}"
                payment.status = PaymentStatus.PENDING_APPROVAL
                payment.updated_at = datetime.utcnow()
            else:
                # Crear nuevo pago
                payment = Payment(
                    enrollment_id=enrollment_id,
                    amount=float(transfer_amount),
                    payment_method=PaymentMethod.BANK_TRANSFER,
                    transfer_sender_name=sender_name,
                    transfer_reference=transfer_reference,
                    bank_account_used=bank_used,
                    transfer_amount=float(transfer_amount),
                    payment_receipt_path=file_path,
                    additional_notes=f"Fecha: {transfer_date} {transfer_time}. {additional_comments}",
                    status=PaymentStatus.PENDING_APPROVAL
                )
                db.session.add(payment)
            
            # Actualizar estado de inscripción a "Validando Pago"
            enrollment.status = EnrollmentStatus.PAYMENT_PENDING_APPROVAL
            
            db.session.commit()
            
            flash('¡Comprobante enviado exitosamente! Te notificaremos cuando sea aprobado.', 'success')
            return redirect(url_for('enrollment.my_enrollments'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error al procesar comprobante: {str(e)}")
            flash('Error al procesar el comprobante. Por favor intenta de nuevo.', 'error')
    
    return render_template('enrollment/payment_instructions.html',
                         enrollment=enrollment)

@enrollment_bp.route('/submit-payment/<int:enrollment_id>', methods=['GET', 'POST'])
@login_required
def submit_payment(enrollment_id):
    """Enviar comprobante de pago"""
    enrollment = CourseEnrollment.query.filter_by(
        id=enrollment_id,
        user_id=current_user.id
    ).first_or_404()
    
    if enrollment.status != EnrollmentStatus.PENDING_PAYMENT:
        flash('Esta inscripción no está disponible para pago', 'error')
        return redirect(url_for('user.dashboard'))
    
    form = PaymentForm()
    
    if form.validate_on_submit():
        # Guardar comprobante de pago si se subió
        proof_filename = None
        if form.proof_of_payment.data:
            proof_filename = save_uploaded_file(
                form.proof_of_payment.data,
                'payment_proofs'
            )
        
        # Crear registro de pago
        payment = Payment(
            enrollment_id=enrollment.id,
            payment_method=PaymentMethod(form.payment_method.data),
            transaction_reference=form.transaction_reference.data,
            bank_account_used=form.bank_account_used.data,
            proof_of_payment_path=proof_filename,
            payment_notes=form.payment_notes.data,
            status=PaymentStatus.PENDING_APPROVAL
        )
        
        db.session.add(payment)
        
        # Actualizar estado de inscripción
        enrollment.status = EnrollmentStatus.PAYMENT_PENDING_APPROVAL
        
        db.session.commit()
        
        flash('Comprobante de pago enviado correctamente. Será revisado en las próximas 24-48 horas.', 'success')
        return redirect(url_for('user.dashboard'))
    
    return render_template('enrollment/submit_payment.html',
                         enrollment=enrollment,
                         form=form)

@enrollment_bp.route('/my-enrollments')
@login_required
def my_enrollments():
    """Ver mis inscripciones"""
    enrollments = CourseEnrollment.query.filter_by(
        user_id=current_user.id
    ).order_by(CourseEnrollment.enrolled_at.desc()).all()
    
    return render_template('enrollment/my_enrollments.html',
                         enrollments=enrollments)

@enrollment_bp.route('/enrollment-status/<int:enrollment_id>')
@login_required
def enrollment_status(enrollment_id):
    """Ver estado detallado de una inscripción"""
    enrollment = CourseEnrollment.query.filter_by(
        id=enrollment_id,
        user_id=current_user.id
    ).first_or_404()
    
    return render_template('enrollment/enrollment_status.html',
                         enrollment=enrollment)

@enrollment_bp.route('/cancel-enrollment/<int:enrollment_id>', methods=['POST'])
@login_required
def cancel_enrollment(enrollment_id):
    """Cancelar inscripción (solo si está pendiente de pago)"""
    enrollment = CourseEnrollment.query.filter_by(
        id=enrollment_id,
        user_id=current_user.id
    ).first_or_404()
    
    if enrollment.status != EnrollmentStatus.PENDING_PAYMENT:
        flash('No se puede cancelar esta inscripción', 'error')
        return redirect(url_for('enrollment.my_enrollments'))
    
    db.session.delete(enrollment)
    db.session.commit()
    
    flash('Inscripción cancelada correctamente', 'success')
    return redirect(url_for('enrollment.my_enrollments'))

# API Endpoints para actualizaciones en tiempo real
@enrollment_bp.route('/api/enrollment-status/<int:enrollment_id>')
@login_required
def api_enrollment_status(enrollment_id):
    """API para obtener estado actual de inscripción"""
    enrollment = CourseEnrollment.query.filter_by(
        id=enrollment_id,
        user_id=current_user.id
    ).first_or_404()
    
    return jsonify({
        'status': enrollment.status.value,
        'status_display': enrollment.get_status_display(),
        'has_payment': enrollment.payment is not None,
        'payment_status': enrollment.payment.status.value if enrollment.payment else None,
        'last_updated': enrollment.updated_at.isoformat() if enrollment.updated_at else None
    })

@enrollment_bp.context_processor
def enrollment_context():
    """Procesador de contexto para templates de inscripción"""
    return {
        'EnrollmentStatus': EnrollmentStatus,
        'PaymentStatus': PaymentStatus,
        'PaymentMethod': PaymentMethod
    }

@enrollment_bp.route('/process-card-payment/<int:enrollment_id>', methods=['POST'])
@login_required
def process_card_payment(enrollment_id):
    """Procesar pago con tarjeta de crédito"""
    enrollment = CourseEnrollment.query.get_or_404(enrollment_id)
    
    if enrollment.user_id != current_user.id:
        flash('No tienes permisos para acceder a esta inscripción', 'error')
        return redirect(url_for('enrollment.my_enrollments'))
    
    # En un entorno real, aquí integrarías con un procesador de pagos como Stripe
    # Por ahora, simulamos el proceso
    try:
        # Crear registro de pago
        payment = Payment(
            enrollment_id=enrollment.id,
            amount=enrollment.enrolled_price,
            payment_method=PaymentMethod.CREDIT_CARD,
            status=PaymentStatus.APPROVED,  # En desarrollo, aprobamos automáticamente
            transaction_id=f"card_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            submitted_at=datetime.utcnow(),
            processed_at=datetime.utcnow()
        )
        
        db.session.add(payment)
        
        # Activar inscripción
        enrollment.activate()
        
        db.session.commit()
        
        flash('¡Pago procesado exitosamente! Ya tienes acceso al curso.', 'success')
        return redirect(url_for('enrollment.my_enrollments'))
        
    except Exception as e:
        db.session.rollback()
        flash('Error al procesar el pago. Inténtalo de nuevo.', 'error')
        return redirect(url_for('enrollment.my_enrollments'))

@enrollment_bp.route('/process-paypal/<int:enrollment_id>', methods=['POST'])
@login_required
def process_paypal_payment(enrollment_id):
    """Procesar pago con PayPal"""
    enrollment = CourseEnrollment.query.get_or_404(enrollment_id)
    
    if enrollment.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'No autorizado'}), 403
    
    data = request.get_json()
    
    try:
        # Crear registro de pago
        payment = Payment(
            enrollment_id=enrollment.id,
            amount=enrollment.enrolled_price,
            payment_method=PaymentMethod.PAYPAL,
            status=PaymentStatus.APPROVED,
            transaction_id=data.get('orderID'),
            payment_details=str(data),
            submitted_at=datetime.utcnow(),
            processed_at=datetime.utcnow()
        )
        
        db.session.add(payment)
        
        # Activar inscripción
        enrollment.activate()
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Pago procesado exitosamente'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@enrollment_bp.route('/process-mercadopago/<int:enrollment_id>', methods=['POST'])
@login_required
def process_mercadopago(enrollment_id):
    """Procesar pago con MercadoPago"""
    enrollment = CourseEnrollment.query.get_or_404(enrollment_id)
    
    if enrollment.user_id != current_user.id:
        flash('No tienes permisos para acceder a esta inscripción', 'error')
        return redirect(url_for('enrollment.my_enrollments'))
    
    # En un entorno real, aquí generarías un enlace de pago de MercadoPago
    # Por ahora, simulamos el proceso
    
    try:
        # Crear un pago pendiente para MercadoPago
        payment = Payment(
            enrollment_id=enrollment.id,
            amount=enrollment.enrolled_price,
            payment_method=PaymentMethod.CREDIT_CARD,  # MercadoPago maneja múltiples métodos
            status=PaymentStatus.PENDING_APPROVAL,
            transaction_id=f"mp_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            submitted_at=datetime.utcnow()
        )
        
        db.session.add(payment)
        db.session.commit()
        
        # En producción, redirigiría a MercadoPago
        flash('Serás redirigido a MercadoPago para completar el pago.', 'info')
        flash('Por ahora en modo desarrollo, el pago está pendiente de aprobación.', 'warning')
        
        return redirect(url_for('enrollment.my_enrollments'))
        
    except Exception as e:
        db.session.rollback()
        flash('Error al procesar el pago. Inténtalo de nuevo.', 'error')
        return redirect(url_for('enrollment.my_enrollments'))
