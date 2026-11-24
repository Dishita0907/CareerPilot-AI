# CareerPilot AI

CareerPilot helps job seekers compare their experience with real employer listings. Paste a résumé, set a career goal and location, and inspect five ranked jobs with employer links, score breakdowns, and skills to review.

**[Try the public job explorer](https://dishita0907.github.io/CareerPilot-AI/)** · **[Check the integration build](https://github.com/Dishita0907/CareerPilot-AI/actions/workflows/check.yml)**

## Dataset

The bundled snapshot contains 770 unique English-language Stripe postings with listing content, retrieved November 24, 2026 from the public [Greenhouse Job Board API](https://boards-api.greenhouse.io/v1/boards/stripe/jobs?content=true). The source returned 771 postings before filtering. Every row includes the employer's job ID, title, location, update timestamp, and application URL. The corpus covers a single employer. Openings can close after collection.

The importer derives skills from the minimum-qualifications section using an explicit vocabulary. It extracts the first numeric years-of-experience expression in that section, which may refer to a specific skill. Empty values mean the parser found no usable evidence. Read the full employer listing to check eligibility and alternatives.

Refresh from the project root with `python scripts/refresh.py`, then rebuild the app. Regenerate the public preview with `cd web && npm ci && VITE_PREVIEW=1 npm run build -- --outDir ../docs --emptyOutDir && touch ../docs/.nojekyll`.

## Run the full app

Requires Docker with Compose. From the repository root:

```sh
docker compose up --build
```

Open **http://localhost:8000**. FastAPI also serves its API reference at **/docs**. PostgreSQL stores preferences, extracted skills, and conversation history in a named volume. A random bearer token identifies each browser workspace. Treat that token like a password. Clearing browser storage loses access to that workspace. The default Compose configuration binds the app to the local machine.

### Enable the OpenAI agent

Set these in a local `.env` file and recreate the app with `docker compose up --build`:

```dotenv
OPENAI_API_KEY=your-key-here
EMBEDDING_PROVIDER=openai
```

The key enables the LangChain tool-calling advisor. The embedding setting switches retrieval from local latent semantic analysis to OpenAI text-embedding-3-small. Model use incurs charges to the supplied account. The index is built on the first search after startup. OpenAI embeddings receive job documents and search queries; the OpenAI advisor receives the profile, retrieved evidence, question, and up to eight recent messages. Raw uploaded PDFs are parsed in memory.

## How recommendations work

1. React collects résumé text or a text-based PDF, a career goal, location, and optional years of experience.
2. FastAPI extracts recognized skills and stores the resulting profile in PostgreSQL.
3. LangGraph runs retrieval and advice. FAISS compares normalized dense vectors using inner product. Local mode learns its vector space from the job snapshot using TF-IDF and truncated SVD.
4. A weighted score combines semantic similarity (45%), overlap with skills mentioned in minimum qualifications (30%), numeric experience fit (15%), and location text match (10%). Missing factors are omitted and remaining weights are normalized. The score is a ranking heuristic, not a probability of employment.
5. The OpenAI agent can call résumé analysis, job discovery, skill-gap, and guidance tools. The local advisor gives a deterministic explanation from retrieved records. Successful exchanges are saved together in a database transaction.

## Public preview

GitHub Pages serves a React explorer from the `docs/` directory. It runs keyword-based ranking and skill comparison locally in the visitor's browser. It supports pasted text and keeps recent searches on that device. Run the full app for PDF ingestion, vector search, PostgreSQL memory, and OpenAI conversations.

## Verification

The GitHub Actions workflow builds the React client and runs `tests/smoke.py` against a PostgreSQL service. The integration check verifies retrieval, source URLs, cross-session isolation, saved conversation history, and invalid PDF handling. No OpenAI key is required for these checks.
