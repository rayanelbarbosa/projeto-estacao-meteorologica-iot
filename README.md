# 🌦️ Estação Meteorológica Virtual com ESP32

Projeto prático da disciplina de **Internet das Coisas (IoT)**  
Universidade de Mogi das Cruzes — 2026

---

## 📋 Descrição

Estação meteorológica simulada no **Wokwi** com ESP32, sensores DHT22, LDR e MQ-2, display OLED SSD1306 com 4 telas alternáveis via botão, comunicação MQTT via **HiveMQ Cloud** e dashboard **Node-RED** com dados reais da API **OpenWeatherMap** para Suzano/SP.

## 🏗️ Arquitetura

```
Wokwi (ESP32 MicroPython) → MQTT → HiveMQ Cloud → Node-RED → Dashboard
                ↑
        OpenWeatherMap API (dados reais Suzano/BR)
```

## 📁 Estrutura do Repositório

```
📦 estacao-meteorologica-iot
 ┣ 📂 codigos-wokwi
 ┃ ┣ 📄 main.py             → Firmware do ESP32 em MicroPython
 ┃ ┣ 📄 ssd1306.py          → Driver do display OLED
 ┃ ┗ 📄 diagram.json        → Conexões dos componentes no Wokwi
 ┣ 📂 codigos-node-red
 ┃ ┣ 📄 flow_nos.json       → Flow completo para importar no Node-RED
 ┃ ┗ 📄 dashboard_layout.html → HTML/CSS do nó Dashboard Visual
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

- 4 telas no OLED alternadas por botão: Temp/Umidade, Luz/Gás, Conforto e Previsão
- Alertas visuais no OLED para temperatura extrema (>35°C ou <5°C) e ar contaminado (>70%)
- Cálculo do índice de conforto térmico pela fórmula de Rothfusz (Heat Index)
- Previsão do tempo calculada por pressão atmosférica + temperatura sensor com identificação dia/noite via sunrise/sunset da API
- Dados reais de Suzano/SP via OpenWeatherMap consultados a cada 5 minutos
- 12 tópicos MQTT publicados a cada 10 segundos
- Dashboard Node-RED dark mode com dados em tempo real

## 📊 Tópicos MQTT

| Tópico | Dado publicado |
|---|---|
| `estacao/temperatura` | Temperatura sensor DHT22 (°C) |
| `estacao/umidade` | Umidade sensor DHT22 (%) |
| `estacao/luminosidade` | Luminosidade LDR (%) |
| `estacao/gas` | Qualidade do ar MQ-2 (%) |
| `estacao/previsao` | Previsão calculada (ex: Noite Nublada, Ensolarado) |
| `estacao/conforto` | Índice de conforto (ex: Confortável, Atenção) |
| `estacao/api/temperatura` | Temperatura real API (°C) |
| `estacao/api/umidade` | Umidade real API (%) |
| `estacao/api/pressao` | Pressão atmosférica real (hPa) |
| `estacao/api/vento` | Velocidade do vento real (km/h) |
| `estacao/api/sensacao` | Sensação térmica real (°C) |
| `estacao/api/descricao` | Descrição do clima (ex: nuvens quebradas) |

---

## 🚀 Como Rodar

### Pré-requisitos

- Conta no [Wokwi](https://wokwi.com)
- Conta no [HiveMQ Cloud](https://hivemq.com) — plano gratuito
- Conta no [OpenWeatherMap](https://openweathermap.org) — plano gratuito
- [Node.js](https://nodejs.org) instalado (versão LTS)
- Node-RED: `npm install -g node-red`
- Dashboard: `cd ~/.node-red && npm install node-red-dashboard`

---

### 1️⃣ Configurar HiveMQ Cloud

1. Acesse [console.hivemq.cloud](https://console.hivemq.cloud) e crie uma conta
2. Clique em **Create New Cluster → Free**
3. Vá em **Access Management → Add Credentials**
4. Crie um usuário com permissão **PUBLISH_SUBSCRIBE**
5. Anote: **Cluster URL** (ex: `abc123.hivemq.cloud`), **usuário** e **senha**

---

### 2️⃣ Configurar OpenWeatherMap

1. Acesse [openweathermap.org](https://openweathermap.org) e crie uma conta gratuita
2. Vá em **My Profile → API Keys**
3. Copie a chave **Default** (Status: Active)
4. ⚠️ Aguarde até 10 minutos para a chave ativar após criar a conta

---

### 3️⃣ Configurar o Wokwi

1. Acesse [wokwi.com](https://wokwi.com) → **New Project → ESP32**
2. Cole o conteúdo de `codigos-wokwi/main.py` na aba de código
3. Crie uma nova aba chamada `ssd1306.py` e cole o conteúdo do arquivo
4. Cole o conteúdo de `codigos-wokwi/diagram.json` na aba **diagram.json**
5. No topo do `main.py` substitua as credenciais:

```python
MQTT_HOST = "SEU_CLUSTER.hivemq.cloud"  # ← Cluster URL do HiveMQ
MQTT_USER = "SEU_USUARIO_HIVEMQ"         # ← Usuário criado
MQTT_PASS = "SUA_SENHA_HIVEMQ"           # ← Senha
OWM_KEY   = "SUA_API_KEY_OPENWEATHERMAP" # ← API Key
OWM_CITY  = "SuaCidade,BR"               # ← Sua cidade
```

6. Clique em **▶ Play** e aguarde ~30 segundos

**✅ Serial Monitor deve mostrar:**
```
I2C scan: [60]
OLED OK!
WiFi OK! IP: 10.10.0.2
MQTT OK!
API OK! Previsao: Noite Nublada
DADOS ENVIADOS VIA MQTT
```

---

### 4️⃣ Configurar Node-RED

**Instalação e inicialização:**
```bash
node-red
```
Acesse [http://localhost:1880](http://localhost:1880)

**Importar o flow:**
1. Menu **☰ → Import**
2. Cole o conteúdo de `codigos-node-red/flow_nos.json`
3. Clique em **Importar**

**Configurar o broker HiveMQ:**
1. Clique duas vezes em qualquer nó MQTT (roxo)
2. Clique no lápis ✏️ ao lado do broker
3. Configure:
   - **Servidor:** seu Cluster URL (ex: `abc123.hivemq.cloud`)
   - **Porta:** `8883`
   - **TLS:** ativado ✅
   - Aba **Segurança:** usuário e senha do HiveMQ
4. Clique em **Atualizar → Concluído**

**Configurar o layout do dashboard:**
1. Clique duas vezes no nó **"Dashboard Visual"** (azul)
2. Apague o conteúdo do campo **Template**
3. Cole todo o conteúdo de `codigos-node-red/dashboard_layout.html`
4. Clique em **Concluído**

**Implementar:**
1. Clique em **Implementar** (botão vermelho no canto superior direito)
2. Acesse o dashboard em [http://localhost:1880/ui](http://localhost:1880/ui)

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