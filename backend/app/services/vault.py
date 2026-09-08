"""
Encrypted local vault for API credentials.

Design goals:
- Free: no cloud secret manager required, everything lives on the machine.
- Secret: values are encrypted at rest with Fernet (AES-128-CBC + HMAC-SHA256).
- Invisible: plaintext values never leave this module. The API layer only ever
  sees masked previews (last 4 characters).

Storage layout (outside the repository, so a secret can never be committed):

    <vault_dir>/master.key   0600  # encryption key, generated on first use
    <vault_dir>/secrets.enc  0600  # encrypted JSON blob with every credential

The master key can also be supplied through the AVE_MASTER_KEY environment
variable, which is the recommended setup for deployments (Replit Secrets,
Railway/Render env vars, Docker secrets): the file on disk is then never
created and the vault is worthless without the env var.
"""

import json
import logging
import os
import stat
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Dict, List, Optional

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)

MASTER_KEY_ENV = "AVE_MASTER_KEY"
VAULT_DIR_ENV = "AVE_VAULT_DIR"
DEFAULT_VAULT_DIR = "~/.autovideoeditor"

_OWNER_ONLY = stat.S_IRUSR | stat.S_IWUSR  # 0600


class VaultError(RuntimeError):
    """Raised when the vault cannot be read or written."""


class SecretVault:
    """Encrypted key/value store for API credentials."""

    def __init__(self, vault_dir: Optional[str] = None) -> None:
        raw_dir = vault_dir or os.getenv(VAULT_DIR_ENV) or DEFAULT_VAULT_DIR
        self.vault_dir = Path(raw_dir).expanduser().resolve()
        self.secrets_path = self.vault_dir / "secrets.enc"
        self.master_key_path = self.vault_dir / "master.key"
        self._lock = Lock()
        self._fernet: Optional[Fernet] = None

    # ------------------------------------------------------------------
    # Encryption key handling
    # ------------------------------------------------------------------
    @property
    def master_key_source(self) -> str:
        """Where the encryption key comes from: 'env' or 'file'."""
        return "env" if os.getenv(MASTER_KEY_ENV) else "file"

    def _load_fernet(self) -> Fernet:
        if self._fernet is not None:
            return self._fernet

        env_key = os.getenv(MASTER_KEY_ENV)
        if env_key:
            try:
                self._fernet = Fernet(env_key.strip().encode())
            except (ValueError, TypeError) as exc:
                raise VaultError(
                    f"{MASTER_KEY_ENV} is not a valid Fernet key. "
                    "Generate one with: python -c \"from cryptography.fernet "
                    'import Fernet; print(Fernet.generate_key().decode())"'
                ) from exc
            return self._fernet

        self._ensure_vault_dir()
        if not self.master_key_path.exists():
            key = Fernet.generate_key()
            self._write_private(self.master_key_path, key)
            logger.info("Generated a new vault master key at %s", self.master_key_path)
        else:
            key = self.master_key_path.read_bytes().strip()

        try:
            self._fernet = Fernet(key)
        except (ValueError, TypeError) as exc:
            raise VaultError(
                f"Master key at {self.master_key_path} is corrupted. "
                "Delete it to start over (stored credentials will be lost)."
            ) from exc
        return self._fernet

    def _ensure_vault_dir(self) -> None:
        self.vault_dir.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(self.vault_dir, stat.S_IRWXU)  # 0700
        except OSError:  # pragma: no cover - non-POSIX filesystems
            logger.debug("Could not tighten permissions on %s", self.vault_dir)

    @staticmethod
    def _write_private(path: Path, payload: bytes) -> None:
        """Write a file that only the current user can read."""
        tmp_path = path.with_suffix(path.suffix + ".tmp")
        fd = os.open(str(tmp_path), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, _OWNER_ONLY)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
        except Exception:
            tmp_path.unlink(missing_ok=True)
            raise
        os.replace(tmp_path, path)
        try:
            os.chmod(path, _OWNER_ONLY)
        except OSError:  # pragma: no cover - non-POSIX filesystems
            logger.debug("Could not tighten permissions on %s", path)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def _read_all(self) -> Dict[str, Dict]:
        if not self.secrets_path.exists():
            return {}

        blob = self.secrets_path.read_bytes()
        if not blob.strip():
            return {}

        try:
            decrypted = self._load_fernet().decrypt(blob)
        except InvalidToken as exc:
            raise VaultError(
                "Could not decrypt the credential vault. The master key does "
                "not match the stored data (was AVE_MASTER_KEY changed?)."
            ) from exc

        try:
            data = json.loads(decrypted.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise VaultError("Credential vault contents are corrupted.") from exc

        return data if isinstance(data, dict) else {}

    def _write_all(self, data: Dict[str, Dict]) -> None:
        self._ensure_vault_dir()
        payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self._write_private(self.secrets_path, self._load_fernet().encrypt(payload))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def set_secret(self, name: str, value: str, **metadata) -> Dict:
        """Store (or replace) a credential. Returns its public metadata."""
        value = (value or "").strip()
        if not value:
            raise ValueError("Credential value cannot be empty")

        now = datetime.now(timezone.utc).isoformat()
        with self._lock:
            data = self._read_all()
            existing = data.get(name, {})
            entry = {
                "value": value,
                "created_at": existing.get("created_at", now),
                "updated_at": now,
                "last4": value[-4:],
                "length": len(value),
                **metadata,
            }
            data[name] = entry
            self._write_all(data)

        return self._public_metadata(name, entry)

    def get_secret(self, name: str) -> Optional[str]:
        """Return the plaintext credential, or None. Never expose over HTTP."""
        with self._lock:
            entry = self._read_all().get(name)
        return entry.get("value") if entry else None

    def delete_secret(self, name: str) -> bool:
        with self._lock:
            data = self._read_all()
            if name not in data:
                return False
            del data[name]
            self._write_all(data)
        return True

    def describe(self, name: str) -> Optional[Dict]:
        """Public, non-sensitive metadata for one credential."""
        with self._lock:
            entry = self._read_all().get(name)
        return self._public_metadata(name, entry) if entry else None

    def list_names(self) -> List[str]:
        with self._lock:
            return sorted(self._read_all().keys())

    def clear(self) -> int:
        """Remove every stored credential. Returns how many were removed."""
        with self._lock:
            data = self._read_all()
            count = len(data)
            self._write_all({})
        return count

    @staticmethod
    def _public_metadata(name: str, entry: Dict) -> Dict:
        return {
            "name": name,
            "masked": SecretVault.mask(entry.get("last4", ""), entry.get("length", 0)),
            "created_at": entry.get("created_at"),
            "updated_at": entry.get("updated_at"),
        }

    @staticmethod
    def mask(last4: str, length: int = 0) -> str:
        """Build a display-safe preview: '••••••••••1234'."""
        dots = "•" * max(4, min(length - len(last4), 20))
        return f"{dots}{last4}" if last4 else dots


_vault: Optional[SecretVault] = None
_vault_lock = Lock()


def get_vault() -> SecretVault:
    """Process-wide vault singleton."""
    global _vault
    if _vault is None:
        with _vault_lock:
            if _vault is None:
                _vault = SecretVault()
    return _vault


def generate_master_key() -> str:
    """Convenience helper for `python -m app.services.vault`."""
    return Fernet.generate_key().decode()


if __name__ == "__main__":  # pragma: no cover - operational helper
    print(generate_master_key())
