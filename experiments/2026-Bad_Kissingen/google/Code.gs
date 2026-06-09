
// 
// When edited: 
// 1. Save and DEPLOY as new deployment! 
// 2. UPDATE the webhook link (URL) in the TTN application
// 

function doGet() {
  return ContentService
    .createTextOutput("Webhook is alive V9")
    .setMimeType(ContentService.MimeType.TEXT);
}

function doPost(e) {
  /* 
  return ContentService
      .createTextOutput(JSON.stringify({ status: "test" }))
      .setMimeType(ContentService.MimeType.JSON);
  */
  try {
    const SPREADSHEET_ID = "1am54Mm_Peyzo58hMVs5cYSzmUhW6zH7aOMFH0EJhQ6s";
    const SHEET_NAME = "data";

    const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
    const sheet = ss.getSheetByName(SHEET_NAME);
    if (!sheet) throw new Error('Sheet "data" not found');

    const body = JSON.parse(e.postData.contents);

    const deviceId = body.end_device_ids?.device_id || "";
    const time =
      body.uplink_message?.received_at ||
      body.received_at ||
      new Date().toISOString();
    
    const decoded = body.uplink_message?.decoded_payload || {};

    //const temp = decoded.dht_temp_c ?? "";
    //const hum = decoded.dht_humidity_pct ?? "";
    //sheet.appendRow([time, deviceId, temp, hum, JSON.stringify(body)]);

    // sheet.appendRow([time, deviceId, JSON.stringify(body)]);

    const bme_hum = decoded.bme_hum ?? "";
    const bme_pres = decoded.bme_pres ?? "";
    const bme_temp = decoded.bme_temp ?? "";
    const ds_temp = decoded.ds_temp ?? "";
    const soil_perm = decoded.soil_perm ?? "";
    const soil_temp = decoded.soil_temp ?? "";
    const soil_econ = decoded.soil_econ ?? "";
    const vr_voltage = decoded.vr_voltage ?? "";

    const soil_vwc =  soil_perm ? 3.879e-4 * soil_perm -0.6956 : "";

    // sheet.appendRow([time, deviceId, bme_hum, bme_pres, bme_temp, ds_temp, soil_vwc, soil_temp,soil_perm,vr_voltage]);
    // sheet.appendRow([time, deviceId, bme_hum, bme_pres, bme_temp, ds_temp, soil_vwc, soil_temp,soil_perm,vr_voltage,JSON.stringify(body)]); // with raw data
    sheet.appendRow([time, deviceId, bme_hum, bme_pres, bme_temp, ds_temp, soil_vwc, soil_temp,soil_perm,soil_econ,vr_voltage,JSON.stringify(decoded)]); // with raw data of payload
    
    return ContentService
      .createTextOutput(JSON.stringify({ status: "ok" }))
      .setMimeType(ContentService.MimeType.JSON);

  } catch (err) {
    return ContentService
      .createTextOutput(JSON.stringify({
        status: "error",
        message: String(err)
      }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}