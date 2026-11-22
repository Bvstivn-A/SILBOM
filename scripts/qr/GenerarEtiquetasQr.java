import com.google.zxing.BarcodeFormat;
import com.google.zxing.EncodeHintType;
import com.google.zxing.common.BitMatrix;
import com.google.zxing.qrcode.QRCodeWriter;
import com.google.zxing.qrcode.decoder.ErrorCorrectionLevel;

import java.awt.Color;
import java.awt.Font;
import java.awt.FontMetrics;
import java.awt.Graphics2D;
import java.awt.RenderingHints;
import java.awt.image.BufferedImage;
import java.io.File;
import java.util.EnumMap;
import java.util.Map;
import java.util.regex.Pattern;
import javax.imageio.ImageIO;

/**
 * Genera etiquetas QR imprimibles para máquinas SILBOM.
 *
 * El QR codifica EXCLUSIVAMENTE el identificador (p. ej. EQ-COM-03): sin URL,
 * sin IP y sin datos adicionales. El texto legible va solo en la imagen.
 *
 * Uso (desde la raíz del repositorio, tras compilar la APK una vez):
 *   java -cp android-app/libs/zxing-core-3.5.3.jar scripts/qr/GenerarEtiquetasQr.java \
 *       docs/qr EQ-COM-03 "Compresor de Tornillo" [EQ-ENV-01 "Envasadora ..."]...
 */
public final class GenerarEtiquetasQr {
    private static final Pattern MACHINE_CODE = Pattern.compile("^EQ-[A-Z]{2,4}-[0-9]{2}$");
    private static final int WIDTH = 900;
    private static final int QR_SIZE = 700;

    public static void main(String[] args) throws Exception {
        if (args.length < 3 || (args.length - 1) % 2 != 0) {
            System.err.println("Uso: GenerarEtiquetasQr <carpeta> <codigo> <nombre> [<codigo> <nombre>]...");
            System.exit(2);
        }
        File dir = new File(args[0]);
        if (!dir.isDirectory() && !dir.mkdirs()) throw new IllegalStateException("No se pudo crear " + dir);
        for (int i = 1; i < args.length; i += 2) {
            String code = args[i];
            String name = args[i + 1];
            if (!MACHINE_CODE.matcher(code).matches()) {
                throw new IllegalArgumentException("Código de máquina inválido: " + code);
            }
            File out = new File(dir, "QR-" + code + ".png");
            ImageIO.write(render(code, name), "png", out);
            System.out.println("Generado " + out.getPath() + " (contenido: " + code + ")");
        }
    }

    private static BufferedImage render(String code, String name) throws Exception {
        Map<EncodeHintType, Object> hints = new EnumMap<>(EncodeHintType.class);
        hints.put(EncodeHintType.ERROR_CORRECTION, ErrorCorrectionLevel.M);
        hints.put(EncodeHintType.MARGIN, 4); // Zona de silencio estándar.
        BitMatrix matrix = new QRCodeWriter().encode(code, BarcodeFormat.QR_CODE, 0, 0, hints);
        int modules = matrix.getWidth();
        int scale = QR_SIZE / modules;
        int qrPixels = modules * scale;

        int top = 110;
        int height = top + qrPixels + 210;
        BufferedImage image = new BufferedImage(WIDTH, height, BufferedImage.TYPE_INT_RGB);
        Graphics2D g = image.createGraphics();
        g.setColor(Color.WHITE);
        g.fillRect(0, 0, WIDTH, height);
        g.setRenderingHint(RenderingHints.KEY_TEXT_ANTIALIASING, RenderingHints.VALUE_TEXT_ANTIALIAS_ON);

        g.setColor(new Color(0x22272B));
        drawCentered(g, "SILBOM · Identificación de máquina", new Font(Font.SANS_SERIF, Font.BOLD, 34), 70);

        int left = (WIDTH - qrPixels) / 2;
        g.setColor(Color.BLACK);
        for (int y = 0; y < modules; y++) {
            for (int x = 0; x < modules; x++) {
                if (matrix.get(x, y)) g.fillRect(left + x * scale, top + y * scale, scale, scale);
            }
        }

        int textTop = top + qrPixels;
        g.setColor(Color.BLACK);
        drawCentered(g, code, new Font(Font.MONOSPACED, Font.BOLD, 64), textTop + 70);
        g.setColor(new Color(0x333333));
        drawCentered(g, name, new Font(Font.SANS_SERIF, Font.PLAIN, 38), textTop + 130);
        g.setColor(new Color(0x777777));
        drawCentered(g, "Solo identifica el equipo. No autoriza bloqueos ni liberaciones.",
                new Font(Font.SANS_SERIF, Font.ITALIC, 22), textTop + 180);
        g.dispose();
        return image;
    }

    private static void drawCentered(Graphics2D g, String text, Font font, int baseline) {
        g.setFont(font);
        FontMetrics metrics = g.getFontMetrics();
        g.drawString(text, (WIDTH - metrics.stringWidth(text)) / 2, baseline);
    }
}
