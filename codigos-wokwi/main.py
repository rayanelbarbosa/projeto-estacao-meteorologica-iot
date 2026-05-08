import network, time, dht, ujson, urequests, ussl
import usocket as socket
from machine import Pin, ADC, I2C
from umqtt.simple import MQTTClient
import ssd1306

# ===================== CONFIGURAÇÕES =====================
WIFI_SSID     = "Wokwi-GUEST"
WIFI_PASSWORD = ""
MQTT_HOST     = "SEU_CLUSTER.hivemq.cloud"       # ← Substitua pelo seu cluster HiveMQ
MQTT_PORT     = 8883
MQTT_USER     = "SEU_USUARIO_HIVEMQ"              # ← Substitua pelo seu usuário
MQTT_PASS     = "SUA_SENHA_HIVEMQ"                # ← Substitua pela sua senha
MQTT_CLIENT   = "estacao-mp-003"
OWM_KEY       = "SUA_API_KEY_OPENWEATHERMAP"      # ← Substitua pela sua API Key
OWM_CITY      = "Suzano,BR"

# ---- Etapa 2: Sheets e Email ----
SHEETS_URL    = "http://script.google.com/macros/s/SUA_URL_APPS_SCRIPT/exec"  # ← Substitua
EMAIL_URL     = "https://script.googleusercontent.com/macros/echo?user_content_key=SUA_URL_FINAL"  # ← Substitua pela URL final após redirecionamento
EMAIL_DEST    = "email_do_professor@dominio.com"  # ← Email do destinatário
EMAIL_FROM    = "SEU_EMAIL@gmail.com"             # ← Seu Gmail

# ===================== TÓPICOS MQTT =====================
TOPIC_TEMP     = b"estacao/temperatura"
TOPIC_UMID     = b"estacao/umidade"
TOPIC_LUZ      = b"estacao/luminosidade"
TOPIC_GAS      = b"estacao/gas"
TOPIC_PREV     = b"estacao/previsao"
TOPIC_CONFORT  = b"estacao/conforto"
TOPIC_API_TEMP = b"estacao/api/temperatura"
TOPIC_API_UMID = b"estacao/api/umidade"
TOPIC_API_PRES = b"estacao/api/pressao"
TOPIC_API_DESC = b"estacao/api/descricao"
TOPIC_API_VENT = b"estacao/api/vento"
TOPIC_API_SENS = b"estacao/api/sensacao"

# ===================== PINOS =====================
DHT_PIN = Pin(4)
LDR_PIN = ADC(Pin(34))
GAS_PIN = ADC(Pin(35))
BTN_PIN = Pin(15, Pin.IN, Pin.PULL_UP)
LDR_PIN.atten(ADC.ATTN_11DB)
GAS_PIN.atten(ADC.ATTN_11DB)

# ===================== OLED =====================
i2c = I2C(0, scl=Pin(22), sda=Pin(21))
print("I2C scan:", i2c.scan())
oled = ssd1306.SSD1306_I2C(128, 64, i2c)
print("OLED OK!")

# ===================== VARIÁVEIS =====================
temperatura      = 25.0
umidade          = 60.0
luminosidade     = 0
qualidade_ar     = 0
conforto_str     = "---"
previsao         = "Carregando..."
api_temp         = 0.0
api_umid         = 0.0
api_pressao      = 0.0
api_vento        = 0.0
api_sensacao     = 0.0
api_descricao    = "---"
api_dt           = 0
api_sunrise      = 0
api_sunset       = 0
tela             = 0
btn_anterior     = 1
mqtt_client      = None
ultimo_print_dht = 0

# Acumuladores para média diária
leituras_temp = []
leituras_umid = []
ultimo_email  = -1

# Intervalos
INTERVALO_SHEETS_MS = 30 * 1000   # Sheets a cada 30s
INTERVALO_EMAIL_MS  = 45 * 1000   # Email aos 45s (após o Sheets)

