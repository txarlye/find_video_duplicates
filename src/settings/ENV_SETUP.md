# Configuración de Variables de Entorno

## Archivo .env

Crea un archivo `.env` en la carpeta `src/settings/` con las siguientes variables:

```bash
# API Key de IMDB (obtener en https://imdb-api.com/api)
IMDB_API_KEY=tu_api_key_aqui

# Token del bot de Telegram (obtener de @BotFather)
TELEGRAM_BOT_TOKEN=tu_bot_token_aqui

# ID del canal de Telegram (formato: @channel_name o -1001234567890)
TELEGRAM_CHANNEL_ID=tu_channel_id_aqui
```

## Cómo Obtener las Variables

### IMDB API Key
1. Ve a [IMDB API](https://imdb-api.com/api)
2. Regístrate y obtén tu API key
3. Reemplaza `tu_api_key_aqui` con tu clave

### Telegram Bot Token
1. Ve a [@BotFather](https://t.me/BotFather) en Telegram
2. Usa el comando `/newbot` para crear un bot
3. Copia el token que te proporcione
4. Reemplaza `tu_bot_token_aqui` con tu token

### Telegram Channel ID
1. Crea un canal en Telegram
2. Agrega tu bot como administrador
3. Para canales públicos: usa `@nombre_del_canal`
4. Para canales privados: usa el ID numérico (ej: `-1001234567890`)
5. Reemplaza `tu_channel_id_aqui` con tu ID

## Seguridad

- **NUNCA** subas el archivo `.env` a Git
- El archivo `.env` está en `.gitignore` para proteger tu información
- Mantén tus tokens seguros y no los compartas
