import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from plexapi.server import PlexServer
import requests
import os
import subprocess
from datetime import datetime

# Configuración
PLEX_URL = "http://localhost:32400"
PLEX_TOKEN = "xxxxxxxxxxxxxxxxxxxxxxxxx"        # Reemplaza con tu token de Plex
TELEGRAM_TOKEN = "xxxxxxxxxxxxxxxxxxxxxxxxxx"   # Reemplaza con tu token de Telegram
AUTHORIZED_USERS = ["xxxxxxxxx", "xxxxxxxxx"]   # IDs de usuarios autorizados para comandos
ADMIN_USER = "xxxxxxxx"                         # Tu ID para comandos de administración

# Configuración de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Inicialización de Plex
try:
    plex = PlexServer(PLEX_URL, PLEX_TOKEN)
    logger.info("Conexión a Plex establecida correctamente")
except Exception as e:
    logger.error(f"Error al conectar a Plex: {e}")
    plex = None

### --- Funciones Auxiliares --- ###
def get_server_stats():
    """Obtiene estadísticas del servidor"""
    try:
        # Uso de CPU
        cpu_percent = subprocess.check_output(
            "top -bn1 | grep 'Cpu(s)' | awk '{print $2 + $4}'", 
            shell=True
        ).decode('utf-8').strip()
        
        # Uso de memoria
        mem_info = subprocess.check_output(
            "free -m | awk 'NR==2{printf \"%.2f%%\", $3*100/$2}'", 
            shell=True
        ).decode('utf-8').strip()
        
        # Temperatura (Raspberry Pi)
        try:
            temp = subprocess.check_output(
                "vcgencmd measure_temp | cut -d'=' -f2", 
                shell=True
            ).decode('utf-8').strip()
        except:
            temp = "N/A"
        
        return f"🖥️ CPU: {cpu_percent}% | 🧠 Memoria: {mem_info} | 🌡️ Temp: {temp}"
    
    except Exception as e:
        logger.error(f"Error obteniendo stats del servidor: {e}")
        return "No se pudieron obtener las estadísticas del servidor"

def get_plex_logs(lines=20):
    """Obtiene las últimas líneas del log de Plex"""
    log_path = "/var/lib/plexmediaserver/Library/Application Support/Plex Media Server/Logs/Plex Media Server.log"
    try:
        with open(log_path, 'r') as f:
            last_lines = f.readlines()[-lines:]
            return "".join(last_lines)
    except Exception as e:
        logger.error(f"Error leyendo logs de Plex: {e}")
        return f"No se pudo leer el archivo de log: {e}"

### --- Comandos del Bot --- ###
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.message.chat_id) not in AUTHORIZED_USERS:
        await update.message.reply_text("❌ No autorizado.")
        return
    
    help_text = """
🤖 *Bot de Notificaciones Plex*

📌 *Comandos disponibles:*
/start - Muestra este mensaje
/status - Estado del servidor Plex
/users - Usuarios conectados
/recent - Contenido recientemente añadido
/stats - Estadísticas del servidor
/logs - Últimas líneas del log (admin)
/restart - Reiniciar servicio Plex (admin)
/errors - Buscar errores en los logs
"""
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.message.chat_id) not in AUTHORIZED_USERS:
        await update.message.reply_text("❌ No autorizado.")
        return
    
    server_stats = get_server_stats()
    
    try:
        response = requests.get(f"{PLEX_URL}/status/sessions?X-Plex-Token={PLEX_TOKEN}", timeout=5)
        if response.status_code == 200:
            status_msg = "✅ *Plex está funcionando correctamente*\n"
            if plex:
                sessions = plex.sessions()
                status_msg += f"👥 Usuarios activos: {len(sessions)}\n"
            status_msg += f"\n{server_stats}"
            await update.message.reply_text(status_msg, parse_mode="Markdown")
        else:
            await update.message.reply_text(
                f"⚠️ *Plex responde pero con errores (Código {response.status_code})*\n\n{server_stats}", 
                parse_mode="Markdown"
            )
    except Exception as e:
        await update.message.reply_text(
            f"🔴 *Plex no responde - Posiblemente caído*\n\n{server_stats}", 
            parse_mode="Markdown"
        )