# ===================== OLED HELPERS =====================
def oled_show(l1="", l2="", l3="", l4="", l5="", l6=""):
    oled.fill(0)
    if l1: oled.text(l1[:21], 0, 0)
    if l2: oled.text(l2[:21], 0, 10)
    if l3: oled.text(l3[:21], 0, 20)
    if l4: oled.text(l4[:21], 0, 30)
    if l5: oled.text(l5[:21], 0, 42)
    if l6: oled.text(l6[:21], 0, 54)
    oled.show()

def oled_booting(msg):
    oled_show("Estacao Meteoro.", "Suzano, SP - BR", msg[:21])

def exibir_tela():
    if tela == 0:
        alerta = "!TEMP EXTREMA!" if temperatura > 35 or temperatura < 5 else ""
        oled_show("== TEMP & UMID ==",
                  "T: {:.1f} C".format(temperatura),
                  "H: {:.1f} %".format(umidade),
                  l5=alerta)
    elif tela == 1:
        alerta = "!AR CONTAMINADO!" if qualidade_ar > 70 else ""
        oled_show("== LUZ & AR ====",
                  "Luz: {}%".format(luminosidade),
                  "Gas: {}%".format(qualidade_ar),
                  l5=alerta)
    elif tela == 2:
        oled_show("== CONFORTO ====",
                  "Status:",
                  conforto_str,
                  "T:{:.1f} H:{:.0f}%".format(temperatura, umidade))
    elif tela == 3:
        oled_show("== PREVISAO ====",
                  "Suzano, SP - BR",
                  previsao,
                  "T:{:.1f} H:{:.0f}%".format(temperatura, umidade))

# ===================== WIFI =====================
def conectar_wifi():
    oled_booting("Conectando WiFi...")
    wlan = network.WLAN(network.STA_IF)
    wlan.active(False)
    time.sleep(1)
    wlan.active(True)
    time.sleep(1)
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)
    tentativas = 0
    while not wlan.isconnected() and tentativas < 40:
        time.sleep(0.5)
        tentativas += 1
        print("WiFi tentativa", tentativas)
    if wlan.isconnected():
        print("WiFi OK! IP:", wlan.ifconfig()[0])
        oled_booting("WiFi OK!")
    else:
        print("WiFi FALHOU - tentando de novo...")
        time.sleep(2)
        conectar_wifi()

# ===================== MQTT =====================
def conectar_mqtt():
    global mqtt_client
    try:
        mqtt_client = MQTTClient(
            MQTT_CLIENT, MQTT_HOST,
            port=MQTT_PORT, user=MQTT_USER, password=MQTT_PASS,
            ssl=True, ssl_params={"server_hostname": MQTT_HOST}
        )
        mqtt_client.connect()
        print("MQTT OK!")
        oled_booting("MQTT OK!")
    except Exception as e:
        print("MQTT falhou:", e)
        mqtt_client = None

def publicar(topico, valor):
    if mqtt_client:
        try:
            mqtt_client.publish(topico, str(valor).encode())
        except Exception as e:
            print("Erro publish:", e)

# ===================== SENSORES =====================
def calcular_conforto(t, h):
    ic = (-8.78469475556 + 1.61139411*t + 2.33854883889*h
        - 0.14611605*t*h - 0.012308094*t*t - 0.0164248277778*h*h
        + 0.002211732*t*t*h + 0.00072546*t*h*h - 0.000003582*t*t*h*h)
    if ic < 26: return "Confortavel"
    if ic < 28: return "Atencao"
    if ic < 30: return "Desconforto"
    if ic < 35: return "Muito Quente"
    return "Perigo!"

