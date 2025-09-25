# CodexSoto - Página de Marca Personal

CodexSoto es una aplicación web moderna desarrollada con Flask para crear una página de marca personal profesional enfocada en investigación en inteligencia artificial, automatizaciones y cursos.

## 🚀 Características

### Funcionalidades Principales
- **Página de Inicio**: Presentación profesional con secciones destacadas
- **Investigación**: Portafolio de proyectos de investigación académica
- **Automatizaciones**: Showcase de proyectos de automatización
- **Cursos**: Plataforma para mostrar y gestionar cursos
- **Blog**: Sistema de publicaciones con soporte para Markdown
- **Contacto**: Formulario de contacto con integración de email

### Panel de Administración
- **Dashboard**: Estadísticas y acceso rápido a funcionalidades
- **Gestión de Contenido**: CRUD completo para posts, cursos y proyectos
- **Configuración de Sitio**: Personalización de colores, temas y contenido
- **Administración de Blog**: Editor con soporte para Markdown
- **Gestión de Mensajes**: Visualización y administración de mensajes de contacto

### API REST
- **Endpoints JSON**: Acceso programático a contenido del sitio
- **Documentación**: API documentada para integración externa
- **Filtros**: Búsqueda y filtrado de contenido

## 🛠 Tecnologías Utilizadas

- **Backend**: Flask (Python)
- **Base de Datos**: SQLite (desarrollo) / PostgreSQL (producción)
- **Frontend**: Bootstrap 5, JavaScript ES6
- **Autenticación**: Flask-Login
- **ORM**: SQLAlchemy con Flask-SQLAlchemy
- **Migraciones**: Flask-Migrate
- **Email**: Flask-Mail
- **Contenedores**: Docker y Docker Compose
- **Servidor Web**: Nginx (reverse proxy)
- **WSGI**: Gunicorn

## 📋 Requisitos Previos

- Docker y Docker Compose instalados
- Git (para clonar el repositorio)
- Al menos 2GB de RAM disponible
- Puerto 80 y 5000 disponibles

## 🔧 Instalación y Configuración

### 1. Clonar el Repositorio
```bash
git clone <tu-repositorio>
cd marca_personal
```

### 2. Configurar Variables de Entorno
```bash
# Copiar el archivo de ejemplo
cp .env.example .env

# Editar las variables según tu configuración
# Cambiar especialmente:
# - SECRET_KEY (generar una clave segura)
# - ADMIN_EMAIL y ADMIN_PASSWORD
# - Configuración de email si deseas usar notificaciones
```

### 3. Levantar con Docker Compose

#### Desarrollo (sin Nginx)
```bash
# Levantar solo la aplicación y base de datos
docker-compose up web db redis
```

#### Producción (con Nginx)
```bash
# Levantar todos los servicios
docker-compose up -d
```

### 4. Acceder a la Aplicación
- **Aplicación**: http://localhost (con Nginx) o http://localhost:5000 (desarrollo)
- **Admin Panel**: http://localhost/auth/login
  - Usuario: `admin`
  - Contraseña: `admin123` (cambiar en producción)

## 📁 Estructura del Proyecto

```
marca_personal/
├── app/
│   ├── blueprints/          # Blueprints de Flask
│   │   ├── admin.py         # Panel de administración
│   │   ├── api.py           # API REST
│   │   ├── auth.py          # Autenticación
│   │   └── main.py          # Rutas principales
│   ├── models/              # Modelos de base de datos
│   │   ├── blog.py          # Modelo de posts del blog
│   │   ├── course.py        # Modelo de cursos
│   │   ├── project.py       # Modelo de proyectos
│   │   ├── site_config.py   # Configuración del sitio
│   │   ├── user.py          # Modelo de usuarios
│   │   └── contact.py       # Mensajes de contacto
│   ├── static/              # Archivos estáticos
│   │   ├── css/             # Estilos CSS
│   │   ├── js/              # JavaScript
│   │   └── images/          # Imágenes
│   └── templates/           # Templates Jinja2
│       ├── admin/           # Templates del admin
│       ├── auth/            # Templates de autenticación
│       └── *.html           # Templates principales
├── uploads/                 # Archivos subidos
├── migrations/              # Migraciones de base de datos
├── docker-compose.yml       # Configuración de Docker Compose
├── Dockerfile              # Imagen de Docker
├── requirements.txt        # Dependencias de Python
├── nginx.conf             # Configuración de Nginx
└── app.py                 # Punto de entrada de la aplicación
```

## 🎨 Personalización

