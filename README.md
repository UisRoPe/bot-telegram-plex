# 🤖 Bot de Telegram para Plex en Raspberry Pi con OMV

Bot de notificaciones y gestión para servidores Plex alojados en Raspberry Pi con OpenMediaVault.

## ✨ Características

- ✅ Monitorización en tiempo real del servidor Plex  
- 👥 Gestión de usuarios conectados  
- 📊 Estadísticas del sistema (CPU, RAM, Temperatura)  
- 🔄 Reinicio remoto del servicio Plex  
- 📝 Visualización de logs y errores  
- 🎬 Notificación de contenido reciente  

## 🛠️ Configuración inicial

### Requisitos
- Raspberry Pi con OMV instalado  
- Python 3.8+  
- Servidor Plex funcionando  
- Cuenta de Telegram  

### Instalación

1. Clonar repositorio:
```bash
git clone https://github.com/UisRoPe/bot-telegram-plex
cd plex-bot
```

2. Instalar dependencias Raspberry PI
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
pip3 install python-telegram-bot requests plexapi
```

3. Crear entorno virtual:
```bash
python3 -m venv plexbot-env
source plexbot-env/bin/activate
```

4. Configurar variables de entorno
```bash
cp .env.example .env
nano .env
```

5. Configurar variables de entorno:
```bash
TELEGRAM_TOKEN="tu_token_de_telegram"
PLEX_TOKEN="tu_token_de_plex"
PLEX_URL="http://localhost:32400"
AUTHORIZED_USERS="19390183,123158510"
```

## 🚀 Implementación como servicio
Archivo de servicio systemd (/etc/systemd/system/plexbot.service)

1. Crea el archivo del servicio:
```bash
sudo nano /etc/systemd/system/plexbot.service
```
2. Copia el contenido anterior y guarda con Ctrl+O, Enter, Ctrl+X
3. Configura los permisos correctos:
```bash
sudo chmod 644 /etc/systemd/system/plexbot.service
```

```bash
[Unit]
Description=Plex Telegram Bot Service
After=network.target plexmediaserver.service
Requires=network.target

[Service]
User=jrojasp
Group=jrojasp
WorkingDirectory=/home/jrojasp/bots/plex

# Configuración del entorno
Environment="PATH=/home/jrojasp/plexbot-env/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
#EnvironmentFile=/home/jrojasp/bots/plex/.env  # Si usas variables de entorno

# Comando de ejecución
ExecStart=/home/jrojasp/plexbot-env/bin/python /home/jrojasp/bots/plex/plex_bot.py

# Configuración de seguridad
ProtectSystem=full
PrivateTmp=true
NoNewPrivileges=true
RestrictNamespaces=yes
RestrictSUIDSGID=yes
ProtectHome=read-only

# Política de reinicios
Restart=on-failure
RestartSec=30s
StartLimitIntervalSec=60
StartLimitBurst=3

# Configuración de logs
StandardOutput=journal
StandardError=journal
SyslogIdentifier=plexbot

[Install]
WantedBy=multi-user.target
```

## Comandos para activar el servicio
```bash
# Recargar configuración
sudo systemctl daemon-reload

# Habilitar inicio automático
sudo systemctl enable plexbot.service

# Iniciar servicio
sudo systemctl start plexbot.service

# Ver estado
systemctl status plexbot.service

# Ver logs en tiempo real
journalctl -u plexbot -f

# Reiniciar servio
sudo systemctl daemon-reload
sudo systemctl restart plexbot
```

## 📜 Comandos disponibles

### Comando Descripción Ejemplo
* /start    Menú principal  /start
* /status   Estado del servidor /status
* /users    Usuarios conectados /users
* /recent   Contenido reciente  /recent
* /stats    Estadísticas del sistema    /stats
* /logs Ver logs (admin)    /logs
* /restart  Reiniciar Plex (admin)  /restart
* /errors   Buscar errores  /errors


## 🔒 Consideraciones de seguridad
Protege tus tokens: Nunca commits tus tokens en GitHub
Usa entornos virtuales: Aísla las dependencias
Limita usuarios autorizados: Configura AUTHORIZED_USERS en .env
Actualiza regularmente: Mantén el bot y sus dependencias actualizadas

## 🆘 Soporte
Para problemas o sugerencias:
Contacto: joseluis.rojasp@outlook.com
