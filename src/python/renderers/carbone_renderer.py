"""
Carbone Renderer Module

Handles PDF generation using Carbone SDK for partnership analysis reports.
Provides integration with Carbone service for converting JSON payloads to PDF documents.
"""

import os
from typing import Dict, Any, Tuple, Optional
import structlog
from ..config.config_loader import ConfigLoader

# Import Carbone SDK - assuming it's installed via pip
try:
    from carbone_sdk import CarboneSDK
except ImportError:
    CarboneSDK = None  # Handle missing SDK gracefully

logger = structlog.get_logger(__name__)


class CarboneRenderer:
    """
    Handles PDF rendering using Carbone SDK.

    This class provides methods to initialize the Carbone client, prepare payloads,
    render PDFs, and validate output integrity.
    """

    def __init__(self, config: ConfigLoader):
        """
        Initialize the Carbone renderer with configuration.

        Args:
            config: Configuration loader instance containing Carbone settings
        """
        self.config = config
        self.client: Optional[CarboneSDK] = None
        self._initialized = False

    def initialize_carbone_client(self, secret_access_token: Optional[str] = None) -> CarboneSDK:
        """
        Initialize and return Carbone SDK client.

        Args:
            secret_access_token: Carbone secret access token (if None, uses config)

        Returns:
            Initialized CarboneSDK client

        Raises:
            RuntimeError: If Carbone SDK is not available or initialization fails
        """
        if CarboneSDK is None:
            raise RuntimeError("Carbone SDK is not installed. Install with: pip install carbone-sdk")

        if secret_access_token is None:
            secret_access_token = self.config.get('carbone_secret_access_token')
            if not secret_access_token:
                raise ValueError("Carbone secret access token not found in configuration")

        try:
            self.client = CarboneSDK(secret_access_token=secret_access_token)
            api_version = self.config.get('carbone_api_version', 'v3')
            self.client.set_api_version(api_version)
            self._initialized = True
            logger.info("Carbone client initialized successfully", api_version=api_version)
            return self.client
        except Exception as e:
            logger.error("Failed to initialize Carbone client", error=str(e))
            raise RuntimeError(f"Carbone client initialization failed: {e}") from e

    def prepare_carbone_payload(self, data: Dict[str, Any], template_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Prepare JSON payload for Carbone rendering.

        This method wraps the data in the expected Carbone payload structure.

        Args:
            data: The data dictionary to render
            template_id: Template ID (if None, uses config default)

        Returns:
            Carbone-compatible payload dictionary
        """
        if template_id is None:
            template_id = self.config.get('carbone_template_id', 'partnership_report_v1')

        payload = {
            "data": data,
            "template": template_id,
            "options": {
                "language": self.config.get('report_language', 'en'),
                "format": "pdf",
                "margins": {
                    "top": self.config.get('pdf_margin_top', 20),
                    "bottom": self.config.get('pdf_margin_bottom', 20),
                    "left": self.config.get('pdf_margin_left', 15),
                    "right": self.config.get('pdf_margin_right', 15)
                }
            }
        }

        logger.debug("Prepared Carbone payload", template_id=template_id)
        return payload

    def render_to_pdf(self, payload: Dict[str, Any], client: Optional[CarboneSDK] = None) -> bytes:
        """
        Render PDF from Carbone payload.

        Args:
            payload: Carbone-compatible payload dictionary
            client: Carbone client instance (if None, uses initialized client)

        Returns:
            PDF binary data

        Raises:
            RuntimeError: If rendering fails
        """
        if client is None:
            if not self._initialized or self.client is None:
                self.initialize_carbone_client()
            client = self.client

        try:
            logger.info("Starting PDF rendering with Carbone")
            file_or_template_id = payload.get("template")
            json_data = payload.get("data")
            options = payload.get("options", {})
            report_bytes, unique_report_name = client.render(file_or_template_id, json_data, options)
            logger.info("PDF rendering completed successfully", report_name=unique_report_name)
            return report_bytes
        except Exception as e:
            logger.error("PDF rendering failed", error=str(e))
            raise RuntimeError(f"Carbone rendering failed: {e}") from e

    def save_pdf(self, pdf_binary: bytes, output_path: str) -> str:
        """
        Save PDF binary data to file.

        Args:
            pdf_binary: PDF binary data
            output_path: Path where to save the PDF

        Returns:
            Absolute path to the saved PDF file

        Raises:
            IOError: If file cannot be written
        """
        try:
            # Ensure output directory exists
            output_dir = os.path.dirname(output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)

            with open(output_path, 'wb') as f:
                f.write(pdf_binary)

            logger.info("PDF saved successfully", path=output_path, size=len(pdf_binary))
            return os.path.abspath(output_path)
        except Exception as e:
            logger.error("Failed to save PDF", path=output_path, error=str(e))
            raise IOError(f"Failed to save PDF to {output_path}: {e}") from e

    def validate_pdf_integrity(self, pdf_path: str) -> Tuple[bool, str]:
        """
        Validate PDF file integrity.

        Performs basic validation to ensure the PDF file is readable and not corrupted.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            if not os.path.exists(pdf_path):
                return False, f"PDF file does not exist: {pdf_path}"

            file_size = os.path.getsize(pdf_path)
            if file_size == 0:
                return False, "PDF file is empty"

            # Basic PDF header check
            with open(pdf_path, 'rb') as f:
                header = f.read(8)
                if not header.startswith(b'%PDF-'):
                    return False, "Invalid PDF header"

            logger.debug("PDF integrity validation passed", path=pdf_path, size=file_size)
            return True, ""
        except Exception as e:
            logger.error("PDF integrity validation failed", path=pdf_path, error=str(e))
            return False, f"PDF validation error: {e}"

    def render_and_save(self, data: Dict[str, Any], output_path: str, template_id: Optional[str] = None) -> str:
        """
        Convenience method to render data to PDF and save to file.

        Args:
            data: Data dictionary to render
            output_path: Path where to save the PDF
            template_id: Optional template ID override

        Returns:
            Absolute path to the saved PDF file

        Raises:
            RuntimeError: If rendering or saving fails
        """
        payload = self.prepare_carbone_payload(data, template_id)
        pdf_binary = self.render_to_pdf(payload)
        saved_path = self.save_pdf(pdf_binary, output_path)

        # Validate the saved PDF
        is_valid, error_msg = self.validate_pdf_integrity(saved_path)
        if not is_valid:
            logger.warning("PDF validation failed after saving", path=saved_path, error=error_msg)
            # Don't raise error, just log - the file might still be usable

        return saved_path