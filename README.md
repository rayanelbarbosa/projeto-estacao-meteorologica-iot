# 🌦️ Estação Meteorológica Virtual com ESP32

Projeto prático da disciplina de **Internet das Coisas (IoT)**  
Universidade de Mogi das Cruzes — 2026

---

## 📋 Descrição

Estação meteorológica simulada no **Wokwi** com ESP32, sensores DHT22, LDR e MQ-2, display OLED SSD1306 com 4 telas alternáveis via botão, comunicação MQTT via **HiveMQ Cloud**, dashboard **Node-RED** com dados reais da API **OpenWeatherMap** para Suzano/SP, persistência automática de dados no **Google Sheets** e envio automatizado de **relatório diário por email** via Google Apps Script.

## 🏗️ Arquitetura

```
Wokwi (ESP32 MicroPython)
  ├── MQTT → HiveMQ Cloud → Node-RED → Dashboard
  ├── HTTP → Google Apps Script → Google Sheets  (Etapa 2)
  └── HTTP → Google Apps Script → Gmail          (Etapa 2)
        ↑
  OpenWeatherMap API (dados reais Suzano/BR)
```

## 📁 Estrutura do Repositório

```
📦 estacao-meteorologica-iot
 ┣ 📂 codigos-wokwi
 ┃ ┣ 📄 main.py               → Firmware ESP32 MicroPython (Etapas 1 e 2)
 ┃ ┣ 📄 ssd1306.py            → Driver do display OLED
 ┃ ┗ 📄 diagram.json          → Conexões dos componentes no Wokwi
 ┣ 📂 codigos-node-red
 ┃ ┣ 📄 flow_nos.json         → Flow completo para importar no Node-RED
 ┃ ┗ 📄 dashboard_layout.html → HTML/CSS do nó Dashboard Visual
 ┣ 📂 codigos-google
 ┃ ┗ 📄 apps_script.js        → Código do Google Apps Script (endpoint HTTP)
 ┗ 📄 README.md
```

## 🛠️ Tecnologias

| Tecnologia | Versão | Uso |
|---|---|---|
| MicroPython | v1.21.0 | Firmware do ESP32 |
| Wokwi | — | Simulador de hardware online |
| HiveMQ Cloud | Free | Broker MQTT (porta 8883 TLS) |
| OpenWeatherMap API | v2.5 | Dados climáticos reais |
| Node-RED | v4.1.8 | Plataforma de automação e dashboard |
| node-red-dashboard | v3.6.6 | Interface gráfica do dashboard |
| Google Sheets | — | Persistência de dados em nuvem (Etapa 2) |
| Google Apps Script | — | Endpoint HTTP para Sheets e Email (Etapa 2) |
| Gmail / MailApp | — | Envio de relatório diário por email (Etapa 2) |

## 📡 Sensores e Componentes

| Componente | Pino | Protocolo | Função |
|---|---|---|---|
| ESP32 DevKit C v4 | — | — | Microcontrolador principal com Wi-Fi |
| OLED SSD1306 128x64 | GPIO21 (SDA) / GPIO22 (SCL) | I2C | Display com 4 telas alternáveis |
| DHT22 | GPIO4 | Digital | Temperatura e Umidade |
| LDR (Photoresistor) | GPIO34 (ADC) | Analógico | Luminosidade (0–100%) |
| MQ-2 | GPIO35 (ADC) | Analógico | Qualidade do Ar (0–100%) |
| Push Button | GPIO15 | Digital | Alternância entre telas do OLED |

## ✅ Funcionalidades

### Etapa 1
- 4 telas no OLED alternadas por botão: Temp/Umidade, Luz/Gás, Conforto e Previsão
- Alertas visuais no OLED para temperatura extrema (>35°C ou <5°C) e ar contaminado (>70%)
- Cálculo do índice de conforto térmico pela fórmula de Rothfusz (Heat Index)
- Previsão do tempo calculada por pressão atmosférica + temperatura com identificação dia/noite
- Dados reais de Suzano/SP via OpenWeatherMap consultados a cada 5 minutos
- 12 tópicos MQTT publicados a cada 10 segundos
- Dashboard Node-RED dark mode com dados em tempo real

### Etapa 2
- Gravação automática de cada leitura no Google Sheets a cada 30 segundos
- Planilha com colunas: Data/Hora, Temperatura, Umidade
- Cálculo da média diária de temperatura e umidade diretamente no ESP32
- Envio automático de relatório por email com data, médias e quantidade de leituras
- Google Apps Script como endpoint HTTP intermediário (resolve limitação SSL do Wokwi)

## 📊 Tópicos MQTT

| Tópico | Dado publicado |
|---|---|
| `estacao/temperatura` | Temperatura sensor DHT22 (°C) |
| `estacao/umidade` | Umidade sensor DHT22 (%) |
| `estacao/luminosidade` | Luminosidade LDR (%) |
| `estacao/gas` | Qualidade do ar MQ-2 (%) |
| `estacao/previsao` | Previsão calculada (ex: Nublado, Ensolarado) |
| `estacao/conforto` | Índice de conforto (ex: Confortável, Atenção) |
| `estacao/api/temperatura` | Temperatura real API (°C) |
| `estacao/api/umidade` | Umidade real API (%) |
| `estacao/api/pressao` | Pressão atmosférica real (hPa) |
| `estacao/api/vento` | Velocidade do vento real (km/h) |
| `estacao/api/sensacao` | Sensação térmica real (°C) |
| `estacao/api/descricao` | Descrição do clima (ex: céu pouco nublado) |

