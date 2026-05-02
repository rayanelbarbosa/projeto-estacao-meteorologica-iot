#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <DHT.h>

// ===================== CONFIGURAÇÕES =====================
// ⚠️ Substitua com suas credenciais antes de rodar
const char* WIFI_SSID     = "Wokwi-GUEST";              // No Wokwi use sempre este SSID
const char* WIFI_PASSWORD = "";                           // No Wokwi a senha é vazia
const char* MQTT_HOST     = "SEU_CLUSTER.hivemq.cloud";  // Cluster URL do HiveMQ Cloud
const int   MQTT_PORT     = 8883;                         // Porta TLS — não altere
const char* MQTT_USER     = "SEU_USUARIO_HIVEMQ";        // Usuário criado no HiveMQ
const char* MQTT_PASS     = "SUA_SENHA_HIVEMQ";          // Senha do HiveMQ
const char* MQTT_CLIENT   = "estacao-esp32-001";
const char* OWM_KEY       = "SUA_API_KEY_OPENWEATHERMAP"; // API Key do OpenWeatherMap
const char* OWM_CITY      = "Suzano,BR";                  // Cidade para dados reais

// ===================== TÓPICOS MQTT =====================
const char* TOPIC_TEMP     = "estacao/temperatura";
const char* TOPIC_UMID     = "estacao/umidade";
const char* TOPIC_LUZ      = "estacao/luminosidade";
const char* TOPIC_GAS      = "estacao/gas";
const char* TOPIC_PREV     = "estacao/previsao";
const char* TOPIC_CONFORT  = "estacao/conforto";
const char* TOPIC_API_TEMP = "estacao/api/temperatura";
const char* TOPIC_API_UMID = "estacao/api/umidade";
const char* TOPIC_API_PRES = "estacao/api/pressao";
const char* TOPIC_API_DESC = "estacao/api/descricao";
const char* TOPIC_API_VENT = "estacao/api/vento";
const char* TOPIC_API_SENS = "estacao/api/sensacao";

// ===================== PINOS =====================
#define DHTPIN    4
#define DHTTYPE   DHT22
#define LDR_PIN   34
#define GAS_PIN   35
#define BTN_PIN   15

// ===================== OLED =====================
#define SCREEN_WIDTH  128
#define SCREEN_HEIGHT 64
#define OLED_ADDR     0x3C

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);
DHT dht(DHTPIN, DHTTYPE);
WiFiClientSecure espClient;
PubSubClient mqtt(espClient);

// ===================== VARIÁVEIS GLOBAIS =====================
float temperatura = 25.0, umidade = 60.0, indiceConforto = 0;
float apiTemperatura = 0, apiUmidade = 0, apiPressao = 0;
float apiVento = 0, apiSensacao = 0;
long  apiDt = 0, apiSunrise = 0, apiSunset = 0;
int   luminosidade = 0, qualidadeAr = 0;
String previsao     = "Carregando...";
String confortoStr  = "---";
String apiDescricao = "---";
int    tela = 0;
unsigned long ultimaLeitura = 0, ultimaMQTT = 0, ultimaPrevisao = 0;
bool btnAnterior = HIGH;

// ===================== SETUP =====================
void setup() {
  Serial.begin(115200);
  delay(3000);
  Serial.println("Iniciando...");

  pinMode(BTN_PIN, INPUT_PULLUP);
  dht.begin();

  Wire.begin(21, 22);
  Serial.println("Wire OK");

  if (!display.begin(SSD1306_SWITCHCAPVCC, OLED_ADDR)) {
    Serial.println("OLED falhou!");
    while (true);
  }
  Serial.println("OLED OK!");

  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(WHITE);
  display.setCursor(0, 0);
  display.println("OLED funcionando!");
  display.display();
  delay(2000);

  telaBooting("Conectando WiFi...");
  conectarWiFi();

  espClient.setInsecure();
  mqtt.setServer(MQTT_HOST, MQTT_PORT);
  mqtt.setBufferSize(512);

  telaBooting("Conectando MQTT...");
  conectarMQTT();

  telaBooting("Buscando previsao...");
  buscarPrevisao();
}

// ===================== LOOP =====================
void loop() {
  if (!mqtt.connected()) conectarMQTT();
  mqtt.loop();

  bool btnAtual = digitalRead(BTN_PIN);
  if (btnAtual == LOW && btnAnterior == HIGH) {
    tela = (tela + 1) % 4;
    delay(50);
  }
  btnAnterior = btnAtual;

  if (millis() - ultimaLeitura > 3000) {
    ultimaLeitura = millis();
    lerSensores();
    exibirTela();
  }
  if (millis() - ultimaMQTT > 10000) {
    ultimaMQTT = millis();
    enviarMQTT();
  }
  if (millis() - ultimaPrevisao > 300000) {
    ultimaPrevisao = millis();
    buscarPrevisao();
  }
}

