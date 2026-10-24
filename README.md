# Accessibility Agent

An AI agent that scans a web page for accessibility problems, fixes them,
re-scans to verify each fix, and retries with feedback if a fix did not work.

## How it works
1. Downloads the page HTML and scans it (rule-based checker, no AI).
2. For each issue, asks an AI model for a fixed HTML element.
3. Applies the fix and re-scans. If the issue count did not drop, the agent
   tells the model what failed and retries (up to 3 times).
4. Writes `report.html` (before/after for every issue) and `fixed_page.html`.

## Checks
Images without alt, buttons/links without a name, form inputs without a label,
page language missing.

## Components (disclosure)
| Part | What it does | Is it AI? | License |
|---|---|---|---|
| scanner.py (our code) | Finds issues | No | MIT |
| agent.py (our code) | Agent loop: fix, verify, retry | Logic only | MIT |
| gpt-4o-mini (via DNotifier API) | Writes the fixed HTML | Yes | Provider terms |
| dnotifier Python SDK | Hackathon-provided API client | No | Proprietary |
| requests | Downloads pages | No | Apache 2.0 |
| beautifulsoup4 | Parses HTML | No | MIT |

## No mock data
Every result comes from a live scan of the URL you provide.

## Setup
    pip install -r requirements.txt
    copy config.example.py config.py   (then add your own credentials)
    python agent.py https://example.com

## Limitations (honest)
- The scanner reads raw HTML only, so content created by JavaScript is not seen.
- The AI does not see the images, it decides from the markup (file name,
  context). Decorative images get empty alt text.
- The AI model is configurable in agent.py (`PROVIDER`, `MODEL`), but this
  demo uses an OpenAI model through the hackathon-provided DNotifier API.
  It does not use Gemma.

## License
MIT (our code). Third-party components keep their own licenses.