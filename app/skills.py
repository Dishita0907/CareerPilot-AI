"""A transparent vocabulary for extracting comparable employer and candidate skills."""
import re

VOCAB = """Python|JavaScript|TypeScript|Java|SQL|PostgreSQL|MySQL|React|Go|Ruby|Rust|Scala|C++|C#|Node.js|Next.js|AWS|GCP|Azure|Docker|Kubernetes|Terraform|Spark|Kafka|Redis|Linux|Git|CI/CD|REST|GraphQL|API|Machine learning|Deep learning|NLP|LLM|AI agents|Data analysis|Statistics|A/B testing|Data modeling|ETL|Tableau|Excel|Salesforce|Product management|Project management|Risk management|Financial analysis|Communication|Stakeholder management|Sales|Marketing|Forecasting|Accounting|Operations|Customer support|Distributed systems|Payments|Fraud|Compliance|Automation|Backend|Frontend|Testing|Analytics""".split("|")
ALIASES = {"Go": r"Golang|(?-i:Go)(?=,|/| programming)", "LLM": r"LLMs?|large language models?", "API": r"APIs?", "NLP": r"NLP|natural language processing", "Machine learning": r"machine learning|ML", "PostgreSQL": r"postgres(?:ql)?"}
PATTERNS = {s: re.compile(r"(?<!\w)(?:" + ALIASES.get(s,re.escape(s)) + r")(?!\w)",re.I) for s in VOCAB}

def skills(text):
    return sorted(s for s, pattern in PATTERNS.items() if pattern.search(text))
