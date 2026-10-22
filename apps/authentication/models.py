from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver

class UsuarioManager(BaseUserManager):
    def create_user(self, email, nombre, apellido, password=None, **extra_fields):
        if not email:
            raise ValueError('El usuario debe tener un correo electrónico válido.')
        email = self.normalize_email(email)
        user = self.model(email=email, nombre=nombre, apellido=apellido, **extra_fields)
        user.set_password(password)  # Esto aplica automáticamente PBKDF2-SHA256
        user.save(using=self._db)
        return user

    def create_superuser(self, email, nombre, apellido, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, nombre, apellido, password, **extra_fields)

class Usuario(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, max_length=254, db_index=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20, null=True, blank=True)
    
    # CAMBIO AQUÍ: De CharField a ImageField
    foto_perfil = models.ImageField(upload_to='perfiles/', null=True, blank=True)
    
    idioma_preferido = models.CharField(max_length=10, default='es')
    fecha_nacimiento = models.DateField(null=True, blank=True)
    pais_origen = models.CharField(max_length=100, null=True, blank=True)
    intentos_fallidos = models.IntegerField(default=0)
    bloqueado_hasta = models.DateTimeField(null=True, blank=True)
    
    # Campos obligatorios de Django
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    
    # Campo para el Core Inteligente
    preferencias_json = models.JSONField(null=True, blank=True)

    objects = UsuarioManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nombre', 'apellido']

    def __str__(self):
        return f"{self.nombre} {self.apellido} ({self.email})"
    
class Rol(models.Model):
    id_rol = models.AutoField(primary_key=True)
    nombre_rol = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'roles_permisos'
        verbose_name = 'Rol'
        verbose_name_plural = 'Roles'

    def __str__(self):
        return self.nombre_rol


class UsuarioRol(models.Model):
    id_usuario_rol = models.AutoField(primary_key=True)
    usuario = models.ForeignKey('Usuario', on_delete=models.CASCADE, related_name='roles_asignados')
    rol = models.ForeignKey(Rol, on_delete=models.CASCADE)
    fecha_asignacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'usuario_rol'
        verbose_name = 'Rol de Usuario'
        verbose_name_plural = 'Roles de Usuarios'
        # Un usuario no debería tener el mismo rol duplicado repetidas veces
        unique_together = ('usuario', 'rol') 

    def __str__(self):
        return f"{self.usuario.email} - {self.rol.nombre_rol}"
    
class Auditoria(models.Model):
    usuario = models.ForeignKey(
        Usuario, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='auditorias_autenticacion'
    )
    usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True)
    accion = models.CharField(max_length=255)
    detalles = models.TextField(null=True, blank=True)
    fecha_hora = models.DateTimeField(auto_now_add=True)
    on_delete=models.CASCADE, 
    related_name='auditorias_autenticacion'

    class Meta:
        db_table = 'auditoria_logs'
        verbose_name = 'Log de Auditoría'
        verbose_name_plural = 'Logs de Auditoría'
        ordering = ['-fecha_hora'] # Muestra siempre lo más reciente primero

    def __str__(self):
        return f"{self.usuario} - {self.accion} ({self.fecha_hora})"
    

@receiver(user_logged_in)
def registrar_login(sender, request, user, **kwargs):
    Auditoria.objects.create(
        usuario=user,
        accion="Inicio de Sesión",
        detalles=f"El usuario ingresó exitosamente desde la IP: {request.META.get('REMOTE_ADDR')}"
    )

@receiver(user_logged_out)
def registrar_logout(sender, request, user, **kwargs):
    if user:
        Auditoria.objects.create(
            usuario=user,
            accion="Cierre de Sesión",
            detalles="El usuario cerró su sesión de forma segura."
        )

@receiver(user_login_failed)
def registrar_login_fallido(sender, credentials, request, **kwargs):
    Auditoria.objects.create(
        usuario=None,
        accion="Intento de Login Fallido",
        detalles=f"Intento de ingreso sospechoso con el correo: {credentials.get('username')}"
    )