async def users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.message.chat_id) not in AUTHORIZED_USERS:
        await update.message.reply_text("❌ No autorizado.")
        return
    
    if not plex:
        await update.message.reply_text("🔴 Plex no está disponible.")
        return
    
    sessions = plex.sessions()
    if sessions:
        message = "👥 *Usuarios conectados:*\n\n"
        for session in sessions:
            message += f"• {session.user.title} ({session.title})\n"
            message += f"  📱 Dispositivo: {session.player.product}\n"
            message += f"  ⏳ Progreso: {session.progress // 60000} min\n\n"
    else:
        message = "📭 *Nadie está reproduciendo contenido actualmente*"
    
    await update.message.reply_text(message, parse_mode="Markdown")

async def recent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.message.chat_id) not in AUTHORIZED_USERS:
        await update.message.reply_text("❌ No autorizado.")
        return
    
    if not plex:
        await update.message.reply_text("🔴 Plex no está disponible.")
        return
    
    recently_added = plex.library.recentlyAdded()
    message = "🎬 *Contenido reciente en Plex:*\n\n"
    for item in recently_added[:10]:  # Muestra los 10 más recientes
        message += f"• {item.title} ({item.year})\n"
        message += f"  🏷️ Tipo: {item.type}\n"
        message += f"  📅 Añadido: {item.addedAt.strftime('%Y-%m-%d %H:%M')}\n\n"
    
    await update.message.reply_text(message, parse_mode="Markdown")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.message.chat_id) not in AUTHORIZED_USERS:
        await update.message.reply_text("❌ No autorizado.")
        return
    
    stats_msg = get_server_stats()
    await update.message.reply_text(f"📊 *Estadísticas del servidor:*\n\n{stats_msg}", parse_mode="Markdown")

async def logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.message.chat_id) != ADMIN_USER:
        await update.message.reply_text("❌ Solo el administrador puede ver los logs.")
        return
    
    log_content = get_plex_logs(30)  # Últimas 30 líneas
    if len(log_content) > 4000:  # Telegram tiene límite de longitud
        log_content = log_content[-4000:]
    
    await update.message.reply_text(f"📄 *Últimas líneas del log:*\n\n```\n{log_content}\n```", parse_mode="Markdown")

async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.message.chat_id) != ADMIN_USER:
        await update.message.reply_text("❌ Solo el administrador puede reiniciar Plex.")
        return
    
    await update.message.reply_text("🔄 Intentando reiniciar Plex...")
    try:
        result = subprocess.run(
            ["sudo", "systemctl", "restart", "plexmediaserver"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            await update.message.reply_text("✅ Plex reiniciado correctamente")
        else:
            await update.message.reply_text(f"⚠️ Error al reiniciar Plex:\n{result.stderr}")
    except Exception as e:
        await update.message.reply_text(f"🔴 Error grave al reiniciar Plex:\n{e}")

async def errors(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.message.chat_id) not in AUTHORIZED_USERS:
        await update.message.reply_text("❌ No autorizado.")
        return
    
    log_content = get_plex_logs(100)  # Busca en las últimas 100 líneas
    error_lines = [line for line in log_content.split('\n') if "ERROR" in line or "error" in line]
    
    if error_lines:
        error_msg = "⚠️ *Errores recientes en Plex:*\n\n"
        error_msg += "\n".join(error_lines[-10:])  # Muestra los 10 últimos errores
        if len(error_msg) > 4000:
            error_msg = error_msg[-4000:]
        await update.message.reply_text(f"```\n{error_msg}\n```", parse_mode="Markdown")
    else:
        await update.message.reply_text("✅ No se encontraron errores recientes en los logs")

### --- Inicialización del Bot --- ###
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Registro de comandos
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("users", users))
    app.add_handler(CommandHandler("recent", recent))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("logs", logs))
    app.add_handler(CommandHandler("restart", restart))
    app.add_handler(CommandHandler("errors", errors))
    
    # Manejo de errores
    app.add_error_handler(error_handler)
    
    logger.info("Bot iniciado, escuchando comandos...")
    app.run_polling()

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Error mientras manejaba una actualización: {context.error}")
    
    # Notificar al admin sobre errores graves
    if ADMIN_USER:
        tb = "".join(traceback.format_tb(context.error.__traceback__))
        error_msg = (
            f"⚠️ *Error en el bot:*\n"
            f"```\n{context.error}\n```\n"
            f"*Traceback:*\n```\n{tb}\n```"
        )
        await context.bot.send_message(chat_id=ADMIN_USER, text=error_msg, parse_mode="Markdown")

if __name__ == "__main__":
    import traceback
    main()