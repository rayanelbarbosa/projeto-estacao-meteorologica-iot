import network
import time
import dht
import ujson
import urequests
from machine import Pin, ADC, I2C
from umqtt.simple import MQTTClient
import ssd1306

# ===================== CONFIGURAÇÕES =====================
WIFI_SSID     = "Wokwi-GUEST" # No Wokwi use sempre este SSID
WIFI_PASSWORD = "" # No Wokwi a senha é sempre vazia, mesmo que o roteador virtual mostre uma senha diferente
MQTT_HOST     = "SEU_CLUSTER.hivemq.cloud" # Substitua pelo host do seu cluster HiveMQ Cloud
MQTT_PORT     = 8883 # Porta TLS — não altere
MQTT_USER     = "SEU_USUARIO_HIVEMQ" # Substitua pelo seu usuário do HiveMQ Cloud
MQTT_PASS     = "SUA_SENHA_HIVEMQ" # Substitua pela sua senha do HiveMQ Cloud
MQTT_CLIENT   = "estacao-mp-003"
OWM_KEY       = "SUA_API_KEY_OPENWEATHERMAP" # Substitua pela sua API Key do OpenWeatherMap
OWM_CITY      = "Suzano,BR" # Cidade para dados reais


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
temperatura   = 25.0
umidade       = 60.0
luminosidade  = 0
qualidade_ar  = 0
conforto_str  = "---"
previsao      = "Carregando..."
api_temp      = 0.0
api_umid      = 0.0
api_pressao   = 0.0
api_vento     = 0.0
api_sensacao  = 0.0
api_descricao = "---"
api_dt        = 0
api_sunrise   = 0
api_sunset    = 0
tela          = 0
btn_anterior  = 1
mqtt_client   = None

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
    print("Conectando WiFi...")
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)
    tentativas = 0
    while not wlan.isconnected() and tentativas < 20:
        time.sleep(0.5)
        print(".", end="")
        tentativas += 1
    if wlan.isconnected():
        print("\nWiFi OK! IP:", wlan.ifconfig()[0])
        oled_booting("WiFi OK!")
    else:
        print("\nWiFi FALHOU")

# ===================== MQTT =====================
def conectar_mqtt():
    global mqtt_client
    oled_booting("Conectando MQTT...")
    print("Conectando MQTT...")
    try:
        mqtt_client = MQTTClient(
            MQTT_CLIENT, MQTT_HOST,
            port=MQTT_PORT,
            user=MQTT_USER,
            password=MQTT_PASS,
            ssl=True,
            ssl_params={"server_hostname": MQTT_HOST}
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
    ic = (-8.78469475556
        + 1.61139411 * t + 2.33854883889 * h
        - 0.14611605 * t * h - 0.012308094 * t * t
        - 0.0164248277778 * h * h + 0.002211732 * t * t * h
        + 0.00072546 * t * h * h - 0.000003582 * t * t * h * h)
    if ic < 26: return "Confortavel"
    if ic < 28: return "Atencao"
    if ic < 30: return "Desconforto"
    if ic < 35: return "Muito Quente"
    return "Perigo!"

def ler_sensores():
    global temperatura, umidade, luminosidade, qualidade_ar, conforto_str
    sensor = dht.DHT22(DHT_PIN)
    for _ in range(5):
        try:
            sensor.measure()
            t = sensor.temperature()
            h = sensor.humidity()
            if t is not None and h is not None:
                temperatura = t
                umidade = h
                print("DHT OK: T={} H={}".format(t, h))
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
    print("E dia:", "Sim" if e_dia else "Nao")
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
    oled_booting("Buscando previsao...")
    print("Buscando previsao...")
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

# ===================== ENVIO MQTT =====================
def enviar_mqtt():
    publicar(TOPIC_TEMP,    "{:.2f}".format(temperatura))
    publicar(TOPIC_UMID,    "{:.2f}".format(umidade))
    publicar(TOPIC_LUZ,     str(luminosidade))
    publicar(TOPIC_GAS,     str(qualidade_ar))
    publicar(TOPIC_PREV,    previsao)
    publicar(TOPIC_CONFORT, conforto_str)
    print("=============================")
    print("DADOS ENVIADOS VIA MQTT")
    print("--- SENSOR (Simulacao) ---")
    print("Temperatura: {:.2f} C".format(temperatura))
    print("Umidade:     {:.2f} %".format(umidade))
    print("Luminosidade:{} %".format(luminosidade))
    print("Qualidade Ar:{} %".format(qualidade_ar))
    print("Conforto:    ", conforto_str)
    print("--- API (Suzano Real) ---")
    print("Temp Real:   {:.2f} C".format(api_temp))
    print("Sensacao:    {:.2f} C".format(api_sensacao))
    print("Umid Real:   {:.1f} %".format(api_umid))
    print("Pressao:     {:.0f} hPa".format(api_pressao))
    print("Vento:       {:.1f} km/h".format(api_vento))
    print("Descricao:   ", api_descricao)
    print("Previsao:    ", previsao)
    print("=============================")

# ===================== INICIALIZAÇÃO =====================
oled_show("Iniciando...", "Estacao Meteoro.", "Suzano SP - BR")
time.sleep(1)

conectar_wifi()
time.sleep(1)
conectar_mqtt()
time.sleep(1)
buscar_previsao()

ultimo_leitura  = time.ticks_ms()
ultimo_mqtt     = time.ticks_ms()
ultimo_previsao = time.ticks_ms()

# ===================== LOOP =====================
while True:
    agora = time.ticks_ms()

    btn_atual = BTN_PIN.value()
    if btn_atual == 0 and btn_anterior == 1:
        tela = (tela + 1) % 4
        time.sleep_ms(50)
    btn_anterior = btn_atual

    if time.ticks_diff(agora, ultimo_leitura) > 3000:
        ultimo_leitura = agora
        ler_sensores()
        exibir_tela()

    if time.ticks_diff(agora, ultimo_mqtt) > 10000:
        ultimo_mqtt = agora
        enviar_mqtt()

    if time.ticks_diff(agora, ultimo_previsao) > 300000:
        ultimo_previsao = agora
        buscar_previsao()

    time.sleep_ms(100)