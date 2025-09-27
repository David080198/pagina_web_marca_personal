import os
import uuid
from werkzeug.utils import secure_filename
from PIL import Image
import io
from flask import current_app

# Configuración de archivos permitidos
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def allowed_file(filename):
    """Verifica si el archivo tiene una extensión permitida"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_unique_filename(filename):
    """Genera un nombre de archivo único"""
    ext = filename.rsplit('.', 1)[1].lower()
    unique_filename = f"{uuid.uuid4().hex}.{ext}"
    return unique_filename

def optimize_image(image_file, max_width=1200, quality=85):
    """Optimiza la imagen redimensionándola y comprimiéndola"""
    try:
        # Abrir la imagen
        image = Image.open(image_file)
        
        # Convertir a RGB si es necesario (para archivos RGBA o P)
        if image.mode in ('RGBA', 'P'):
            image = image.convert('RGB')
        
        # Redimensionar si es muy grande
        if image.width > max_width:
            ratio = max_width / image.width
            new_height = int(image.height * ratio)
            image = image.resize((max_width, new_height), Image.Resampling.LANCZOS)
        
        # Guardar la imagen optimizada en memoria
        output = io.BytesIO()
        image.save(output, format='JPEG', quality=quality, optimize=True)
        output.seek(0)
        
        return output
    except Exception as e:
        current_app.logger.error(f"Error optimizando imagen: {str(e)}")
        return None

def save_uploaded_file(file, upload_folder='uploads'):
    """
    Guarda un archivo subido y retorna la URL relativa
    """
    if not file or file.filename == '':
        return None
    
    if not allowed_file(file.filename):
        raise ValueError("Tipo de archivo no permitido")
    
    # Verificar tamaño del archivo
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    if file_size > MAX_FILE_SIZE:
        raise ValueError("El archivo es demasiado grande (máximo 5MB)")
    
    try:
        # Crear directorio si no existe
        upload_path = os.path.join(current_app.static_folder, upload_folder)
        os.makedirs(upload_path, exist_ok=True)
        
        # Generar nombre único
        filename = generate_unique_filename(file.filename)
        
        # Optimizar imagen
        optimized_image = optimize_image(file)
        if optimized_image is None:
            # Si no se pudo optimizar, guardar el archivo original
            file_path = os.path.join(upload_path, filename)
            file.save(file_path)
        else:
            # Guardar imagen optimizada
            file_path = os.path.join(upload_path, filename)
            with open(file_path, 'wb') as f:
                f.write(optimized_image.getvalue())
        
        # Retornar URL relativa
        return f"/static/{upload_folder}/{filename}"
        
    except Exception as e:
        current_app.logger.error(f"Error guardando archivo: {str(e)}")
        raise ValueError(f"Error al guardar el archivo: {str(e)}")

def delete_uploaded_file(file_url):
    """
    Elimina un archivo subido dado su URL
    """
    if not file_url or not file_url.startswith('/static/'):
        return False
    
    try:
        # Extraer la ruta relativa
        relative_path = file_url.replace('/static/', '')
        file_path = os.path.join(current_app.static_folder, relative_path)
        
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        
    except Exception as e:
        current_app.logger.error(f"Error eliminando archivo: {str(e)}")
    
    return False