// ===================== LEITURA DE SENSORES =====================
void lerSensores() {
  float t = NAN, h = NAN;
  for (int i = 0; i < 5 && (isnan(t) || isnan(h)); i++) {
    t = dht.readTemperature();
    h = dht.readHumidity();
    if (isnan(t) || isnan(h)) delay(300);
  }
  if (!isnan(t) && !isnan(h)) {
    temperatura = t; umidade = h;
    Serial.print("DHT OK: T="); Serial.print(t);
    Serial.print(" H="); Serial.println(h);
  }
  indiceConforto = calcularConforto(temperatura, umidade);
  confortoStr    = classificarConforto(indiceConforto);
  int ldrRaw = analogRead(LDR_PIN);
  luminosidade = map(ldrRaw, 0, 4095, 0, 100);
  int gasRaw = analogRead(GAS_PIN);
  qualidadeAr  = map(gasRaw, 0, 4095, 0, 100);
}

// ===================== CONFORTO TÉRMICO (Fórmula de Rothfusz) =====================
float calcularConforto(float t, float h) {
  return -8.78469475556
    + 1.61139411 * t + 2.33854883889 * h
    - 0.14611605 * t * h - 0.012308094 * t * t
    - 0.0164248277778 * h * h + 0.002211732 * t * t * h
    + 0.00072546 * t * h * h - 0.000003582 * t * t * h * h;
}

String classificarConforto(float ic) {
  if (ic < 26) return "Confortavel";
  if (ic < 28) return "Atencao";
  if (ic < 30) return "Desconforto";
  if (ic < 35) return "Muito Quente";
  return "Perigo!";
}

// ===================== TELAS OLED =====================
void telaBooting(String msg) {
  display.clearDisplay();
  display.setCursor(0, 20);
  display.setTextSize(1);
  display.println("  Estacao Meteoro.");
  display.println("  Suzano, SP - BR");
  display.println("  " + msg);
  display.display();
}

void exibirTela() {
  display.clearDisplay();
  switch (tela) {
    case 0: telaTempUmidade(); break;
    case 1: telaLuzGas();      break;
    case 2: telaConforto();    break;
    case 3: telaPrevisao();    break;
  }
  display.display();
}

void telaTempUmidade() {
  display.setTextSize(1); display.setCursor(0, 0);
  display.println("== TEMP & UMIDADE ==");
  display.setTextSize(2); display.setCursor(0, 16);
  display.print(temperatura, 1); display.print((char)247); display.println("C");
  display.setCursor(0, 38); display.print(umidade, 1); display.println("%");
  if (temperatura > 35 || temperatura < 5) {
    display.setTextSize(1); display.setCursor(0, 57);
    display.print("! TEMP EXTREMA !");
  }
}

void telaLuzGas() {
  display.setTextSize(1); display.setCursor(0, 0);
  display.println("== LUZ & AR ========");
  display.setCursor(0, 16);
  display.print("Luz:  "); display.print(luminosidade); display.println("%");
  exibirBarra(luminosidade, 28);
  display.setCursor(0, 38);
  display.print("Gas:  "); display.print(qualidadeAr); display.println("%");
  exibirBarra(qualidadeAr, 50);
  if (qualidadeAr > 70) { display.setCursor(0, 57); display.print("! AR CONTAMINADO !"); }
}

void exibirBarra(int valor, int y) {
  display.drawRect(0, y, 100, 8, WHITE);
  display.fillRect(0, y, map(valor, 0, 100, 0, 100), 8, WHITE);
}

void telaConforto() {
  display.setTextSize(1); display.setCursor(0, 0);
  display.println("== CONFORTO TERMICO=");
  display.setCursor(0, 16);
  display.print("Ind. Calor: "); display.print(indiceConforto, 1); display.println("C");
  display.setCursor(0, 32);
  display.print("Status: "); display.println(confortoStr);
  display.setCursor(0, 48);
  display.print("T:"); display.print(temperatura, 1);
  display.print(" H:"); display.print(umidade, 0); display.print("%");
}

void telaPrevisao() {
  display.setTextSize(1); display.setCursor(0, 0);
  display.println("== PREVISAO TEMPO ==");
  display.setCursor(0, 16); display.println("Suzano, SP - BR");
  display.setCursor(0, 32); display.println(previsao);
  display.setCursor(0, 48);
  display.print("T:"); display.print(temperatura, 1);
  display.print("C H:"); display.print(umidade, 0); display.print("%");
}

// ===================== WIFI =====================
void conectarWiFi() {
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  int t = 0;
  while (WiFi.status() != WL_CONNECTED && t < 20) {
    delay(500); Serial.print("."); t++;
  }
  Serial.println(WiFi.status() == WL_CONNECTED ? "\nWiFi OK!" : "\nWiFi FALHOU");
}

// ===================== MQTT =====================
void conectarMQTT() {
  int tentativas = 0;
  while (!mqtt.connected() && tentativas < 5) {
    Serial.print("Conectando MQTT... ");
    if (mqtt.connect(MQTT_CLIENT, MQTT_USER, MQTT_PASS)) {
      Serial.println("OK!");
    } else {
      Serial.print("Falhou rc="); Serial.println(mqtt.state());
      delay(3000); tentativas++;
    }
  }
}

