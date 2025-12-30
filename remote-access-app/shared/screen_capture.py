"""
Módulo de captura de tela
Responsável por capturar e processar frames da tela
"""

import mss
import numpy as np
from PIL import Image
import io
import logging
from typing import Tuple, Optional
import time

logger = logging.getLogger(__name__)


class ScreenCapture:
    """
    Gerenciador de captura de tela
    """

    def __init__(self, target_fps: int = 15, quality: int = 80, scale: float = 1.0):
        """
        Inicializa capturador de tela

        Args:
            target_fps (int): FPS alvo para captura
            quality (int): Qualidade JPEG (0-100)
            scale (float): Escala de redimensionamento (1.0 = sem redimensionamento)
        """
        self.target_fps = target_fps
        self.frame_delay = 1.0 / target_fps
        self.quality = quality
        self.scale = scale
        self.last_frame_time = 0
        self.sct = mss.mss()
        self.monitor = self.sct.monitors[1]  # Monitor principal
        self.width = self.monitor["width"]
        self.height = self.monitor["height"]

        logger.info(
            f"ScreenCapture inicializado: {self.width}x{self.height} @ {target_fps}fps"
        )

    def capture_frame(self) -> Optional[Tuple[bytes, Tuple[int, int]]]:
        """
        Captura um frame da tela

        Returns:
            Tuple[bytes, (width, height)]: Frame em JPEG comprimido e dimensões
            None: Se ainda não passou o tempo mínimo entre frames
        """
        try:
            now = time.time()

            # Respeita FPS alvo
            elapsed = now - self.last_frame_time
            if elapsed < self.frame_delay:
                return None

            self.last_frame_time = now

            # Captura tela
            screenshot = self.sct.grab(self.monitor)

            # Converte para NumPy array
            frame = np.array(screenshot)

            # BGR to RGB (mss usa BGRA)
            frame = frame[:, :, :3]  # Remove canal alfa

            # Aplicar escala se necessário
            if self.scale != 1.0:
                new_width = int(self.width * self.scale)
                new_height = int(self.height * self.scale)
                frame = self._resize_frame(frame, new_width, new_height)
                actual_width, actual_height = new_width, new_height
            else:
                actual_width, actual_height = self.width, self.height

            # Comprime para JPEG
            jpeg_data = self._compress_frame(frame)

            return jpeg_data, (actual_width, actual_height)

        except Exception as e:
            logger.error(f"Erro ao capturar tela: {e}")
            return None

    @staticmethod
    def _resize_frame(frame: np.ndarray, width: int, height: int) -> np.ndarray:
        """Redimensiona frame mantendo aspect ratio"""
        try:
            img = Image.fromarray(frame, "RGB")
            img = img.resize((width, height), Image.Resampling.LANCZOS)
            return np.array(img)
        except Exception as e:
            logger.error(f"Erro ao redimensionar: {e}")
            return frame

    def _compress_frame(self, frame: np.ndarray) -> bytes:
        """
        Comprime frame para JPEG

        Args:
            frame (np.ndarray): Frame em formato RGB

        Returns:
            bytes: Dados JPEG comprimidos
        """
        try:
            img = Image.fromarray(frame, "RGB")

            # Salva em memória
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=self.quality, optimize=True)

            return buffer.getvalue()

        except Exception as e:
            logger.error(f"Erro ao comprimir frame: {e}")
            return b""

    def get_monitor_info(self) -> dict:
        """Retorna informações do monitor"""
        return {
            "width": self.width,
            "height": self.height,
            "top": self.monitor.get("top", 0),
            "left": self.monitor.get("left", 0)
        }

    def close(self):
        """Libera recursos"""
        if self.sct:
            self.sct.close()


class FrameProcessor:
    """
    Processa frames para otimização
    """

    @staticmethod
    def detect_changes(
        frame1: np.ndarray,
        frame2: np.ndarray,
        threshold: float = 0.05
    ) -> Tuple[bool, float]:
        """
        Detecta mudanças entre dois frames

        Args:
            frame1: Frame anterior
            frame2: Frame atual
            threshold: Limiar de mudança (0-1)

        Returns:
            Tuple[mudou?, diferença_percentual]
        """
        try:
            if frame1.shape != frame2.shape:
                return True, 1.0

            # Calcula diferença absoluta
            diff = np.abs(frame1.astype(float) - frame2.astype(float))

            # Percentual de pixels diferentes
            change_percent = np.mean(diff > 10) / 255

            changed = change_percent > threshold

            return changed, change_percent

        except Exception as e:
            logger.error(f"Erro ao detectar mudanças: {e}")
            return True, 1.0

    @staticmethod
    def apply_compression_hints(frame: np.ndarray) -> np.ndarray:
        """
        Aplica otimizações ao frame antes da compressão

        Args:
            frame: Frame em RGB

        Returns:
            np.ndarray: Frame otimizado
        """
        try:
            # Pode reduzir cores em áreas uniformes
            # Por enquanto, retorna o frame como está
            return frame

        except Exception as e:
            logger.error(f"Erro ao aplicar dicas de compressão: {e}")
            return frame


# Exemplo de uso
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)

    cap = ScreenCapture(target_fps=5, quality=85, scale=0.75)

    print(f"Monitor: {cap.get_monitor_info()}")

    # Captura 5 frames
    for i in range(5):
        result = cap.capture_frame()
        if result:
            jpeg_data, (w, h) = result
            print(f"Frame {i+1}: {len(jpeg_data)} bytes ({w}x{h})")
        else:
            time.sleep(0.1)

    cap.close()
