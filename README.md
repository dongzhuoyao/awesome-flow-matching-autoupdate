# Awesome Flow Matching - Auto Updated

[![Auto Update](https://github.com/YOUR_USERNAME/awesome-flow-matching-autoupdate/actions/workflows/update-papers.yml/badge.svg)](https://github.com/YOUR_USERNAME/awesome-flow-matching-autoupdate/actions/workflows/update-papers.yml)

Automatically curated list of flow matching papers with **10+ citations**.

This repository automatically tracks new flow matching papers from arXiv, OpenAlex, and Semantic Scholar, filtering for quality (minimum 10 citations) and categorizing them using AI.

Original curated list: [awesome-flow-matching](https://github.com/dongzhuoyao/awesome-flow-matching)

---

## Setup

1. Fork this repository
2. Add your OpenAI API key as a GitHub secret named `OPENAI_API_KEY`
3. Update the badge URL in this README with your username
4. The workflow will run daily at 6:00 AM UTC

## How It Works

1. **Sources**: Searches arXiv, OpenAlex, and Semantic Scholar for papers matching:
   - "flow matching"
   - "rectified flow"
   - "stochastic interpolant"
   - "continuous normalizing flow"

2. **Quality Filter**: Only includes papers with **10+ citations**

3. **Deduplication**: Parses the original [awesome-flow-matching](https://github.com/dongzhuoyao/awesome-flow-matching) repo to avoid duplicates

4. **Classification**: Uses OpenAI GPT-4o-mini to categorize papers into:
   - Foundational
   - Theory
   - Schrödinger Bridge
   - Discrete Data
   - Accelerating
   - Applications

5. **Auto-Update**: GitHub Actions runs daily to find and add new papers

---

## Papers

*Papers will be auto-populated after the first run.*

---

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run test
python test_run.py

# Run full update (requires OPENAI_API_KEY)
export OPENAI_API_KEY=your_key_here
python src/main.py
```

## Configuration

Edit `config.yaml` to customize:
- Search terms
- Minimum citation threshold
- Top-tier venues
- Categories

## License

MIT
