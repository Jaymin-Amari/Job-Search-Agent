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

GATE CHECK — evaluate this first.
Pass the gate if ANY ONE of these is true:
- Work is directionally relevant: enablement, program ops, RevOps, ecosystem support, community ops, learning/platform ops, systems operations, business analysis, process design, operational or systems auditing
- Company is in a target sector: tech, SaaS, startup ecosystem, innovation, education, health tech, fintech — even if the role is adjacent to the candidate's target
- Organization is government, public sector, publicly funded, or non-profit — any role that isn't actively draining and pays adequately
- Company name, network, or sector puts the candidate in proximity to GTM/RevOps/Product roles within 12–18 months

Fail the gate (return gate_passed: false) only if the role is primarily:
- Financial audit, compliance audit, or regulatory audit
- Accounting, bookkeeping, or financial analysis as the core function
- Customer support or service delivery as the primary responsibility
- Pure event coordination or community networking as a weekly core requirement
- Heavy outbound sales or cold lead generation as the primary function
- Deep technical engineering with no ops or strategic layer

If gate fails, return gate_passed: false with a one-line reason. Stop there.

SCORING — only for roles that pass the gate.
Score 1–10 using this weighted composite:
- Resume/JD fit (30%): Does the candidate's background map to core parts of this role? Directional alignment counts — innovation ecosystem, program ops, systems building, and community platform experience are transferable to a wide range of ops/enablement/BA roles. Score relative to a strong generalist ops background, not a keyword-perfect match.
- Interview likelihood (30%): Given this candidate's profile and the typical hiring pool for this role and organization type, how likely are they to get a screening call? Government, non-profit, and innovation org roles should score higher here given the candidate's background in those environments.
- Offer likelihood (40%): If they get the interview, how competitive is their full profile? For pivot roles at target-sector companies, weigh potential and trajectory alongside direct experience.

Scoring calibration:
- 1–4: Poor directional fit even accounting for transferability
- 5–6: Directionally relevant, credible application, some gaps — worth a look
- 7–8: Solid fit, competitive application, should apply
- 9–10: Exceptional fit, top-tier applicant

A role that passes the gate should floor at 4. A role where the candidate has genuine relevant experience in at least two dimensions should floor at 5.

Do not penalize heavily for title mismatch. Penalize for credential gaps the candidate cannot credibly bridge in an interview.

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
