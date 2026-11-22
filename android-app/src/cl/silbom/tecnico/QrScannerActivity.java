package cl.silbom.tecnico;

import android.Manifest;
import android.app.Activity;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.hardware.Camera;
import android.os.Bundle;
import android.os.Handler;
import android.os.HandlerThread;
import android.os.Looper;
import android.view.Gravity;
import android.view.SurfaceHolder;
import android.view.SurfaceView;
import android.view.View;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.TextView;

import com.google.zxing.BarcodeFormat;
import com.google.zxing.BinaryBitmap;
import com.google.zxing.DecodeHintType;
import com.google.zxing.NotFoundException;
import com.google.zxing.PlanarYUVLuminanceSource;
import com.google.zxing.Result;
import com.google.zxing.common.HybridBinarizer;
import com.google.zxing.qrcode.QRCodeReader;

import java.util.Collections;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.atomic.AtomicBoolean;

/**
 * Lector QR propio de la APK: cámara trasera + ZXing (solo QR_CODE).
 *
 * Devuelve únicamente el texto leído; MainActivity lo valida como identificador
 * de máquina. Nunca abre enlaces ni ejecuta el contenido del código.
 */
@SuppressWarnings("deprecation") // android.hardware.Camera: API estable en Android 7-14, sin dependencias.
public final class QrScannerActivity extends Activity implements SurfaceHolder.Callback, Camera.PreviewCallback {

    public static final String EXTRA_TEXT = "cl.silbom.tecnico.QR_TEXT";
    public static final String EXTRA_ERROR = "cl.silbom.tecnico.QR_ERROR";

    public static final String ERROR_CANCELLED = "cancelled";
    public static final String ERROR_CAMERA_UNAVAILABLE = "camera_unavailable";
    public static final String ERROR_PERMISSION_DENIED = "camera_permission_denied";
    public static final String ERROR_SCANNER_FAILED = "scanner_failed";

    private static final int REQUEST_CAMERA = 41;
    private static final long FOCUS_INTERVAL_MS = 2000;

    private final AtomicBoolean finished = new AtomicBoolean(false);
    private final AtomicBoolean decoding = new AtomicBoolean(false);
    private final Handler mainHandler = new Handler(Looper.getMainLooper());
    private final QRCodeReader reader = new QRCodeReader();
    private final Map<DecodeHintType, Object> hints = new EnumMap<>(DecodeHintType.class);

    private SurfaceView surfaceView;
    private boolean surfaceReady;
    private boolean permissionGranted;
    private Camera camera;
    private Camera.Size previewSize;
    private boolean periodicFocus;
    private HandlerThread decodeThread;
    private Handler decodeHandler;

    private final Runnable focusTask = new Runnable() {
        @Override
        public void run() {
            Camera current = camera;
            if (current == null || !periodicFocus) return;
            try {
                current.autoFocus(null);
            } catch (RuntimeException ignored) {
                // Algunos equipos rechazan enfocar mientras ya enfocan.
            }
            mainHandler.postDelayed(this, FOCUS_INTERVAL_MS);
        }
    };

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        getWindow().setStatusBarColor(Color.BLACK);
        getWindow().setNavigationBarColor(Color.BLACK);

        hints.put(DecodeHintType.POSSIBLE_FORMATS, Collections.singletonList(BarcodeFormat.QR_CODE));
        hints.put(DecodeHintType.TRY_HARDER, Boolean.TRUE);
        hints.put(DecodeHintType.CHARACTER_SET, "UTF-8");

        setContentView(buildLayout());

        if (!getPackageManager().hasSystemFeature(PackageManager.FEATURE_CAMERA_ANY)
                || Camera.getNumberOfCameras() == 0) {
            finishWithError(ERROR_CAMERA_UNAVAILABLE);
            return;
        }
        if (checkSelfPermission(Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED) {
            permissionGranted = true;
        } else {
            requestPermissions(new String[]{Manifest.permission.CAMERA}, REQUEST_CAMERA);
        }
    }

    private View buildLayout() {
        float density = getResources().getDisplayMetrics().density;
        FrameLayout root = new FrameLayout(this);
        root.setBackgroundColor(Color.BLACK);

        surfaceView = new SurfaceView(this);
        surfaceView.getHolder().addCallback(this);
        root.addView(surfaceView, new FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT, FrameLayout.LayoutParams.MATCH_PARENT, Gravity.CENTER));

        // Marco guía (solo visual; se decodifica el cuadro completo).
        View frame = new View(this);
        GradientDrawable border = new GradientDrawable();
        border.setColor(Color.TRANSPARENT);
        border.setStroke((int) (3 * density), 0xFFFFC107);
        border.setCornerRadius(16 * density);
        frame.setBackground(border);
        int side = (int) (240 * density);
        root.addView(frame, new FrameLayout.LayoutParams(side, side, Gravity.CENTER));

