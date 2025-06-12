# planner_ai.py – PlannerAI v2.3
"""
PlannerAI – End‑to‑end planning & research assistant (verbose + token logging)
Upgraded planning schema with unique IDs, estimates, acceptance criteria, deliverables, tags/layer, status flags, tech‑stack block, and risk linkage.
"""

import os
import re
import json
import datetime
import logging
from pathlib import Path
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

# ---------- logging setup ----------------------------------------------------
logging.basicConfig(format="[%(levelname)s] %(message)s", level=logging.INFO)
log = logging.getLogger("PlannerAI")

# ---------- optional search tool --------------------------------------------
try:
    from langchain_community.tools.tavily_search import TavilySearchResults

    _TAVILY_AVAILABLE = True
except ImportError:
    _TAVILY_AVAILABLE = False

# ---------- bootstrap --------------------------------------------------------
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("GEMINI_API_KEY not found")

gemini = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key=api_key,
    temperature=0.7,
)

if _TAVILY_AVAILABLE and os.getenv("TAVILY_API_KEY"):
    search_tool = TavilySearchResults(k=5, api_key=os.getenv("TAVILY_API_KEY"))
    log.info("Tavily search enabled")
else:
    search_tool = None
    log.info("Running in LLM-only mode (no live search)")

# ---------- helpers ----------------------------------------------------------
PLANS_DIR = Path(__file__).parent / "plans"
PLANS_DIR.mkdir(parents=True, exist_ok=True)

TOKEN_USAGE = {"prompt": 0, "completion": 0}

def _timestamp() -> str:
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

def _slugify(text: str) -> str:
    return re.sub(r"[^\w]+", "_", text).strip("_").lower()[:60]


def _count_tokens(text: str) -> int:
    try:
        return gemini.get_num_tokens(text)
    except Exception:
        return max(1, len(text) // 4)


def _add_token_usage(prompt_tokens: int, completion_tokens: int):
    TOKEN_USAGE["prompt"] += prompt_tokens
    TOKEN_USAGE["completion"] += completion_tokens


def save_json(data: dict, stem: str) -> str:
    path = PLANS_DIR / f"{stem}_{_timestamp()}.json"
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return str(path)

# ---------- PlanningAgent ----------------------------------------------------
PLANNING_SYS_PROMPT = """
You are a senior software project planner.
Return ONE valid **JSON** object that captures the entire project plan.

Schema (curly‑braces escaped so the template engine doesn’t treat them as variables):
{{{{
  "project_name": string,
  "overview": string,
  "tech_stack": {{{{ "frontend": string, "backend": string, "database": string }}}},
  "milestones": [
    {{{{
      "id": string,
      "name": string,
      "description": string,
      "status": "pending",
      "steps": [
        {{{{
          "id": string,
          "title": string,
          "description": string,
          "reasoning": string,
          "layer": "frontend"|"backend"|"devops"|"database"|"design",
          "tags": [string],
          "acceptance": string,
          "deliverables": [string],
          "dependencies": [string],
          "status": "pending",
          "resources": []
        }}}}, … as many necessary steps per milestone …
      ]
    }}}}, …
  ],
  "success_criteria": [string],
  "risks": [
    {{{{
      "description": string,
      "reasoning": string,
      "impact": "high"|"medium"|"low",
      "likelihood": "high"|"medium"|"low",
      "mitigation": [string],
      "affects_steps": [string]
    }}}}
  ]
}}}}

Rules:
• IDs must be globally unique; dependencies reference those IDs.
• Every step includes acceptance, deliverables, estimate_hours, status.
• Use plain JSON, no markdown fences, no comments.
"""

planning_prompt = ChatPromptTemplate.from_messages([
    ("system", PLANNING_SYS_PROMPT),
    ("human", "Create a complete project plan for: {project_request}")
])


def generate_plan(project_request: str) -> dict:
    prompt_tokens = _count_tokens(PLANNING_SYS_PROMPT + project_request)
    log.info(f"[Planning] Prompt tokens ≈ {prompt_tokens}")

    result = (planning_prompt | gemini).invoke({"project_request": project_request})
    content = re.sub(r"```[a-zA-Z]*", "", result.content).strip("`").strip()
    completion_tokens = _count_tokens(content)
    _add_token_usage(prompt_tokens, completion_tokens)
    log.info(f"[Planning] Completion tokens ≈ {completion_tokens}")

    try:
        plan = json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON from Gemini: {e}\n---\n{content[:400]}")
    log.info("[Planning] Plan generated successfully")
    return plan

# ---------- ResearchAgent ----------------------------------------------------
RESEARCH_SYS_PROMPT = """
You are a diligent technical researcher. For the given *step* description produce
up to 5 helpful online resources (docs, blog posts, videos, libraries, etc.).
Return a JSON array of objects {"title", "url", "snippet" (≤120 chars)}.
"""

research_prompt = ChatPromptTemplate.from_messages([
    ("system", RESEARCH_SYS_PROMPT),
    ("human", "Provide resources for: {topic}")
])


def _resources_via_llm(topic: str):
    prompt_tokens = _count_tokens(RESEARCH_SYS_PROMPT + topic)
    resp = (research_prompt | gemini).invoke({"topic": topic})
    txt = re.sub(r"```[a-zA-Z]*", "", resp.content).rstrip("`").strip()
    completion_tokens = _count_tokens(txt)
    _add_token_usage(prompt_tokens, completion_tokens)
    try:
        return json.loads(txt)
    except Exception:
        return [{"title": "Resource list", "url": "", "snippet": txt}]


def _resources_via_search(topic: str):
    if not search_tool:
        return _resources_via_llm(topic)
    results = search_tool.run(topic)
    out = [{"title": r.get("title", "link"), "url": r.get("url", ""), "snippet": r.get("snippet", "")[:120]} for r in results]
    return out or _resources_via_llm(topic)


def enrich_with_research(plan: dict) -> dict:
    log.info("[Research] Adding resources …")
    for ms in plan.get("milestones", []):
        for step in ms.get("steps", []):
            topic = f"{plan['project_name']} – {step['title']}"
            step["resources"] = _resources_via_search(topic)
    log.info("[Research] Done")
    return plan

# ---------- coordinator ------------------------------------------------------

def build_full_project_package(request: str):
    log.info("========= PlannerAI run start =========")
    plan = generate_plan(request)
    plan = enrich_with_research(plan)
    path = save_json(plan, f"{_slugify(plan['project_name'])}_full_plan")
    log.info(f"[Save] Plan saved to {path}")
    log.info(f"[Tokens] prompt≈{TOKEN_USAGE['prompt']} completion≈{TOKEN_USAGE['completion']} total≈{sum(TOKEN_USAGE.values())}")
    log.info("========= PlannerAI run end =========")
    return path, plan

# ---------- CLI --------------------------------------------------------------
if __name__ == "__main__":
    print("\nPlannerAI – project planning + research (v2.3)")
    while True:
        user_text = input("\n≫ ")
        if user_text.lower() in {"exit", "quit", "bye"}:
            print("Goodbye!")
            break
        try:
            p, _ = build_full_project_package(user_text)
            print(f"\n✅ Plan saved to {p}\n")
        except Exception as e:
            print(f"⚠️  {e}\n")
