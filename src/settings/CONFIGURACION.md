# 🔧 Guía de Configuración

## 📋 Configuración Inicial

### 1. **Variables de Entorno**
Copia `env.example` a `.env` y configura las variables necesarias:

```bash
cp env.example .env
```

### 2. **Configuración de PLEX**
Edita `src/settings/config.json` y configura:

```json
{
    "plex": {
        "enabled": true,
        "server_url": "http://tu-servidor:32400",
        "database_path": "ruta/a/tu/base/de/datos/plex.db",
        "token": "tu_token_de_plex"
    }
}
```

### 3. **Obtener Token de PLEX**
1. Ve a tu servidor PLEX
2. Configuración → Red → Acceso remoto
3. Copia el token y pégalo en `config.json`

## 🔒 Seguridad

### ✅ **Archivos Protegidos**
- `.env` - Variables de entorno (no se sube a Git)
- `test_files/` - Archivos de test (ignorados)
- `*.log` - Archivos de log (ignorados)
- `debug/` - Archivos de debug (ignorados)

### ⚠️ **Información Sensible**
- **Tokens de API**: Solo en `.env` o `config.json`
- **Rutas de red**: Configurables por usuario
- **Credenciales**: Nunca hardcodeadas

## 🚀 Configuración Rápida

### Para Desarrollo Local:
```json
{
    "plex": {
        "server_url": "http://localhost:32400",
        "database_path": "ruta/local/a/plex.db"
    }
}
```

### Para Servidor Remoto:
```json
{
    "plex": {
        "server_url": "http://192.168.1.100:32400",
        "database_path": "\\\\servidor\\ruta\\plex.db"
    }
}
```

## 📝 Notas Importantes

- **Nunca** subas archivos `.env` a Git
- **Siempre** usa rutas relativas cuando sea posible
- **Configura** tokens en variables de entorno
- **Revisa** el `.gitignore` antes de hacer commit