        TextView hint = new TextView(this);
        hint.setText("Apunta la cámara al código QR de la máquina");
        hint.setTextColor(Color.WHITE);
        hint.setTextSize(17);
        hint.setGravity(Gravity.CENTER);
        hint.setBackgroundColor(0xB322272B);
        int pad = (int) (16 * density);
        hint.setPadding(pad, pad * 2, pad, pad);
        root.addView(hint, new FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT, FrameLayout.LayoutParams.WRAP_CONTENT, Gravity.TOP));

        LinearLayout bottom = new LinearLayout(this);
        bottom.setOrientation(LinearLayout.VERTICAL);
        bottom.setGravity(Gravity.CENTER);
        bottom.setBackgroundColor(0xB322272B);
        bottom.setPadding(pad, pad, pad, pad * 2);
        TextView info = new TextView(this);
        info.setText("Solo se aceptan códigos de máquina SILBOM (ej. EQ-COM-03).");
        info.setTextColor(0xFFDDDDDD);
        info.setTextSize(13);
        info.setGravity(Gravity.CENTER);
        bottom.addView(info);
        Button cancel = new Button(this);
        cancel.setText("Cancelar y volver a SILBOM");
        cancel.setOnClickListener(v -> finishWithError(ERROR_CANCELLED));
        LinearLayout.LayoutParams buttonParams = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT);
        buttonParams.topMargin = pad / 2;
        bottom.addView(cancel, buttonParams);
        root.addView(bottom, new FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT, FrameLayout.LayoutParams.WRAP_CONTENT, Gravity.BOTTOM));
        return root;
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {
        if (requestCode != REQUEST_CAMERA) return;
        if (grantResults.length > 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
            permissionGranted = true;
            startCameraIfReady();
        } else {
            finishWithError(ERROR_PERMISSION_DENIED);
        }
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (decodeThread == null) {
            decodeThread = new HandlerThread("silbom-qr-decode");
            decodeThread.start();
            decodeHandler = new Handler(decodeThread.getLooper());
        }
        startCameraIfReady();
    }

    @Override
    protected void onPause() {
        releaseCamera();
        if (decodeThread != null) {
            decodeThread.quitSafely();
            decodeThread = null;
            decodeHandler = null;
        }
        super.onPause();
    }

    @Override
    public void onBackPressed() {
        finishWithError(ERROR_CANCELLED);
    }

    @Override
    public void surfaceCreated(SurfaceHolder holder) {
        surfaceReady = true;
        startCameraIfReady();
    }

    @Override
    public void surfaceChanged(SurfaceHolder holder, int format, int width, int height) {
        // La vista previa se configura una sola vez al abrir la cámara.
    }

    @Override
    public void surfaceDestroyed(SurfaceHolder holder) {
        surfaceReady = false;
        releaseCamera();
    }

    private void startCameraIfReady() {
        if (finished.get() || camera != null || !permissionGranted || !surfaceReady || decodeHandler == null) return;
        try {
            int cameraId = findBackCamera();
            camera = Camera.open(cameraId);
            if (camera == null) {
                finishWithError(ERROR_CAMERA_UNAVAILABLE);
                return;
            }
            Camera.CameraInfo info = new Camera.CameraInfo();
            Camera.getCameraInfo(cameraId, info);
            boolean front = info.facing == Camera.CameraInfo.CAMERA_FACING_FRONT;
            // La actividad está fija en vertical (rotación de pantalla 0).
            camera.setDisplayOrientation(front ? (360 - info.orientation) % 360 : info.orientation);

            Camera.Parameters params = camera.getParameters();
            previewSize = choosePreviewSize(params.getSupportedPreviewSizes());
            params.setPreviewSize(previewSize.width, previewSize.height);
            List<String> focusModes = params.getSupportedFocusModes();
            periodicFocus = false;
            if (focusModes != null && focusModes.contains(Camera.Parameters.FOCUS_MODE_CONTINUOUS_PICTURE)) {
                params.setFocusMode(Camera.Parameters.FOCUS_MODE_CONTINUOUS_PICTURE);
            } else if (focusModes != null && focusModes.contains(Camera.Parameters.FOCUS_MODE_CONTINUOUS_VIDEO)) {
                params.setFocusMode(Camera.Parameters.FOCUS_MODE_CONTINUOUS_VIDEO);
            } else if (focusModes != null && focusModes.contains(Camera.Parameters.FOCUS_MODE_AUTO)) {
                params.setFocusMode(Camera.Parameters.FOCUS_MODE_AUTO);
                periodicFocus = true;
            }
            camera.setParameters(params);
            fitPreview(previewSize, info.orientation);
            camera.setPreviewDisplay(surfaceView.getHolder());
            camera.setPreviewCallback(this);
            camera.startPreview();
            if (periodicFocus) mainHandler.postDelayed(focusTask, 500);
        } catch (Exception exception) {
            releaseCamera();
            // Cámara ocupada por otra aplicación o sin acceso.
            finishWithError(ERROR_CAMERA_UNAVAILABLE);
        }
    }

    private static int findBackCamera() {
        Camera.CameraInfo info = new Camera.CameraInfo();
        for (int i = 0; i < Camera.getNumberOfCameras(); i++) {
            Camera.getCameraInfo(i, info);
            if (info.facing == Camera.CameraInfo.CAMERA_FACING_BACK) return i;
        }
        return 0;
    }

    /** Resolución cercana a 1280x720: suficiente para QR impresos y rápida de decodificar. */
    private static Camera.Size choosePreviewSize(List<Camera.Size> sizes) {
        Camera.Size best = sizes.get(0);
        long target = 1280L * 720L;
        long bestDiff = Long.MAX_VALUE;
        for (Camera.Size size : sizes) {
            long diff = Math.abs((long) size.width * size.height - target);
            if (diff < bestDiff) {
                best = size;
                bestDiff = diff;
            }
        }
        return best;
    }

    /** Ajusta la vista previa a la proporción real de la cámara para no deformar la imagen. */
    private void fitPreview(Camera.Size size, int orientation) {
        View parent = (View) surfaceView.getParent();
        int viewW = parent.getWidth();
        int viewH = parent.getHeight();
        if (viewW == 0 || viewH == 0) return;
        boolean rotated = orientation == 90 || orientation == 270;
        float camW = rotated ? size.height : size.width;
        float camH = rotated ? size.width : size.height;
        float scale = Math.max(viewW / camW, viewH / camH); // Cubre la pantalla (center-crop).
        FrameLayout.LayoutParams lp = new FrameLayout.LayoutParams(
                Math.round(camW * scale), Math.round(camH * scale), Gravity.CENTER);
        surfaceView.setLayoutParams(lp);
    }

    @Override
    public void onPreviewFrame(byte[] data, Camera cam) {
        Handler handler = decodeHandler;
        final Camera.Size size = previewSize;
        if (data == null || handler == null || size == null || finished.get()) return;
        if (!decoding.compareAndSet(false, true)) return; // Un cuadro a la vez.
        final byte[] frame = data.clone();
        boolean queued = handler.post(() -> {
            try {
                String text = decode(frame, size.width, size.height);
                if (text != null) mainHandler.post(() -> finishWithText(text));
            } catch (RuntimeException exception) {
                mainHandler.post(() -> finishWithError(ERROR_SCANNER_FAILED));
            } finally {
                decoding.set(false);
            }
        });
        if (!queued) decoding.set(false); // El hilo se detuvo en onPause.
    }

    private String decode(byte[] yuv, int width, int height) {
        PlanarYUVLuminanceSource source =
                new PlanarYUVLuminanceSource(yuv, width, height, 0, 0, width, height, false);
        try {
            Result result = reader.decode(new BinaryBitmap(new HybridBinarizer(source)), hints);
            return result.getBarcodeFormat() == BarcodeFormat.QR_CODE ? result.getText() : null;
        } catch (NotFoundException | com.google.zxing.ChecksumException | com.google.zxing.FormatException e) {
            return null; // Sin QR legible en este cuadro: seguir intentando.
        } finally {
            reader.reset();
        }
    }

    private void releaseCamera() {
        mainHandler.removeCallbacks(focusTask);
        Camera current = camera;
        camera = null;
        if (current == null) return;
        try {
            current.setPreviewCallback(null);
            current.stopPreview();
        } catch (RuntimeException ignored) {
            // La cámara pudo cerrarse por el sistema.
        }
        current.release();
    }

    private void finishWithText(String text) {
        if (!finished.compareAndSet(false, true)) return;
        releaseCamera();
        Intent data = new Intent();
        data.putExtra(EXTRA_TEXT, text == null ? "" : text);
        setResult(RESULT_OK, data);
        finish();
    }

    private void finishWithError(String reason) {
        if (!finished.compareAndSet(false, true)) return;
        releaseCamera();
        Intent data = new Intent();
        data.putExtra(EXTRA_ERROR, reason);
        setResult(RESULT_CANCELED, data);
        finish();
    }
}
