# Inkafarma · Sitio web informativo

Sitio público de presentación para una farmacia. Muestra información, un catálogo de productos de solo lectura, servicios, un formulario para contactar y una solicitud para agendar una cita médica.

## Lo que puede hacer el visitante

- Leer información general sobre la farmacia y sus servicios.
- Explorar, buscar y filtrar productos. Solo se muestran nombre, categoría, presentación y precio; no se muestran existencias ni datos internos del inventario.
- Enviar un mensaje desde **Contáctanos**.
- Enviar una solicitud de cita con un servicio y horario preferido. La farmacia debe confirmar la disponibilidad por teléfono.

El sitio **no permite crear, editar ni eliminar productos**, ni administrar inventario o revisar mensajes y citas. Esas tareas corresponden a un sistema interno separado. El catálogo consulta los productos del mismo esquema MySQL/SQLite; la aplicación pública solo tiene rutas de lectura para productos.

## Ejecutar en Windows / PowerShell

Requiere Python 3.10 o posterior.

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
py app.py
```

Abre `http://127.0.0.1:5000`. También puedes usar `py run.py`. Si no configuras RDS, los datos se guardan en SQLite local (`instance/farmacia.db`).

## Conectar con AWS RDS

En `.env`, define la conexión MySQL:

```dotenv
DATABASE_URL=mysql+pymysql://USUARIO:CONTRASENA@ENDPOINT_RDS:3306/NOMBRE_BASE?charset=utf8mb4
SECRET_KEY=una-clave-larga-y-aleatoria
FLASK_DEBUG=0
```

El archivo `schema.sql` crea la base `farmacia_inkafarma` y las tres tablas del proyecto. Si usas ese nombre, configura el mismo nombre en `DATABASE_URL` (o `DB_NAME`). Si RDS no permite `CREATE DATABASE`, selecciona la base al crear la instancia y quita del script las sentencias `CREATE DATABASE` y `USE` antes de ejecutarlo.

También se aceptan `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD` y `DB_NAME`. La base de datos debe existir y el usuario configurado necesita permisos para crear las tablas al iniciar la aplicación. Permite el acceso desde el servidor web en el grupo de seguridad de RDS. No publiques `.env` ni guardes credenciales en Git.

El sitio muestra productos registrados con stock mayor que cero y sin vencimiento pasado. Si el catálogo está vacío, carga los productos desde tu proceso administrativo separado.

## Estructura

```text
app/
  config.py          Configuración SQLite / RDS
  database.py        SQLAlchemy
  constants.py       Estados y servicios
  models/            Producto, cita y contacto
  routes/            Rutas públicas Flask
  services/          Catálogo, citas y contactos
  templates/         Sitio web con Jinja
  static/css/        Estilos adaptables
  static/js/         Menú móvil y avisos
app.py               Punto de entrada
Dockerfile           Imagen de despliegue
.python-version      Versión de Python
sitemap.xml          Rutas públicas para buscadores
schema.sql           Esquema de MySQL / RDS
```

## Antes de publicar

Esta es una base demostrativa. Configura los datos reales de contacto, dirección y horarios de cada tienda. Añade protección CSRF, límites contra spam, autenticación y permisos en el sistema administrativo separado, así como políticas de privacidad, respaldo y retención. No solicites diagnósticos ni guardes información clínica en los formularios. La marca y el contenido se deben revisar antes de presentar el sitio como un canal oficial.
