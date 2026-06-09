function decodeUplink(input) {
  var bytes = input.bytes;

  function readInt32LE(b, i) {
    return (b[i] | (b[i+1] << 8) | (b[i+2] << 16) | (b[i+3] << 24));
  }

  function readFloatLE(b, i) {
    var buffer = new ArrayBuffer(4);
    var view = new DataView(buffer);
    for (var j = 0; j < 4; j++) {
      view.setUint8(j, b[i + j]);
    }
    return view.getFloat32(0, true); // true = little endian
  }

  return {
    data: {
      // soil_id: readInt32LE(bytes, 0),
      soil_perm: readFloatLE(bytes, 0),
      soil_temp: readFloatLE(bytes, 4),
      ds_temp: readFloatLE(bytes, 8),
      bme_temp: readFloatLE(bytes, 12),
      bme_hum: readFloatLE(bytes, 16),
      bme_pres: readFloatLE(bytes, 20),
    }
  };
}
