# Inkafarma · Sitio web informativo

Sitio público de presentación para una farmacia. Muestra información, un catálogo de productos de solo lectura, servicios, un formulario para contactar y una solicitud para agendar una cita médica.

## Lo que puede hacer el visitante

- Leer información general sobre la farmacia y sus servicios.
- Explorar, buscar y filtrar productos. Solo se muestran nombre, categoría, presentación y precio; no se muestran existencias ni datos internos del inventario.
- Enviar un mensaje desde **Contáctanos**.
- Enviar una solicitud de cita con un servicio y horario preferido. La farmacia debe confirmar la disponibilidad por teléfono.

El catálogo público es de solo lectura. La administración de productos está disponible en un área interna con inicio de sesión.

## Administración de productos (demo académica)

La opción **Iniciar sesión** del encabezado abre el área administrativa en `/admin/login`. Desde allí se puede crear, listar, actualizar y eliminar productos. Cada producto tiene una relación muchos-a-uno con `categories` mediante `products.category_id`, y la categoría asociada aparece en el formulario y en el listado. Configura `ADMIN_USERNAME` y `ADMIN_PASSWORD` en `.env`; para la demostración local se usan `admin` / `admin123`. Cambia esas credenciales y `SECRET_KEY` antes de desplegar. `schema.sql` crea la tabla de categorías y la relación para una base nueva. Para migrar la base de la versión anterior, respáldala y ejecuta `migrate_categories.sql` una vez antes de iniciar la app nueva.

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

En el primer inicio con SQLite, la aplicación carga cuatro productos de demostración para que el catálogo muestre las imágenes incluidas en `app/static/img/`. No agrega datos de demostración a una base RDS.

## Conectar con AWS RDS

RDS permanece **privado**. Para ejecutar esta app desde tu PC, crea un túnel SSH por una instancia EC2 bastión que tenga acceso a la misma VPC que RDS. AWS también recomienda usar una bastión o VPN cuando necesitas llegar a una base privada desde fuera de la VPC.

### 1. Reglas de red

- En el grupo de seguridad de la EC2 bastión, permite SSH/TCP `22` desde tu IP pública.
- En el grupo de seguridad de RDS, permite MySQL/TCP `3306` con origen el **grupo de seguridad de la EC2 bastión**. No uses una regla abierta a Internet.
- La instancia EC2 necesita una dirección pública o una ruta SSH accesible desde tu PC. RDS se queda con **Public access: No**.

La EC2 y RDS deben tener conectividad de red dentro de la VPC (o por una conexión privada equivalente).

### 2. Abrir el túnel en Windows

En una primera ventana de PowerShell, reemplaza la ruta de la llave, el endpoint de RDS, el usuario SSH y la IP pública de la EC2:

```powershell
ssh -i "C:\ruta\a\mi-llave.pem" -N -L 3307:MI-ENDPOINT-RDS:3306 ec2-user@IP-PUBLICA-EC2
```

Usa `ec2-user` para Amazon Linux o el usuario configurado en tu instancia. Deja esa ventana abierta mientras uses la aplicación. El puerto local `3307` se reenvía por SSH al puerto `3306` de RDS.

### 3. Configurar el proyecto

En el `.env` del proyecto, usa la dirección local del túnel. La configuración de la app acepta estas variables y codifica el usuario y la contraseña al construir la URL de conexión:

```dotenv
DATABASE_URL=mysql+pymysql://USUARIO:CONTRASENA@127.0.0.1:3307/farmacia_inkafarma?charset=utf8mb4
FLASK_DEBUG=0
```

La URL usa `mysql+pymysql` porque ese es el conector instalado por `requirements.txt`. No dejes espacios alrededor del usuario, la contraseña, el host ni el puerto; si la contraseña contiene caracteres reservados de URL, codifícalos. No compartas `.env` ni lo subas a Git. En otra ventana de PowerShell, activa el entorno virtual y ejecuta `python app.py`. Mientras el túnel siga abierto, la app se conecta a la base privada. Si Workbench necesita conectarse desde tu PC, configura su host como `127.0.0.1` y su puerto como `3307` mientras el túnel está activo.

### 4. Crear las tablas

Con el túnel abierto, conecta MySQL Workbench a `127.0.0.1:3307` y ejecuta `schema.sql` una sola vez. El script crea las tablas y agrega cuatro productos de demostración. Si la base tiene otro nombre, cambia `CREATE DATABASE` y `USE` en el script y configura el mismo nombre en `DB_NAME`. El usuario MySQL necesita permisos para crear tablas durante esta preparación y para que la aplicación lea productos y guarde citas y mensajes.

Si ejecutas la aplicación en EC2 dentro de la VPC, no necesitas el túnel local. Usa el endpoint privado directamente en `DATABASE_URL`:

```dotenv
DATABASE_URL=mysql+pymysql://USUARIO:CONTRASENA@ENDPOINT-RDS:3306/farmacia_inkafarma?charset=utf8mb4
```

En el grupo de seguridad de RDS, permite MySQL/TCP `3306` desde el grupo de seguridad de esa EC2.

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
