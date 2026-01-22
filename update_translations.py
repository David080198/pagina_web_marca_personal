# Script para agregar traducciones al español automáticamente
import re

# Diccionario de traducciones comunes
translations = {
    # Navegación
    "Home": "Inicio",
    "Projects": "Proyectos",
    "Courses": "Cursos",
    "Blog": "Blog",
    "Contact": "Contacto",
    "Articles": "Artículos",
    
    # Usuario
    "My Profile": "Mi Perfil",
    "Dashboard": "Panel de Control",
    "Admin": "Administración",
    "Logout": "Salir",
    "Login": "Ingresar",
    
    # Login/Auth
    "Access your account": "Accede a tu cuenta",
    "Username or Email": "Usuario o Email",
    "You can use your username or email": "Puedes usar tu nombre de usuario o email",
    "Password": "Contraseña",
    "Remember me": "Recordarme",
    "Don't have an account?": "¿No tienes cuenta?",
    "Register here": "Regístrate aquí",
    "Enter your username or email": "Ingrese su usuario o email",
    "Enter your password": "Ingrese su contraseña",
    
    # Página principal
    "Available for projects": "Disponible para proyectos",
    "Professional": "Profesional",
    "Software Development": "Desarrollo de Software",
    "I transform ideas into scalable digital solutions. Specialized in web development and automation.": "Transformo ideas en soluciones digitales escalables. Especializado en desarrollo web y automatización.",
    "View Projects": "Ver Proyectos",
    "Students": "Estudiantes",
    "Years": "Años",
    
    # Servicios
    "Services": "Servicios",
    "Solutions": "Soluciones",
    "Web Development": "Desarrollo Web",
    "Modern and optimized web applications.": "Aplicaciones web modernas y optimizadas.",
    "Automation": "Automatización",
    "Scripts and bots to optimize processes.": "Scripts y bots para optimizar procesos.",
    "Mentoring": "Mentoría",
    "Personalized programming classes.": "Clases personalizadas de programación.",
    
    # Portfolio
    "Portfolio": "Portafolio",
    "Featured": "Destacados",
    "Project": "Proyecto",
    "View": "Ver",
    "View All": "Ver Todos",
    
    # Educación
    "Education": "Educación",
    "Available": "Disponibles",
    "Course": "Curso",
    "View Course": "Ver Curso",
    
    # Blog
    "Latest": "Últimas",
    "Posts": "Publicaciones",
    "Read more": "Leer más",
    "View Blog": "Ver Blog",
    
    # CTA
    "Ready for your": "Listo para tu",
    "project": "proyecto",
    "Let's work together to create technological solutions.": "Trabajemos juntos para crear soluciones tecnológicas.",
    
    # Contacto
    "Contact Information": "Información de Contacto",
    "Follow me on:": "Sígueme en:",
    "Send Message": "Enviar Mensaje",
    "Name": "Nombre",
    "Your full name": "Tu nombre completo",
    "Email": "Correo Electrónico",
    "your@email.com": "tu@email.com",
    "Subject": "Asunto",
    "Message subject (optional)": "Asunto del mensaje (opcional)",
    "Message": "Mensaje",
    "Write your message here...": "Escribe tu mensaje aquí...",
    
    # Footer
    "Software development and technological solutions.": "Desarrollo de software y soluciones tecnológicas.",
    "Links": "Enlaces",
    "Resources": "Recursos",
    "Connect": "Conecta",
    "2024 CODEXSOTO. All rights reserved.": "2024 CODEXSOTO. Todos los derechos reservados.",
}

# Leer el archivo .po
po_file = r"c:\Users\David Soto\Desktop\Marca Personal\marca_personal\translations\es\LC_MESSAGES\messages.po"

with open(po_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Reemplazar las traducciones vacías
for english, spanish in translations.items():
    # Buscar el patrón msgid "..." msgstr ""
    pattern = re.escape(f'msgid "{english}"') + r'\nmsgstr ""'
    replacement = f'msgid "{english}"\nmsgstr "{spanish}"'
    content = re.sub(pattern, replacement, content)

# Guardar el archivo actualizado
with open(po_file, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"✅ Archivo de traducción actualizado: {po_file}")
print(f"📝 Traducciones agregadas: {len(translations)}")