### Cambiar Colores y Tema
1. Acceder al panel de administración
2. Ir a "Configuración"
3. Modificar colores primarios y secundarios
4. Activar/desactivar modo oscuro

### Agregar Contenido
1. **Posts del Blog**: Admin → Blog → Nuevo Post
2. **Cursos**: Admin → Cursos → Nuevo Curso
3. **Proyectos**: Admin → Proyectos → Nuevo Proyecto

### Personalizar Información
- Modificar `hero_title`, `hero_subtitle` y `about_text` desde la configuración
- Agregar enlaces a redes sociales
- Cambiar información de contacto

## 🔌 API REST

La aplicación expone una API REST para acceso programático:

### Endpoints Disponibles

```
GET /api/posts          # Listar todos los posts publicados
GET /api/posts/<slug>   # Obtener post específico
GET /api/courses        # Listar todos los cursos
GET /api/courses/<slug> # Obtener curso específico
GET /api/projects       # Listar proyectos (filtrable por categoría)
GET /api/projects/<slug># Obtener proyecto específico
GET /api/config         # Configuración pública del sitio
```

### Ejemplos de Uso

```bash
# Obtener todos los posts
curl http://localhost/api/posts

# Obtener proyectos de investigación
curl http://localhost/api/projects?category=research

# Obtener configuración del sitio
curl http://localhost/api/config
```

## 🐳 Comandos Docker Útiles

```bash
# Ver logs de la aplicación
docker-compose logs web

# Acceder al contenedor de la aplicación
docker-compose exec web bash

# Reiniciar solo la aplicación web
docker-compose restart web

# Parar todos los servicios
docker-compose down

# Parar y eliminar volúmenes (CUIDADO: elimina la base de datos)
docker-compose down -v

# Reconstruir la imagen
docker-compose build web
```

## 🔧 Comandos de Base de Datos

```bash
# Acceder al contenedor de la aplicación
docker-compose exec web bash

# Dentro del contenedor:
# Inicializar migraciones (solo la primera vez)
flask db init

# Crear una migración
flask db migrate -m "Descripción del cambio"

# Aplicar migraciones
flask db upgrade
```

## 🚀 Despliegue en Producción

### Configuración de Seguridad
1. **Cambiar credenciales por defecto**:
   - Modificar `ADMIN_PASSWORD` en docker-compose.yml
   - Generar un `SECRET_KEY` seguro
   - Cambiar contraseñas de la base de datos

2. **Variables de entorno de producción**:
   ```yaml
   environment:
     - FLASK_ENV=production
     - SECRET_KEY=tu-clave-super-secreta-muy-larga
     - ADMIN_PASSWORD=contraseña-muy-segura
   ```

3. **HTTPS con SSL**:
   - Configurar certificados SSL en Nginx
   - Usar Let's Encrypt para certificados gratuitos

### Backup de Base de Datos
```bash
# Crear backup
docker-compose exec db pg_dump -U codexsoto codexsoto_db > backup.sql

# Restaurar backup
docker-compose exec -T db psql -U codexsoto codexsoto_db < backup.sql
```

## 🐛 Solución de Problemas

### Problema: La aplicación no inicia
- Verificar que los puertos 80 y 5000 no estén ocupados
- Revisar los logs: `docker-compose logs web`
- Verificar la configuración de variables de entorno

### Problema: No se pueden subir imágenes
- Verificar permisos del directorio `uploads/`
- Verificar límites de tamaño en nginx.conf

### Problema: Error de base de datos
- Verificar que PostgreSQL esté corriendo: `docker-compose ps`
- Aplicar migraciones: `docker-compose exec web flask db upgrade`

## 🤝 Contribución

1. Fork el proyecto
2. Crear una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear un Pull Request

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 📞 Contacto

- **Autor**: David Soto
- **Email**: admin@codexsoto.com
- **GitHub**: [Tu GitHub]
- **LinkedIn**: [Tu LinkedIn]

## 🔄 Roadmap

### Próximas Características
- [ ] Sistema de comentarios en el blog
- [ ] Newsletter/suscripción por email
- [ ] Integración con redes sociales
- [ ] Sistema de etiquetas para posts
- [ ] Búsqueda avanzada
- [ ] Panel de analytics
- [ ] Multiidioma
- [ ] PWA (Progressive Web App)

### Mejoras Técnicas
- [ ] Tests automatizados
- [ ] CI/CD con GitHub Actions
- [ ] Monitoreo con Prometheus/Grafana
- [ ] Cache con Redis
- [ ] Optimización de imágenes
- [ ] CDN para archivos estáticos

---

¿Necesitas ayuda? Abre un issue en el repositorio o contacta al desarrollador.
