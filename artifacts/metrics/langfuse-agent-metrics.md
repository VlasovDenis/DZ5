# Langfuse agent metrics

## Normal run

- Trace name: `ai-smm-multi-agent-run`
- Trace ID: `5ad7e025393088b33b060290fff5fd1b`
- End-to-end latency: 112.28 s
- LLM calls: 6
- Input tokens: 21396
- Output tokens: 4957
- Total tokens: 26353
- Sum of LLM generation latency: 96.85 s
- External API cost: 0.000000

| Step | Model | Input | Output | Total | Latency, s | TTFT, s |
|---|---|---:|---:|---:|---:|---:|
| strategist | qwen3:4b-instruct | 896 | 1950 | 2846 | 33.08 | 7.39 |
| copywriter | qwen3:4b-instruct | 4165 | 608 | 4773 | 14.20 | 5.54 |
| editor | qwen3:4b-instruct | 4503 | 1253 | 5756 | 24.21 | 6.16 |
| copywriter #2 | qwen3:4b-instruct | 6163 | 689 | 6852 | 15.47 | 5.08 |
| editor #2 | qwen3:4b-instruct | 4585 | 222 | 4807 | 5.44 | 2.19 |
| publisher | qwen3:4b-instruct | 1084 | 235 | 1319 | 4.45 | 1.37 |

## Controlled revision run

- Trace name: `ai-smm-forced-revision-run`
- Trace ID: `213ebccb50bdcabc1ab8c082a060e96b`
- End-to-end latency: 116.84 s
- LLM calls: 6
- Input tokens: 20564
- Output tokens: 4319
- Total tokens: 24883
- Sum of LLM generation latency: 101.14 s
- External API cost: 0.000000

| Step | Model | Input | Output | Total | Latency, s | TTFT, s |
|---|---|---:|---:|---:|---:|---:|
| strategist | qwen3:4b-instruct | 896 | 1964 | 2860 | 47.91 | 20.49 |
| copywriter | qwen3:4b-instruct | 4201 | 551 | 4752 | 14.49 | 5.97 |
| editor | qwen3:4b-instruct | 4460 | 725 | 5185 | 15.48 | 4.64 |
| copywriter #2 | qwen3:4b-instruct | 5614 | 544 | 6158 | 12.70 | 4.25 |
| editor #2 | qwen3:4b-instruct | 4454 | 341 | 4795 | 6.80 | 1.61 |
| publisher | qwen3:4b-instruct | 939 | 194 | 1133 | 3.76 | 1.26 |
