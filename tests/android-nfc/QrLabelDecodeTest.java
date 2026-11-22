import com.google.zxing.BarcodeFormat;
import com.google.zxing.BinaryBitmap;
import com.google.zxing.DecodeHintType;
import com.google.zxing.RGBLuminanceSource;
import com.google.zxing.Result;
import com.google.zxing.common.HybridBinarizer;
import com.google.zxing.qrcode.QRCodeReader;

import java.awt.image.BufferedImage;
import java.io.File;
import java.util.Collections;
import java.util.EnumMap;
import java.util.Map;
import javax.imageio.ImageIO;

/**
 * Decodifica las etiquetas impresas con las mismas opciones que QrScannerActivity
 * (ZXing, solo QR_CODE) y exige que el contenido sea exactamente el identificador.
 */
public final class QrLabelDecodeTest {
    public static void main(String[] args) throws Exception {
        File dir = new File(args[0]);
        String[] codes = {"EQ-COM-03", "EQ-ENV-01", "EQ-EXT-02"};
        Map<DecodeHintType, Object> hints = new EnumMap<>(DecodeHintType.class);
        hints.put(DecodeHintType.POSSIBLE_FORMATS, Collections.singletonList(BarcodeFormat.QR_CODE));
        hints.put(DecodeHintType.TRY_HARDER, Boolean.TRUE);
        hints.put(DecodeHintType.CHARACTER_SET, "UTF-8");
        for (String code : codes) {
            BufferedImage image = ImageIO.read(new File(dir, "QR-" + code + ".png"));
            int[] pixels = image.getRGB(0, 0, image.getWidth(), image.getHeight(), null, 0, image.getWidth());
            RGBLuminanceSource source = new RGBLuminanceSource(image.getWidth(), image.getHeight(), pixels);
            Result result = new QRCodeReader().decode(new BinaryBitmap(new HybridBinarizer(source)), hints);
            if (result.getBarcodeFormat() != BarcodeFormat.QR_CODE || !code.equals(result.getText())) {
                throw new AssertionError("QR-" + code + ".png contiene '" + result.getText() + "'");
            }
            if (cl.silbom.tecnico.MachineCode.rejectionReason(result.getText()) != null) {
                throw new AssertionError(code + " no pasa la validación de la app");
            }
            System.out.println("ZXing: QR-" + code + ".png -> '" + result.getText() + "' OK");
        }
    }
}
