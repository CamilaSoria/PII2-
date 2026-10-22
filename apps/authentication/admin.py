from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, Rol, UsuarioRol, Auditoria

# --- ACCIONES EN LOTE (Superpoderes para el Administrador) ---
@admin.action(description='🟢 Activar usuarios seleccionados')
def activar_usuarios(modeladmin, request, queryset):
    queryset.update(is_active=True)
    modeladmin.message_user(request, f"Se han activado {queryset.count()} usuarios con éxito.")

@admin.action(description='🔴 Desactivar (Dar de baja) usuarios seleccionados')
def desactivar_usuarios(modeladmin, request, queryset):
    queryset.update(is_active=False)
    modeladmin.message_user(request, f"Se han desactivado {queryset.count()} usuarios con éxito.")


# --- CONFIGURACIÓN DEL PANEL DE USUARIOS ---
class CustomUserAdmin(UserAdmin):
    model = Usuario
    
    # 1. Columnas en la tabla principal (Agregamos tus nuevos campos de control)
    list_display = ['email', 'nombre', 'apellido', 'is_active', 'intentos_fallidos', 'bloqueado_hasta', 'is_staff']
    
    # 🔍 Buscador inteligente y filtros laterales (Se quedan exactamente como los tenías)
    search_fields = ['email', 'nombre', 'apellido']
    ordering = ['email']
    list_filter = ['is_active', 'is_staff', 'pais_origen']
    
    # Conectamos tus acciones en lote
    actions = [activar_usuarios, desactivar_usuarios]

    # 2. SOLUCIÓN AL ERROR: Volvemos 'date_joined' y 'last_login' campos de solo lectura
    readonly_fields = ('date_joined', 'last_login')

    # 3. Reescribimos los fieldsets de forma explícita para evitar que UserAdmin herede el campo roto
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Información Personal', {'fields': ('nombre', 'apellido')}),
        ('Información de Turismo', {'fields': ('telefono', 'foto_perfil', 'idioma_preferido', 'pais_origen', 'preferencias_json')}),
        ('Permisos y Roles', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Control de Seguridad (Fuerza Bruta)', {'fields': ('intentos_fallidos', 'bloqueado_hasta')}),
        ('Fechas Importantes', {'fields': ('last_login', 'date_joined')}),
    )

    # Campos al crear un usuario nuevo desde el admin
    add_fieldsets = (
        (None, {
            'classes': ('collapse',),
            'fields': ('email', 'nombre', 'apellido', 'password'),
        }),
    )

# Registramos absolutamente todos tus modelos de vuelta
admin.site.register(Usuario, CustomUserAdmin)
admin.site.register(Rol)
admin.site.register(UsuarioRol)
admin.site.register(Auditoria)