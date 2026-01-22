# 🐳 Instrucciones Docker + Multi-Idioma

## Levantar la Aplicación con Docker

### 1. Asegúrate de que Docker Desktop está corriendo
Abre Docker Desktop y espera a que inicie completamente.

### 2. Construir y levantar los contenedores
```bash
docker-compose up --build -d
```

Esto levantará:
- **web** (Flask app) en http://localhost:5000
- **nginx** (Reverse proxy) en http://localhost:8080
- **db** (PostgreSQL) en localhost:5432
- **redis** (Cache) en localhost:6379

### 3. Verificar que los contenedores están corriendo
```bash
docker-compose ps
```

### 4. Ver logs
```bash
# Ver logs de todos los servicios
docker-compose logs -f

# Ver logs solo del servicio web
docker-compose logs -f web
```

## 🌍 Trabajar con Traducciones en Docker

### Opción 1: Editar traducciones fuera del contenedor
1. Edita los archivos `.po` en tu máquina local:
   - `translations/es/LC_MESSAGES/messages.po`
   - `translations/en/LC_MESSAGES/messages.po`

2. Compila las traducciones:
   ```bash
   pybabel compile -d translations
   ```

3. Reinicia el contenedor:
   ```bash
   docker-compose restart web
   ```

### Opción 2: Trabajar dentro del contenedor
```bash
# Entrar al contenedor
docker-compose exec web bash

# Extraer mensajes
pybabel extract -F babel.cfg -o messages.pot .

# Actualizar catálogos
pybabel update -i messages.pot -d translations

# Compilar traducciones
pybabel compile -d translations

# Salir del contenedor
exit

# Reiniciar para aplicar cambios
docker-compose restart web
```

## 📝 Flujo de Trabajo Completo

### Paso 1: Agregar traducciones a tus templates
```bash
# Edita tus archivos HTML agregando _() alrededor del texto
# Ejemplo: <h1>{{ _('Welcome') }}</h1>
```

### Paso 2: Extraer y actualizar
```bash
# En tu máquina local (o dentro del contenedor)
pybabel extract -F babel.cfg -o messages.pot .
pybabel update -i messages.pot -d translations
```

### Paso 3: Traducir
```bash
# Edita: translations/es/LC_MESSAGES/messages.po
# Agrega las traducciones al español
```

### Paso 4: Compilar
```bash
pybabel compile -d translations
```

### Paso 5: Reiniciar
```bash
docker-compose restart web
```

### Paso 6: Probar
Visita http://localhost:8080 y cambia el idioma usando el selector en la navegación.

## 🔄 Comandos Docker Útiles

```bash
# Detener todos los contenedores
docker-compose down

# Detener y eliminar volúmenes (¡cuidado! elimina la BD)
docker-compose down -v

# Reconstruir solo el servicio web
docker-compose build web

# Ver logs en tiempo real
docker-compose logs -f web

# Ejecutar comandos dentro del contenedor
docker-compose exec web python
docker-compose exec web flask shell

# Reiniciar un servicio específico
docker-compose restart web

# Ver recursos utilizados
docker stats

# Limpiar contenedores detenidos
docker system prune
```

## 🚀 Acceder a la Aplicación

Una vez que Docker Compose esté corriendo:

- **Nginx (recomendado)**: http://localhost:8080
- **Flask directo**: http://localhost:5000
- **PostgreSQL**: localhost:5432
  - Usuario: codexsoto
  - Contraseña: password123
  - Base de datos: codexsoto_db

## 🌐 Cambiar Idioma

### Desde la Interfaz:
1. Haz clic en el ícono 🌍 en la barra de navegación
2. Selecciona "English" o "Español"

### Usando URL:
- http://localhost:8080/?lang=en
- http://localhost:8080/?lang=es

## ⚠️ Solución de Problemas

### El idioma no cambia:
```bash
# 1. Verifica que las traducciones estén compiladas
ls translations/*/LC_MESSAGES/*.mo

# 2. Si no existen archivos .mo, compílalos
pybabel compile -d translations

# 3. Reinicia el contenedor
docker-compose restart web
```

### Error al construir Docker:
```bash
# Limpiar caché de Docker y reconstruir
docker-compose down
docker system prune -f
docker-compose up --build
```

### Las traducciones no se actualizan:
```bash
# 1. Detén los contenedores
docker-compose down

# 2. Recompila las traducciones
pybabel compile -d translations

# 3. Reconstruye y levanta
docker-compose up --build
```

## 📦 Volúmenes y Persistencia

Los siguientes datos persisten entre reinicios:
- **Base de datos PostgreSQL**: Volumen `postgres_data`
- **Uploads**: Carpeta `./uploads` (mapeada)
- **Imágenes estáticas**: Carpeta `./app/static/images` (mapeada)

## 🔐 Variables de Entorno

Definidas en `docker-compose.yml`:
```yaml
DATABASE_URL=postgresql://codexsoto:password123@db:5432/codexsoto_db
SECRET_KEY=your-super-secret-key-change-in-production
ADMIN_EMAIL=david@codexsoto.com
ADMIN_PASSWORD=MiPasswordSeguro123!
FLASK_ENV=production
```

Para producción, crea un archivo `.env` y sobrescribe estos valores.

## ✅ Checklist de Inicio

- [ ] Docker Desktop está corriendo
- [ ] Has ejecutado `docker-compose up --build -d`
- [ ] Puedes acceder a http://localhost:8080
- [ ] El selector de idioma aparece en la navegación
- [ ] Puedes cambiar entre English y Español
- [ ] Los logs no muestran errores: `docker-compose logs -f web`

---

**¡Listo!** Tu aplicación ahora soporta múltiples idiomas y está corriendo en Docker. 🎉
