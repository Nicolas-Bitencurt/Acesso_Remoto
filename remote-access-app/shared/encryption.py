"""
Módulo de criptografia para comunicação segura
Implementa AES-256-GCM para criptografia de ponta a ponta
"""

import os
import json
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
import hashlib
from typing import Tuple, Dict, Any
import logging

logger = logging.getLogger(__name__)


class CryptoManager:
    """
    Gerenciador de criptografia para a aplicação
    Usa AES-256-GCM para autenticação e criptografia
    """

    def __init__(self, master_key: str):
        """
        Inicializa o gerenciador de criptografia

        Args:
            master_key (str): Chave mestra para derivar chaves
        """
        self.master_key = master_key.encode()
        self.salt = b"RemoteAccessApp2024"  # Em produção, gerar aleatoriamente
        self.nonce_counter = 0

    def _derive_key(self, salt: bytes = None) -> bytes:
        """
        Deriva uma chave de 256 bits a partir da chave mestra usando PBKDF2

        Args:
            salt (bytes): Salt para derivação (opcional)

        Returns:
            bytes: Chave de 256 bits
        """
        if salt is None:
            salt = self.salt

        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,  # 256 bits
            salt=salt,
            iterations=100000,
        )
        return kdf.derive(self.master_key)

    def _generate_nonce(self) -> bytes:
        """
        Gera um nonce (número usado uma vez) para GCM

        Returns:
            bytes: Nonce de 12 bytes
        """
        # Para aplicação em produção, usar os.urandom(12)
        # Para MVP, usamos counter
        self.nonce_counter += 1
        nonce = (self.nonce_counter).to_bytes(12, byteorder="big")
        return nonce

    def encrypt(self, plaintext: str, associated_data: str = None) -> Dict[str, str]:
        """
        Criptografa um texto usando AES-256-GCM

        Args:
            plaintext (str): Texto a criptografar
            associated_data (str): Dados associados (não criptografados, mas autenticados)

        Returns:
            Dict: {
                'ciphertext': texto criptografado (base64),
                'nonce': nonce usado (base64),
                'tag': tag de autenticação (base64),
                'aad': associated_data (base64)
            }
        """
        try:
            key = self._derive_key()
            nonce = self._generate_nonce()

            cipher = AESGCM(key)

            # Dados associados (autenticados mas não criptografados)
            aad = None
            if associated_data:
                aad = associated_data.encode()

            # Criptografa e obtém tag de autenticação
            ciphertext = cipher.encrypt(
                nonce, plaintext.encode(), aad
            )

            # ciphertext já contém a tag no final (GCM automático)
            # Separamos: primeiros N-16 bytes são dados, últimos 16 são tag
            actual_ciphertext = ciphertext[:-16]
            tag = ciphertext[-16:]

            return {
                "ciphertext": base64.b64encode(actual_ciphertext).decode(),
                "nonce": base64.b64encode(nonce).decode(),
                "tag": base64.b64encode(tag).decode(),
                "aad": base64.b64encode(aad).decode() if aad else None
            }

        except Exception as e:
            logger.error(f"Erro ao criptografar: {str(e)}")
            raise

    def decrypt(self, encrypted_data: Dict[str, str]) -> str:
        """
        Descriptografa um texto usando AES-256-GCM

        Args:
            encrypted_data (Dict): Dicionário com:
                - ciphertext (base64)
                - nonce (base64)
                - tag (base64)
                - aad (base64, opcional)

        Returns:
            str: Texto descriptografado

        Raises:
            ValueError: Se a autenticação falhar
        """
        try:
            key = self._derive_key()

            # Decodifica de base64
            nonce = base64.b64decode(encrypted_data["nonce"])
            ciphertext = base64.b64decode(encrypted_data["ciphertext"])
            tag = base64.b64decode(encrypted_data["tag"])

            aad = None
            if encrypted_data.get("aad"):
                aad = base64.b64decode(encrypted_data["aad"])

            # Reconstrói o ciphertext (dados + tag)
            full_ciphertext = ciphertext + tag

            cipher = AESGCM(key)

            # Descriptografa e verifica tag
            plaintext = cipher.decrypt(nonce, full_ciphertext, aad)

            return plaintext.decode()

        except Exception as e:
            logger.error(f"Erro ao descriptografar: {str(e)}")
            raise ValueError("Falha na descriptografia ou autenticação")

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash de senha usando SHA-256

        Args:
            password (str): Senha em texto plano

        Returns:
            str: Hash hexadecimal
        """
        return hashlib.sha256(password.encode()).hexdigest()

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """
        Verifica se uma senha corresponde ao hash

        Args:
            password (str): Senha em texto plano
            password_hash (str): Hash armazenado

        Returns:
            bool: True se coincide
        """
        return CryptoManager.hash_password(password) == password_hash

    @staticmethod
    def generate_session_token(length: int = 32) -> str:
        """
        Gera um token de sessão aleatório

        Args:
            length (int): Tamanho do token em bytes

        Returns:
            str: Token em hexadecimal
        """
        return os.urandom(length).hex()


# Exemplo de uso
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)

    # Inicializa gerenciador
    crypto = CryptoManager("minha-chave-super-segura")

    # Teste de criptografia
    msg = "Olá, mundo!"
    print(f"Mensagem original: {msg}")

    encrypted = crypto.encrypt(msg, "dados_associados")
    print(f"Criptografado: {encrypted}")

    decrypted = crypto.decrypt(encrypted)
    print(f"Descriptografado: {decrypted}")

    # Teste de hash de senha
    password = "senha123"
    hashed = CryptoManager.hash_password(password)
    print(f"\nSenha hash: {hashed}")
    print(f"Verificação: {CryptoManager.verify_password(password, hashed)}")
