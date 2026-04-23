GAP_ANALYSIS_PROMPT = """\
Complete a detailed gap analysis report by looking at my resume and the job description.

First, analyze from the perspective of how well my resume aligns with the job requirements.

Second, complete the same analysis from the lens of the hiring manager — what concerns they
would have, what stands out, and how I would be perceived relative to other candidates.

Third, provide an ATS-style analysis including an estimated match score, missing keywords,
and missed opportunities.

For all three sections, be highly critical, specific, and strategic — not generic. Prioritize
insights that would materially improve my chances of getting an interview and offer.

At the end, provide 3–5 high-impact recommendations that would meaningfully improve my candidacy.

Assume I am targeting a top-tier candidate position and want to be in the top 5–10% of
applicants. Focus on what separates strong candidates from offer-level candidates.

My resume:
{resume_text}

Job description:
{job_text}"""


# The JSON schema example uses {{ }} to escape literal braces in Python's .format()
SCORING_PROMPT = """\
You are evaluating a job posting for a candidate with the following background:
{resume_text}

Score this job posting on a scale of 1–10 using a weighted composite:
- Resume/JD fit (30%): How well does the candidate's experience and language match the role requirements?
- Interview likelihood (30%): Given the typical candidate pool for this role and company, how likely is this candidate to get a call?
- Offer likelihood (40%): If they get the interview, how competitive is their full profile for an offer?

Be realistic and critical. A strong fit does not automatically mean a high score — interview and offer likelihood must reflect actual competitiveness, not just alignment.

Hard gate: If resume/JD alignment is below 75%, return score of 0 and reason only. Do not complete full scoring.

Return JSON only:
{{
  "score": 7.8,
  "gate_passed": true,
  "fit_summary": "2-sentence plain summary of the role",
  "fit_reasons": ["reason 1", "reason 2"],
  "concerns": ["concern 1"],
  "interview_likelihood": "High / Medium / Low + one sentence why",
  "offer_likelihood": "High / Medium / Low + one sentence why",
  "network_flag": "Riipen — Tortise works here" or null,
  "teal_entry": {{
    "title": "GTM Architect",
    "company": "Fellow",
    "url": "https://job.url"
  }}
}}

Job posting:
{job_text}"""


RESUME_TAILORING_PROMPT = """\
You are tailoring a resume for a specific job application.

Master resume:
{resume_text}

Job posting:
{job_text}

Gap analysis findings:
{gap_analysis_output}

Instructions:
- Tailor language, emphasis, and bullet points to align with this specific role
- Prioritize experience most relevant to the role — Lead Gen ETL platform when role involves operations, systems, product, or data
- Do not invent experience or credentials that do not exist in the master resume
- Do not include AXE Media
- Toni Marlow: reference as founder only, no co-founder or queer/trans context unless briefing flags it
- Smart Film business: include only if role involves entrepreneurship, operations, or sales
- Do not change the structure — content tailoring only
- Output the full tailored resume text, ready to paste into a Word doc"""


COVER_LETTER_PROMPT = """\
You are writing a cover letter for a job application.

Candidate resume:
{resume_text}

Job posting:
{job_text}

Gap analysis findings:
{gap_analysis_output}

Rules — follow exactly:
- Tone: confident, direct, warm. Not corporate. Not sycophantic.
- Length: 3 paragraphs maximum
- Never open with "I am excited to apply" or any variation
- Do not reference AXE Media
- Toni Marlow: founder only — no co-founder reference, no queer/trans context unless explicitly flagged
- Lead Gen ETL: include when role involves operations, systems, product, or data
- Smart Film business: include only if role involves entrepreneurship, operations, or sales
- Do not fabricate experience not present in the resume

Output the cover letter text only. No subject line, no header, no commentary."""