---

## 🚀 Como Rodar

### Pré-requisitos

- Conta no [Wokwi](https://wokwi.com)
- Conta no [HiveMQ Cloud](https://hivemq.com) — plano gratuito
- Conta no [OpenWeatherMap](https://openweathermap.org) — plano gratuito
- Conta Google com Gmail e Google Sheets (Etapa 2)
- [Node.js](https://nodejs.org) instalado (versão LTS)
- Node-RED: `npm install -g node-red`
- Dashboard: `cd ~/.node-red && npm install node-red-dashboard`

---

### 1️⃣ Configurar HiveMQ Cloud

1. Acesse [console.hivemq.cloud](https://console.hivemq.cloud) e crie uma conta
2. Clique em **Create New Cluster → Free**
3. Vá em **Access Management → Add Credentials**
4. Crie um usuário com permissão **PUBLISH_SUBSCRIBE**
5. Anote: **Cluster URL**, **usuário** e **senha**

---

### 2️⃣ Configurar OpenWeatherMap

1. Acesse [openweathermap.org](https://openweathermap.org) e crie uma conta gratuita
2. Vá em **My Profile → API Keys** e copie a chave **Default**
3. ⚠️ Aguarde até 10 minutos para a chave ativar

---

### 3️⃣ Configurar Google Sheets e Apps Script (Etapa 2)

1. Acesse [sheets.google.com](https://sheets.google.com) e crie uma planilha
2. Renomeie a aba para **Leituras** e adicione cabeçalhos: `Data/Hora`, `Temperatura`, `Umidade`
3. No menu **Extensões → Apps Script**, cole o conteúdo de `codigos-google/apps_script.js`
4. Execute a função `testarEmail` para autorizar permissões do MailApp
5. Clique em **Implantar → Nova implantação → App da Web → Qualquer pessoa → Implantar**
6. Copie a **URL de implantação** gerada
7. No navegador acesse `http://script.google.com/macros/s/SUA_URL/exec?datetime=teste&temp=25&hum=60` e copie a **URL final** após o redirecionamento (será usada em `EMAIL_URL`)

---

### 4️⃣ Configurar o Wokwi

1. Acesse o projeto: [wokwi.com/projects/463321787155842049](https://wokwi.com/projects/463321787155842049)
2. Cole o conteúdo de `codigos-wokwi/main.py` na aba de código
3. Crie uma aba `ssd1306.py` e cole o driver
4. Cole o `diagram.json` na aba correspondente
5. Substitua as credenciais no topo do `main.py`:

```python
MQTT_HOST  = "SEU_CLUSTER.hivemq.cloud"
MQTT_USER  = "SEU_USUARIO_HIVEMQ"
MQTT_PASS  = "SUA_SENHA_HIVEMQ"
OWM_KEY    = "SUA_API_KEY_OPENWEATHERMAP"
SHEETS_URL = "http://script.google.com/macros/s/SUA_URL/exec"
EMAIL_URL  = "https://script.googleusercontent.com/macros/echo?user_content_key=..."
EMAIL_DEST = "email_destinatario@dominio.com"
EMAIL_FROM = "SEU_EMAIL@gmail.com"
```

6. Clique em **▶ Play** e aguarde ~30 segundos

**✅ Serial Monitor deve mostrar:**
```
WiFi OK! IP: 10.10.0.2
MQTT OK!
API OK! Previsao: Nublado
Sistema iniciado! Aguardando ciclos...
DHT OK: T=25.0 H=60.0
DADOS ENVIADOS VIA MQTT | T=25.0 H=60.0
Salvando Sheets...
Sheets resp: {"status":"ok","msg":"Dados salvos!"}
Enviando email via Apps Script...
Email resp: {"status":"ok","msg":"Email enviado!"}
```

---

### 5️⃣ Configurar Node-RED

```bash
node-red
```
Acesse [http://localhost:1880](http://localhost:1880)

1. Menu **☰ → Import** → cole o `flow_nos.json`
2. Configure o broker HiveMQ (host, porta 8883, TLS, usuário e senha)
3. No nó **Dashboard Visual**, cole o conteúdo de `dashboard_layout.html`
4. Clique em **Implementar**
5. Acesse o dashboard: [http://localhost:1880/ui](http://localhost:1880/ui)

---

## 🖥️ Dashboard

Design dark mode com três seções:

- **Dados Reais (OpenWeatherMap):** temperatura, condição climática, sensação térmica, umidade, pressão e vento de Suzano/SP
- **Sensor ESP32 (Simulação Wokwi):** temperatura, umidade, luminosidade e qualidade do ar com cores dinâmicas
- **Previsão e Conforto:** previsão calculada com identificação dia/noite e índice de conforto térmico

---

## 👩‍💻 Autora

**Rayane da Luz Barbosa**  
RGM: 11221103247  
Universidade de Mogi das Cruzes — Disciplina: IoT — 2026  
Professor: Alessandro Aparecido da Silva Horas
