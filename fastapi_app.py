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

import logging

from fastapi import FastAPI, HTTPException

from extraction import get_processed_text
from metrics import calculate_readability_metrics_logic
from models import ReadabilityScoresModel, TextSourceModel

logger = logging.getLogger(__name__)

fastapi_app = FastAPI(title="Readability API", version="1.4.0")

@fastapi_app.post("/scores/", response_model=ReadabilityScoresModel)
async def scores_fastapi(req: TextSourceModel):
    """FastAPI endpoint to calculate readability scores."""
    try:
        text, desc = await get_processed_text(req)
        return await calculate_readability_metrics_logic(text, desc)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"FastAPI error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error.")
