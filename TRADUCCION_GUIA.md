# Sistema Multi-Idioma (i18n) - Guía de Uso

## 🌍 Configuración Implementada

Tu aplicación ahora soporta múltiples idiomas (inglés y español) usando **Flask-Babel**.

### Idiomas Disponibles:
- 🇺🇸 **Inglés (en)** - Idioma por defecto
- 🇪🇸 **Español (es)**

## 📝 Cómo Usar Traducciones en Templates

### 1. En archivos HTML (Jinja2):

Usa la función `_()` o `gettext()` para marcar texto traducible:

```html
<!-- Antes (sin traducción) -->
<h1>Bienvenido a CodexSoto</h1>
<p>Cursos de programación</p>

<!-- Después (con traducción) -->
<h1>{{ _('Welcome to CodexSoto') }}</h1>
<p>{{ _('Programming courses') }}</p>
```

### 2. En archivos Python:

Importa y usa `gettext` o su alias `_`:

```python
from flask_babel import gettext as _

# En tus rutas o funciones
flash(_('Login successful!'), 'success')
flash(_('Please enter a valid email'), 'error')
```

### 3. Variables en traducciones:

Usa `%(variable)s` para incluir variables:

```python
# Python
message = _('Welcome, %(name)s!', name=user.name)

# Template
<p>{{ _('You have %(count)d new messages', count=5) }}</p>
```

## 🔧 Flujo de Trabajo para Agregar/Modificar Traducciones

### Paso 1: Marcar texto traducible
Agrega `_()` alrededor del texto en inglés en tus templates y código Python.

### Paso 2: Extraer mensajes
```bash
pybabel extract -F babel.cfg -o messages.pot .
```

### Paso 3: Actualizar catálogos de traducción
```bash
pybabel update -i messages.pot -d translations
```

### Paso 4: Editar traducciones
Abre los archivos `.po` y agrega las traducciones:

**translations/es/LC_MESSAGES/messages.po:**
```po
msgid "Welcome to CodexSoto"
msgstr "Bienvenido a CodexSoto"

msgid "Programming courses"
msgstr "Cursos de programación"

msgid "Contact"
msgstr "Contacto"
```

**translations/en/LC_MESSAGES/messages.po:**
```po
msgid "Welcome to CodexSoto"
msgstr "Welcome to CodexSoto"

msgid "Programming courses"
msgstr "Programming courses"
```

### Paso 5: Compilar traducciones
```bash
pybabel compile -d translations
```

### Paso 6: Reiniciar la aplicación
```bash
# Si usas Docker:
docker-compose restart web

# Si corres localmente:
# Reinicia el servidor Flask
```

## 🎯 Ejemplo Completo

### Antes (index.html sin traducción):
```html
<section class="hero">
    <h1>Desarrollador Full Stack</h1>
    <p>Especialista en IA y Automatización</p>
    <a href="/projects" class="btn btn-primary">Ver Proyectos</a>
</section>
```

### Después (index.html con traducción):
```html
<section class="hero">
    <h1>{{ _('Full Stack Developer') }}</h1>
    <p>{{ _('AI and Automation Specialist') }}</p>
    <a href="/projects" class="btn btn-primary">{{ _('View Projects') }}</a>
</section>
```

### Archivo de traducción español (messages.po):
```po
msgid "Full Stack Developer"
msgstr "Desarrollador Full Stack"

msgid "AI and Automation Specialist"
msgstr "Especialista en IA y Automatización"

msgid "View Projects"
msgstr "Ver Proyectos"
```

## 🚀 Selector de Idioma

El selector de idioma ya está agregado en la barra de navegación (`base.html`). Los usuarios pueden:
- Hacer clic en el ícono de globo 🌍
- Seleccionar entre English o Español
- La preferencia se guarda en la sesión

## 📁 Estructura de Archivos

```
marca_personal/
├── babel.cfg                    # Configuración de Babel
├── messages.pot                 # Template de mensajes (generado)
├── translations/                # Carpeta de traducciones
│   ├── en/                     # Inglés
│   │   └── LC_MESSAGES/
│   │       ├── messages.po     # Archivo editable
│   │       └── messages.mo     # Archivo compilado
│   └── es/                     # Español
│       └── LC_MESSAGES/
│           ├── messages.po     # Archivo editable
│           └── messages.mo     # Archivo compilado
└── app/
    └── blueprints/
        └── language.py          # Blueprint para cambio de idioma
```

## 💡 Consejos

1. **Siempre escribe el texto original en inglés** en tus templates
2. **Mantén las traducciones simples** y claras
3. **Usa contexto** cuando la misma palabra puede tener diferentes significados
4. **Prueba ambos idiomas** regularmente
5. **Actualiza las traducciones** cada vez que agregues nuevo contenido

## 🔄 Comandos Útiles

```bash
# Extraer nuevos mensajes
pybabel extract -F babel.cfg -o messages.pot .

# Actualizar archivos de traducción existentes
pybabel update -i messages.pot -d translations

# Compilar traducciones (necesario después de editar .po)
pybabel compile -d translations

# Crear nuevo idioma (ejemplo: francés)
pybabel init -i messages.pot -d translations -l fr
```

## 🌐 URLs con Parámetro de Idioma

También puedes cambiar el idioma usando parámetros en la URL:
- `http://localhost:5000/?lang=en` - Inglés
- `http://localhost:5000/?lang=es` - Español

## ✅ Estado Actual

- ✅ Flask-Babel instalado y configurado
- ✅ Archivos de traducción creados (en, es)
- ✅ Selector de idioma en navbar
- ✅ Blueprint para cambio de idioma
- ✅ Sistema de detección automática de idioma
- ⚠️ **Pendiente**: Traducir todo el contenido de los templates

## 📝 Próximos Pasos

1. Ir template por template agregando `_()` alrededor del texto
2. Extraer los mensajes con `pybabel extract`
3. Actualizar los catálogos con `pybabel update`
4. Traducir al español en los archivos `.po`
5. Compilar con `pybabel compile`
6. Probar en ambos idiomas

---

**Nota**: Por defecto, la aplicación mostrará contenido en **inglés**. Los usuarios pueden cambiar a español usando el selector de idioma en la navegación.
