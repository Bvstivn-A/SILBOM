#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
node --test "$ROOT/tests/android-nfc/nfc-code.test.js"
TEMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TEMP_DIR"' EXIT
javac -d "$TEMP_DIR" \
  "$ROOT/android-app/src/cl/silbom/tecnico/NfcTextDecoder.java" \
  "$ROOT/android-app/src/cl/silbom/tecnico/MachineCode.java" \
  "$ROOT/tests/android-nfc/NfcTextDecoderTest.java" \
  "$ROOT/tests/android-nfc/MachineCodeTest.java"
java -cp "$TEMP_DIR" cl.silbom.tecnico.NfcTextDecoderTest
java -cp "$TEMP_DIR" cl.silbom.tecnico.MachineCodeTest

# Etiquetas QR impresas: se decodifican con el mismo ZXing que usa la APK.
ZXING_JAR="${SILBOM_ANDROID_LIBS:-$ROOT/android-app/libs}/zxing-core-3.5.3.jar"
if [[ -f "$ZXING_JAR" ]]; then
  javac -cp "$ZXING_JAR:$TEMP_DIR" -d "$TEMP_DIR" "$ROOT/tests/android-nfc/QrLabelDecodeTest.java"
  java -Djava.awt.headless=true -cp "$ZXING_JAR:$TEMP_DIR" QrLabelDecodeTest "$ROOT/docs/qr"
else
  echo "AVISO: $ZXING_JAR no existe; ejecuta android-app/build-apk.sh para probar las etiquetas QR."
fi