void enviarMQTT() {
  mqtt.publish(TOPIC_TEMP,    String(temperatura, 2).c_str());
  mqtt.publish(TOPIC_UMID,    String(umidade, 2).c_str());
  char buf[16];
  itoa(luminosidade, buf, 10); mqtt.publish(TOPIC_LUZ, buf);
  itoa(qualidadeAr,  buf, 10); mqtt.publish(TOPIC_GAS, buf);
  mqtt.publish(TOPIC_PREV,    previsao.c_str());
  mqtt.publish(TOPIC_CONFORT, confortoStr.c_str());
  Serial.println("=============================");
  Serial.println("DADOS ENVIADOS VIA MQTT");
  Serial.println("--- SENSOR (Simulacao) ---");
  Serial.print("Temperatura: "); Serial.print(temperatura); Serial.println(" C");
  Serial.print("Umidade:     "); Serial.print(umidade);     Serial.println(" %");
  Serial.print("Luminosidade:"); Serial.print(luminosidade);Serial.println(" %");
  Serial.print("Qualidade Ar:"); Serial.print(qualidadeAr); Serial.println(" %");
  Serial.print("Conforto:    "); Serial.println(confortoStr);
  Serial.println("--- API (Suzano Real) ---");
  Serial.print("Temp Real:   "); Serial.print(apiTemperatura); Serial.println(" C");
  Serial.print("Sensacao:    "); Serial.print(apiSensacao);    Serial.println(" C");
  Serial.print("Umid Real:   "); Serial.print(apiUmidade);     Serial.println(" %");
  Serial.print("Pressao:     "); Serial.print(apiPressao);     Serial.println(" hPa");
  Serial.print("Vento:       "); Serial.print(apiVento);       Serial.println(" km/h");
  Serial.print("Descricao:   "); Serial.println(apiDescricao);
  Serial.print("Previsao:    "); Serial.println(previsao);
  Serial.print("E dia:       "); Serial.println((apiDt >= apiSunrise && apiDt <= apiSunset) ? "Sim" : "Nao");
  Serial.println("=============================");
}

// ===================== API OPENWEATHERMAP =====================
void buscarPrevisao() {
  if (WiFi.status() != WL_CONNECTED) return;
  HTTPClient http;
  String url = "http://api.openweathermap.org/data/2.5/weather?q=";
  url += OWM_CITY; url += "&appid="; url += OWM_KEY; url += "&units=metric&lang=pt";
  http.begin(url);
  int code = http.GET();
  if (code == 200) {
    String payload = http.getString();
    DynamicJsonDocument doc(2048);
    deserializeJson(doc, payload);
    apiPressao     = doc["main"]["pressure"].as<float>();
    apiTemperatura = doc["main"]["temp"].as<float>();
    apiUmidade     = doc["main"]["humidity"].as<float>();
    apiSensacao    = doc["main"]["feels_like"].as<float>();
    apiVento       = doc["wind"]["speed"].as<float>() * 3.6;
    apiDescricao   = doc["weather"][0]["description"].as<String>();
    apiDt          = doc["dt"].as<long>();
    apiSunrise     = doc["sys"]["sunrise"].as<long>();
    apiSunset      = doc["sys"]["sunset"].as<long>();
    previsao = calcularPrevisao(apiPressao, apiTemperatura);
    mqtt.publish(TOPIC_API_TEMP, String(apiTemperatura, 1).c_str());
    mqtt.publish(TOPIC_API_UMID, String(apiUmidade, 1).c_str());
    mqtt.publish(TOPIC_API_PRES, String(apiPressao, 0).c_str());
    mqtt.publish(TOPIC_API_DESC, apiDescricao.c_str());
    mqtt.publish(TOPIC_API_VENT, String(apiVento, 1).c_str());
    mqtt.publish(TOPIC_API_SENS, String(apiSensacao, 1).c_str());
    Serial.print("API OK! Previsao: "); Serial.println(previsao);
  } else {
    previsao = "Sem dados";
  }
  http.end();
}

// ===================== PREVISÃO DO TEMPO =====================
// Baseada em pressão atmosférica + temperatura sensor vs API + identificação dia/noite
String calcularPrevisao(float pressao, float tempAPI) {
  float diffTemp = abs(temperatura - tempAPI);
  bool  eDia     = (apiDt >= apiSunrise && apiDt <= apiSunset);
  Serial.print("E dia: "); Serial.println(eDia ? "Sim" : "Nao");
  if (pressao >= 1020) {
    if (diffTemp < 3) return eDia ? "Ensolarado"    : "Noite Clara";
    return                   eDia ? "Parc. nublado" : "Noite Nublada";
  } else if (pressao >= 1005) {
    if (umidade > 70) return "Possivel chuva";
    return "Nublado";
  } else if (pressao >= 990) {
    if (umidade > 75) return "Chuva provavel";
    return "Tempo fechado";
  } else {
    return "Tempestade";
  }
}
