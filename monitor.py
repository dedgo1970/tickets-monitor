# Último Script ejecutandose correctamente
# 15/04/2026

from playwright.sync_api import sync_playwright
import requests
import time
import random
import smtplib
from datetime import datetime
from email.mime.text import MIMEText


# =========================
# EVENTOS A MONITOREAR
# =========================
URLS = {
    "07 Mayo": "https://www.ticketmaster.com.mx/event/1400642AA1B78268",
    "09 Mayo": "https://www.ticketmaster.com.mx/event/1400642AA32C84D5",
    "10 Mayo": "https://www.ticketmaster.com.mx/event/1400642AA32D84D7"
}

# =========================
# MODO DE PRUEBA
# =========================
TEST_MODE = False
TEST_AVAILABLE_URL = "https://www.ticketmaster.com.mx/event/3D0064428F9E0DDA"

# =========================
# TELEGRAM
# =========================
TELEGRAM_TOKEN = "TELEGRAM_TOKEN"
TELEGRAM_CHAT_ID = "TELEGRAM_CHAT_ID"

telegram_session = requests.Session()

# =========================
# GMAIL SMTP
# =========================
EMAIL_SENDER = "EMAIL_SENDER"
EMAIL_PASSWORD = "EMAIL_PASSWORD"

EMAIL_RECEIVERS = [
    "michhhh2809@gmail.com",
    "25030481M@itesa.edu.mx"
]

# =========================
# ESTADO
# =========================
last_status = {date: False for date in URLS}


# =========================
# TELEGRAM ALERT (ROBUSTO)
# =========================
def send_telegram_alert(date, url, persistent=False):
    title = (
        "🔥 AÚN HAY BOLETOS DISPONIBLES"
        if persistent
        else "🔥 BOLETOS DISPONIBLES"
    )

    message = (
        f"{title}\n\n"
        f"📅 Fecha: {date}\n"
        f"🕒 Hora: {datetime.now().strftime('%H:%M:%S')}\n"
        f"🎟️ Link: {url}"
    )

    for attempt in range(3):
        try:
            response = telegram_session.post(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                json={
                    "chat_id": TELEGRAM_CHAT_ID,
                    "text": message
                },
                timeout=15
            )

            response.raise_for_status()
            print(f"📲 Telegram enviado para {date}")
            return

        except Exception as e:
            print(f"⚠️ Error Telegram intento {attempt+1}: {e}")
            time.sleep(3)


# =========================
# EMAIL ALERT
# =========================
def send_email_alert(date, url, persistent=False):
    subject = (
        "🔥 AÚN HAY BOLETOS DISPONIBLES"
        if persistent
        else "🔥 BOLETOS DISPONIBLES"
    )

    body = (
        f"{subject}\n\n"
        f"Fecha: {date}\n"
        f"Hora: {datetime.now().strftime('%H:%M:%S')}\n"
        f"Link: {url}"
    )

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_SENDER
    msg["To"] = ", ".join(EMAIL_RECEIVERS)

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)

            server.sendmail(
                EMAIL_SENDER,
                EMAIL_RECEIVERS,
                msg.as_string()
            )

        print(f"📧 Correo enviado a {len(EMAIL_RECEIVERS)} destinatarios para {date}")

    except Exception as e:
        print(f"⚠️ Error enviando correo: {e}")


# =========================
# CHECK DISPONIBILIDAD
# =========================
def check_availability(page, url, retries=2):
    for attempt in range(retries):
        try:
            response = page.goto(url, wait_until="networkidle")
            page.wait_for_timeout(4000)

            # Si la página no cargó bien, reintentar
            if response is None or response.status >= 400:
                print(f"⚠️ Status {response.status if response else 'None'}, intento {attempt + 1}/{retries}...")
                if attempt < retries - 1:
                    time.sleep(4)
                continue

            # Señal principal: el contador h2
            no_results = page.locator("h2", has_text="Sin resultados")
            has_results = page.locator("h2", has_text="Resultados para")

            if no_results.count() > 0:
                return False
            if has_results.count() > 0:
                return True

            # Estado ambiguo: reintentar
            print(f"⚠️ Estado ambiguo, intento {attempt + 1}/{retries}...")
            if attempt < retries - 1:
                time.sleep(4)

        except Exception as e:
            print(f"⚠️ Intento {attempt + 1}/{retries} fallido: {e}")
            if attempt < retries - 1:
                time.sleep(4)

    print(f"⚠️ Todos los intentos fallaron, saltando...")
    return None


# =========================
# MAIN LOOP
# =========================
with sync_playwright() as p:
    #context = p.chromium.launch_persistent_context(
        #user_data_dir="ticketmaster_profile",
        #headless=True,
        #user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        #locale="es-MX",
        #timezone_id="America/Mexico_City"
    #)
    context = p.chromium.launch_persistent_context(
        user_data_dir="ticketmaster_profile",
        headless=True,
        proxy={
            "server": "http://31.59.20.176:6754",
            "username": "modsedkf",
            "password": "5prxrbs8ik1d"
        },
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        locale="es-MX",
        timezone_id="America/Mexico_City"
    )

    
    page = context.new_page()

    while True:
        print(f"\n🕐 {datetime.now().strftime('%H:%M:%S - %d de %B')}")
        print("Revisando disponibilidad...")

        simulated_urls = URLS.copy()

        if TEST_MODE:
            if random.choice([True, False]):
                selected_date = random.choice(list(simulated_urls.keys()))
                simulated_urls[selected_date] = TEST_AVAILABLE_URL
                print(f"🧪 Simulación activa: {selected_date} tendrá boletos")

        items = list(simulated_urls.items())
        random.shuffle(items)

        for date, url in items:
            try:
                available = check_availability(page, url)

                if available:
                    if not last_status[date]:
                        print(f"🔥 NUEVA DISPONIBILIDAD DETECTADA en {date}")
                        send_telegram_alert(date, url, persistent=False)
                        send_email_alert(date, url, persistent=False)
                    else:
                        print(f"🔥 Disponibles en {date}")
                        send_telegram_alert(date, url, persistent=True)
                        send_email_alert(date, url, persistent=True)

                else:
                    if last_status[date]:
                        print(f"ℹ️ Se agotaron nuevamente los boletos en {date}")
                    else:
                        print(f"❌ Sin boletos en {date}")

                last_status[date] = available

            except Exception as e:
                print(f"Error en {date}: {e}")

        wait_time = random.randint(40, 60)
        print(f"Esperando {wait_time} segundos...\n")
        time.sleep(wait_time)