def ler_sensores():
    global temperatura, umidade, luminosidade, qualidade_ar, conforto_str
    global leituras_temp, leituras_umid, ultimo_print_dht
    sensor = dht.DHT22(DHT_PIN)
    for _ in range(5):
        try:
            sensor.measure()
            t = sensor.temperature()
            h = sensor.humidity()
            if t is not None and h is not None:
                temperatura = t
                umidade = h
                leituras_temp.append(t)
                leituras_umid.append(h)
                agora = time.ticks_ms()
                if time.ticks_diff(agora, ultimo_print_dht) > 30000:
                    print("DHT OK: T={} H={}".format(t, h))
                    ultimo_print_dht = agora
                break
        except:
            time.sleep(0.3)
    conforto_str = calcular_conforto(temperatura, umidade)
    ldr_raw = LDR_PIN.read()
    luminosidade = int(ldr_raw * 100 / 4095)
    gas_raw = GAS_PIN.read()
    qualidade_ar = int(gas_raw * 100 / 4095)

# ===================== API =====================
def calcular_previsao(pressao):
    e_dia = (api_dt >= api_sunrise and api_dt <= api_sunset)
    diff_temp = abs(temperatura - api_temp)
    if pressao >= 1020:
        if diff_temp < 3: return "Ensolarado" if e_dia else "Noite Clara"
        return "Parc. nublado" if e_dia else "Noite Nublada"
    elif pressao >= 1005:
        if umidade > 70: return "Possivel chuva"
        return "Nublado"
    elif pressao >= 990:
        if umidade > 75: return "Chuva provavel"
        return "Tempo fechado"
    else:
        return "Tempestade"

def buscar_previsao():
    global previsao, api_temp, api_umid, api_pressao
    global api_vento, api_sensacao, api_descricao
    global api_dt, api_sunrise, api_sunset
    url = ("http://api.openweathermap.org/data/2.5/weather?q={}"
           "&appid={}&units=metric&lang=pt").format(OWM_CITY, OWM_KEY)
    try:
        r = urequests.get(url, timeout=10)
        if r.status_code == 200:
            dados = ujson.loads(r.text)
            api_temp      = dados["main"]["temp"]
            api_umid      = dados["main"]["humidity"]
            api_pressao   = dados["main"]["pressure"]
            api_sensacao  = dados["main"]["feels_like"]
            api_vento     = dados["wind"]["speed"] * 3.6
            api_descricao = dados["weather"][0]["description"]
            api_dt        = dados["dt"]
            api_sunrise   = dados["sys"]["sunrise"]
            api_sunset    = dados["sys"]["sunset"]
            previsao      = calcular_previsao(api_pressao)
            publicar(TOPIC_API_TEMP, "{:.1f}".format(api_temp))
            publicar(TOPIC_API_UMID, "{:.1f}".format(api_umid))
            publicar(TOPIC_API_PRES, "{:.0f}".format(api_pressao))
            publicar(TOPIC_API_VENT, "{:.1f}".format(api_vento))
            publicar(TOPIC_API_SENS, "{:.1f}".format(api_sensacao))
            publicar(TOPIC_API_DESC, api_descricao)
            print("API OK! Previsao:", previsao)
        r.close()
    except Exception as e:
        print("Erro API:", e)
        previsao = "Sem dados"

# ===================== GOOGLE SHEETS (Etapa 2) =====================
def salvar_sheets(dt_str, temp, hum):
    """Envia leitura para Google Sheets via Apps Script (HTTP GET)"""
    try:
        url = "{}?datetime={}&temp={:.2f}&hum={:.2f}".format(
            SHEETS_URL,
            dt_str.replace(" ", "%20").replace("/", "%2F").replace(":", "%3A"),
            temp, hum
        )
        print("Salvando Sheets...")
        r = urequests.get(url, timeout=15)
        print("Sheets resp:", r.text[:80])
        r.close()
        oled_booting("Sheets: OK!")
    except Exception as e:
        print("Erro Sheets:", e)
        oled_booting("Sheets: ERRO")

