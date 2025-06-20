import os
from dotenv import load_dotenv
import json
import time
import random
from google.api_core.exceptions import ResourceExhausted, TooManyRequests
from config import Config
from logger import Logger

load_dotenv()

from pydantic import BaseModel
from typing import List, Optional, Dict
from langchain.output_parsers import PydanticOutputParser, OutputFixingParser
from langchain_google_genai import ChatGoogleGenerativeAI
from agents.prompts import INSTRUCTION_ANALYSIS_PROMPT

logger = Logger(log_file=Config.LOG_FILE)

class PageSpec(BaseModel):
    name: str
    contents: List[str]
    slug: str
    path: str
    nav: List[str]

class SiteMapEntry(BaseModel):
    slug: str
    path: str
    title: str

class OutputSchema(BaseModel):
    overall_design: str
    pages: List[PageSpec]
    siteMap: List[SiteMapEntry]

class InstructionAnalysisAgent:
    def analyze(self, user_instruction: str) -> dict:
        logger.info(f"[InstructionAnalysisAgent] Analyzing user instruction...")
        parser = PydanticOutputParser(pydantic_object=OutputSchema)
        
        # Gemini APIレート制限対応のリトライロジック
        max_retries = 3
        base_delay = 2
        
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    # 指数バックオフ + ランダム要素
                    delay = base_delay * (2 ** (attempt - 1)) + random.uniform(0.5, 1.5)
                    logger.info(f"[InstructionAnalysisAgent] Retrying Gemini API call, attempt {attempt + 1}, waiting {delay:.2f} seconds")
                    time.sleep(delay)
                
                fixing_parser = OutputFixingParser.from_llm(
                    parser=parser, 
                    llm=ChatGoogleGenerativeAI(
                        model="gemini-2.5-pro-preview-06-05", 
                        temperature=0.2, 
                        google_api_key=Config.GOOGLE_API_KEY,
                        timeout=180  # 3分タイムアウト
                    )
                )
                
                # プロンプトを明確に構造化してuser_instructionを強調
                prompt = f"""
{INSTRUCTION_ANALYSIS_PROMPT}

=== USER REQUIREMENTS TO ANALYZE ===
{user_instruction}

=== OUTPUT FORMAT INSTRUCTIONS ===
{parser.get_format_instructions()}

IMPORTANT: Focus on the user requirements above and transform them into the specified JSON format. Analyze every detail mentioned by the user and create comprehensive page specifications.
"""
                logger.debug(f"[InstructionAnalysisAgent] Using INSTRUCTION_ANALYSIS_PROMPT from prompts.py")
                logger.debug(f"[InstructionAnalysisAgent] User instruction length: {len(user_instruction)} characters")
                logger.debug(f"[InstructionAnalysisAgent] Full prompt constructed")
                
                # レート制限回避のための軽微な遅延
                if attempt == 0:
                    time.sleep(random.uniform(0.3, 0.8))
                
                llm = ChatGoogleGenerativeAI(
                    model="gemini-2.5-pro-preview-06-05", 
                    temperature=0.2, 
                    google_api_key=Config.GOOGLE_API_KEY,
                    timeout=180  # 3分タイムアウト
                )
                response = llm.invoke(prompt)
                logger.info(f"[InstructionAnalysisAgent] Successfully called Gemini API on attempt {attempt + 1}")
                
                try:
                    result = fixing_parser.parse(response.content)
                    logger.debug(f"[InstructionAnalysisAgent] Successfully parsed result with {len(result.pages)} pages")
                    logger.info(f"[InstructionAnalysisAgent] Analysis complete - generated {len(result.pages)} pages: {[p.name for p in result.pages]}")
                    return result.dict()
                except Exception as e:
                    logger.warning(f"[InstructionAnalysisAgent] OutputFixingParser failed on attempt {attempt + 1}: {e}")
                    logger.debug(f"[InstructionAnalysisAgent] Raw response content: {response.content[:500]}...")
                    if attempt == max_retries - 1:
                        logger.error(f"[InstructionAnalysisAgent] All parsing attempts failed, returning empty result")
                        return {"overall_design": "", "pages": [], "siteMap": []}
                    continue
                
            except (ResourceExhausted, TooManyRequests) as e:
                logger.warning(f"[InstructionAnalysisAgent] Rate limit hit on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    logger.error(f"[InstructionAnalysisAgent] Rate limit exceeded after {max_retries} attempts")
                    return {"overall_design": "", "pages": [], "siteMap": []}
                continue
                
            except Exception as e:
                logger.warning(f"[InstructionAnalysisAgent] API call failed on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    logger.error(f"[InstructionAnalysisAgent] API call failed after {max_retries} attempts")
                    return {"overall_design": "", "pages": [], "siteMap": []}
                continue
        
        # すべてのリトライが失敗した場合
        logger.error(f"[InstructionAnalysisAgent] All retry attempts failed")
        return {"overall_design": "", "pages": [], "siteMap": []} 