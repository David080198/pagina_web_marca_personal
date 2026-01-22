# Ejemplo de Traducción para index.html

## Template Original (sin traducciones)
Aquí te muestro cómo convertir el contenido de index.html para que soporte multi-idioma.

### PASO 1: Importar gettext en el template
No es necesario importar nada, Flask-Babel automáticamente hace disponible la función `_()`.

### PASO 2: Envolver texto en la función `_()`

#### Ejemplo de ANTES:
```html
<h1>Bienvenido a CodexSoto</h1>
<p>Desarrollador Full Stack | IA & Automatización</p>
<a href="#" class="btn btn-primary">Ver Proyectos</a>
```

#### Ejemplo de DESPUÉS:
```html
<h1>{{ _('Welcome to CodexSoto') }}</h1>
<p>{{ _('Full Stack Developer | AI & Automation') }}</p>
<a href="#" class="btn btn-primary">{{ _('View Projects') }}</a>
```

### PASO 3: Agregar traducciones al español

Una vez que hayas marcado todo el texto, ejecuta:
```bash
pybabel extract -F babel.cfg -o messages.pot .
pybabel update -i messages.pot -d translations
```

Luego edita: `translations/es/LC_MESSAGES/messages.po`

```po
# Traducciones al español
msgid "Welcome to CodexSoto"
msgstr "Bienvenido a CodexSoto"

msgid "Full Stack Developer | AI & Automation"
msgstr "Desarrollador Full Stack | IA & Automatización"

msgid "View Projects"
msgstr "Ver Proyectos"

msgid "Contact"
msgstr "Contacto"

msgid "About Me"
msgstr "Sobre Mí"

msgid "My Skills"
msgstr "Mis Habilidades"

msgid "Recent Projects"
msgstr "Proyectos Recientes"

msgid "Latest Blog Posts"
msgstr "Últimas Publicaciones"

msgid "Get In Touch"
msgstr "Ponte en Contacto"
```

### PASO 4: Compilar
```bash
pybabel compile -d translations
```

### PASO 5: Reiniciar la aplicación
Si usas Docker:
```bash
docker-compose restart web
```

---

## 🎨 Plantilla Completa de Ejemplo

Aquí hay un ejemplo más completo de cómo se vería una sección del index.html:

```html
<!-- Hero Section -->
<section class="hero-section">
    <div class="container">
        <div class="row align-items-center">
            <div class="col-lg-6">
                <h1 class="display-4 fw-bold">{{ _('Hi, I\'m David Soto') }}</h1>
                <p class="lead">{{ _('Full Stack Developer & AI Specialist') }}</p>
                <p class="text-muted">
                    {{ _('I create intelligent solutions and automations that transform businesses.') }}
                </p>
                <div class="mt-4">
                    <a href="{{ url_for('main.projects') }}" class="btn btn-primary btn-lg me-3">
                        {{ _('View Projects') }}
                    </a>
                    <a href="{{ url_for('main.contact') }}" class="btn btn-outline-primary btn-lg">
                        {{ _('Contact Me') }}
                    </a>
                </div>
            </div>
            <div class="col-lg-6">
                <img src="{{ url_for('static', filename='images/hero-image.png') }}" 
                     alt="{{ _('Developer working') }}" 
                     class="img-fluid">
            </div>
        </div>
    </div>
</section>

<!-- Skills Section -->
<section class="skills-section py-5">
    <div class="container">
        <h2 class="text-center mb-5">{{ _('My Skills') }}</h2>
        <div class="row">
            <div class="col-md-4 mb-4">
                <div class="skill-card">
                    <i class="fas fa-code fa-3x mb-3"></i>
                    <h4>{{ _('Web Development') }}</h4>
                    <p>{{ _('Modern web applications with Flask, React, and more.') }}</p>
                </div>
            </div>
            <div class="col-md-4 mb-4">
                <div class="skill-card">
                    <i class="fas fa-robot fa-3x mb-3"></i>
                    <h4>{{ _('Artificial Intelligence') }}</h4>
                    <p>{{ _('Machine learning models and intelligent automation.') }}</p>
                </div>
            </div>
            <div class="col-md-4 mb-4">
                <div class="skill-card">
                    <i class="fas fa-cog fa-3x mb-3"></i>
                    <h4>{{ _('Automation') }}</h4>
                    <p>{{ _('Process automation and workflow optimization.') }}</p>
                </div>
            </div>
        </div>
    </div>
</section>
```

## 📋 Lista de Traducciones Comunes

Aquí tienes una lista de traducciones comunes que probablemente necesitarás:

```po
# Navegación
msgid "Home"
msgstr "Inicio"

msgid "Projects"
msgstr "Proyectos"

msgid "Courses"
msgstr "Cursos"

msgid "Blog"
msgstr "Blog"

msgid "Contact"
msgstr "Contacto"

# Acciones
msgid "View More"
msgstr "Ver Más"

msgid "Read More"
msgstr "Leer Más"

msgid "Learn More"
msgstr "Aprender Más"

msgid "Download"
msgstr "Descargar"

msgid "Share"
msgstr "Compartir"

msgid "Subscribe"
msgstr "Suscribirse"

# Formularios
msgid "Name"
msgstr "Nombre"

msgid "Email"
msgstr "Correo Electrónico"

msgid "Message"
msgstr "Mensaje"

msgid "Send"
msgstr "Enviar"

msgid "Submit"
msgstr "Enviar"

# Mensajes
msgid "Welcome"
msgstr "Bienvenido"

msgid "Thank you"
msgstr "Gracias"

msgid "Success"
msgstr "Éxito"

msgid "Error"
msgstr "Error"

# Fechas y tiempo
msgid "Today"
msgstr "Hoy"

msgid "Yesterday"
msgstr "Ayer"

msgid "ago"
msgstr "hace"

msgid "Posted on"
msgstr "Publicado el"
```

---

**Nota Importante**: Recuerda que después de editar los archivos `.po`, **siempre** debes compilarlos con `pybabel compile -d translations` para que los cambios tengan efecto.
