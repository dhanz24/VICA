import json
import logging
from typing import Optional

from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, Request, Response, Depends, APIRouter, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
