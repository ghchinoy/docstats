# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import asyncio
import io
import logging

import httpx
import pypdf
from bs4 import BeautifulSoup
from google.cloud import storage

from models import TextSourceModel

logger = logging.getLogger(__name__)

# Shared GCS client
_storage_client = None

def get_storage_client():
    """Returns a shared Google Cloud Storage client instance."""
    global _storage_client

    if _storage_client is None:

        _storage_client = storage.Client()

    return _storage_client





async def extract_text_from_gcs_pdf(gcs_uri: str) -> str:
    """Extracts text from a PDF file stored in Google Cloud Storage."""
    try:

        storage_client = get_storage_client()

        bucket_name, blob_name = gcs_uri.replace("gs://", "").split("/", 1)

        blob = storage_client.bucket(bucket_name).blob(blob_name)

        # download_as_bytes is blocking, run in thread

        pdf_bytes = await asyncio.to_thread(blob.download_as_bytes)

        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))

        text = "".join(page.extract_text() or "" for page in reader.pages)

        if not text.strip():

            raise ValueError("No text in PDF.")

        return text

    except Exception as e:

        raise ValueError(f"GCS PDF error ({gcs_uri}): {e}") from e





async def get_processed_text(source: TextSourceModel) -> tuple[str, str]:
    """Processes the input source and returns the extracted text and a description."""
    if source.text:

        return source.text, "direct text"



    if source.web_url:

        try:

            async with httpx.AsyncClient(follow_redirects=True) as client:

                response = await client.get(

                    source.web_url,

                    headers={"User-Agent": "Mozilla/5.0"},

                    timeout=15.0,

                )

                response.raise_for_status()



            content_type = response.headers.get("Content-Type", "").lower()



            if "application/pdf" in content_type or source.web_url.lower().endswith(

                ".pdf"

            ):

                # Handle PDF from URL

                reader = pypdf.PdfReader(io.BytesIO(response.content))

                text = "".join(page.extract_text() or "" for page in reader.pages)

                if not text.strip():

                    raise ValueError("No text in web PDF.")

                return text, f"Web PDF: {source.web_url}"



            # Handle HTML

            soup = BeautifulSoup(response.content, "html.parser")

            # Try to find the main content

            article = soup.find("article") or soup.find("main")

            target = article or soup.body

            text = target.get_text(separator=" ", strip=True) if target else ""



            if not text.strip():

                raise ValueError("No text from URL.")

            return text, f"URL: {source.web_url}"

        except Exception as e:

            raise ValueError(f"Web URL error ({source.web_url}): {e}") from e



    if source.gcs_pdf_uri:

        text = await extract_text_from_gcs_pdf(source.gcs_pdf_uri)

        return text, f"GCS: {source.gcs_pdf_uri}"



    raise ValueError("Invalid source.")
