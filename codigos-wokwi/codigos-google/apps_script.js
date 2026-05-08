/**
 * Google Apps Script — Estação Meteorológica IoT
 * Universidade de Mogi das Cruzes — 2026
 * Autora: Rayane da Luz Barbosa
 *
 * Endpoint HTTP para:
 *   1. Gravar leituras de temperatura e umidade no Google Sheets
 *   2. Enviar relatório diário por email
 *
 * Como usar:
 *   1. Cole este código no Apps Script da sua planilha
 *   2. Execute testarEmail() para autorizar permissões
 *   3. Implante como Web App com acesso "Qualquer pessoa"
 */
 
function doGet(e) {
  try {
    var ss  = SpreadsheetApp.getActiveSpreadsheet();
    var aba = ss.getSheetByName("Leituras");
    var acao = e.parameter.acao || "salvar";
 
    // ---- Ação: salvar leitura na planilha ----
    if (acao == "salvar") {
      var dataHora    = e.parameter.datetime || new Date().toLocaleString("pt-BR");
      var temperatura = e.parameter.temp || "0";
      var umidade     = e.parameter.hum  || "0";
 
      aba.appendRow([dataHora, parseFloat(temperatura), parseFloat(umidade)]);
 
      return ContentService
        .createTextOutput(JSON.stringify({ status: "ok", msg: "Dados salvos!" }))
        .setMimeType(ContentService.MimeType.JSON);
 
    // ---- Ação: enviar email com relatório diário ----
    } else if (acao == "email") {
      var data_ref   = e.parameter.data || "hoje";
      var media_temp = e.parameter.temp || "0";
      var media_umid = e.parameter.hum  || "0";
      var qtd        = e.parameter.qtd  || "0";
      var dest       = "alessandrohoras@umc.br";
      var assunto    = "Relatorio Diario - Estacao Meteorologica";
      var corpo =
        "Relatorio Diario - Estacao Meteorologica Wokwi\n" +
        "===============================================\n" +
        "Data: "                    + data_ref   + "\n" +
        "Media de Temperatura: "    + media_temp + " C\n" +
        "Media de Umidade:     "    + media_umid + " %\n" +
        "Total de leituras:    "    + qtd        + "\n" +
        "===============================================\n" +
        "Projeto IoT - UMC 2026 - Rayane da Luz Barbosa\n";
 
      MailApp.sendEmail(dest, assunto, corpo);
 
      return ContentService
        .createTextOutput(JSON.stringify({ status: "ok", msg: "Email enviado!" }))
        .setMimeType(ContentService.MimeType.JSON);
    }
 
  } catch (err) {
    return ContentService
      .createTextOutput(JSON.stringify({ status: "erro", msg: err.toString() }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}
 
/**
 * Execute esta função manualmente UMA VEZ para autorizar
 * a permissão de envio de email (MailApp).
 * Depois pode apagar ou manter — não afeta o funcionamento.
 */
function testarEmail() {
  MailApp.sendEmail("alessandrohoras@umc.br", "Teste de permissao", "Teste de permissao ESP32 Estacao");
}