# ===================== EMAIL (Etapa 2) =====================
def enviar_email(data_ref, media_temp, media_umid, qtd_leituras):
    """Envia relatório diário via Google Apps Script"""
    print("Enviando email via Apps Script...")
    oled_booting("Enviando email...")
    try:
        url = "{}&acao=email&data={}&temp={:.2f}&hum={:.2f}&qtd={}".format(
            EMAIL_URL,
            data_ref.replace("/", "%2F"),
            media_temp, media_umid, qtd_leituras
        )
        r = urequests.get(url, timeout=15)
        print("Email resp:", r.text[:80])
        r.close()
        print("Email enviado com sucesso!")
        oled_booting("Email: OK!")
        return True
    except Exception as e:
        print("Erro email:", e)
        oled_booting("Email: ERRO")
        return False

# ===================== ENVIO MQTT =====================
def enviar_mqtt():
    publicar(TOPIC_TEMP,    "{:.2f}".format(temperatura))
    publicar(TOPIC_UMID,    "{:.2f}".format(umidade))
    publicar(TOPIC_LUZ,     str(luminosidade))
    publicar(TOPIC_GAS,     str(qualidade_ar))
    publicar(TOPIC_PREV,    previsao)
    publicar(TOPIC_CONFORT, conforto_str)
    print("DADOS ENVIADOS VIA MQTT | T={:.1f} H={:.1f}".format(temperatura, umidade))

# ===================== DATA/HORA SIMULADA =====================
def get_datetime_str(ticks_inicio, ticks_agora):
    """Data/hora simulada — Wokwi não tem RTC real"""
    segundos = time.ticks_diff(ticks_agora, ticks_inicio) // 1000
    h = (10 + segundos // 3600) % 24
    m = (segundos % 3600) // 60
    s = segundos % 60
    return "08/05/2026 {:02d}:{:02d}:{:02d}".format(h, m, s)

# ===================== INICIALIZAÇÃO =====================
oled_show("Iniciando...", "Estacao Meteoro.", "Suzano SP - BR")
time.sleep(1)
conectar_wifi()
time.sleep(1)
conectar_mqtt()
time.sleep(1)
buscar_previsao()

ticks_inicio    = time.ticks_ms()
ultimo_leitura  = time.ticks_ms()
ultimo_mqtt     = time.ticks_ms()
ultimo_previsao = time.ticks_ms()
ultimo_sheets   = time.ticks_ms()

print("Sistema iniciado! Aguardando ciclos...")

# ===================== LOOP PRINCIPAL =====================
while True:
    agora = time.ticks_ms()

    # Botão — alterna tela do OLED
    btn_atual = BTN_PIN.value()
    if btn_atual == 0 and btn_anterior == 1:
        tela = (tela + 1) % 4
        time.sleep_ms(50)
    btn_anterior = btn_atual

    # Leitura dos sensores a cada 3s
    if time.ticks_diff(agora, ultimo_leitura) > 3000:
        ultimo_leitura = agora
        ler_sensores()
        exibir_tela()

    # MQTT a cada 10s
    if time.ticks_diff(agora, ultimo_mqtt) > 10000:
        ultimo_mqtt = agora
        enviar_mqtt()

    # API OpenWeatherMap a cada 5min
    if time.ticks_diff(agora, ultimo_previsao) > 300000:
        ultimo_previsao = agora
        buscar_previsao()

    # Google Sheets a cada 30s
    if time.ticks_diff(agora, ultimo_sheets) > INTERVALO_SHEETS_MS:
        ultimo_sheets = agora
        dt_str = get_datetime_str(ticks_inicio, agora)
        salvar_sheets(dt_str, temperatura, umidade)

    # Email aos 45s e depois a cada 45s
    if time.ticks_diff(agora, ticks_inicio) > INTERVALO_EMAIL_MS:
        if ultimo_email == -1 or time.ticks_diff(agora, ultimo_email) > INTERVALO_EMAIL_MS:
            if len(leituras_temp) > 0:
                media_t = sum(leituras_temp) / len(leituras_temp)
                media_h = sum(leituras_umid) / len(leituras_umid)
                qtd = len(leituras_temp)
                enviou = enviar_email("08/05/2026", media_t, media_h, qtd)
                if enviou:
                    ultimo_email = agora
                    leituras_temp = []
                    leituras_umid = []

    time.sleep_ms(100)