# analyzer.py
import anthropic
import json

client = anthropic.Anthropic()  # uses ANTHROPIC_API_KEY from .env

def analyze_job_batch(job_descriptions: list[dict]) -> dict:
    prompt = f"""
    Analyze these job postings and return a JSON object with:
    
    1. top_skills: ranked list of most requested technical skills
    2. top_soft_skills: ranked list of soft skills mentioned
    3. seniority_signals: words/phrases that indicate seniority level
    4. salary_insights: any patterns in compensation mentioned
    5. resume_recommendations: specific, actionable bullet points 
       to tailor a resume for these roles
    6. keyword_frequency: dict of important keywords and how often 
       they appear across postings
    7. emerging_trends: skills or tools appearing in newer postings
       that seem to be growing in demand
    
    Job postings:
    {json.dumps(job_descriptions, indent=2)}
    
    Return only valid JSON, no explanation.
    """

    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    if response.content and response.content[0].type == "text":
        return json.loads(response.content[0].text)
    else:
        raise ValueError(f"Unexpected response: {response}")


def generate_resume_tips(job_descriptions: list, your_resume: str) -> str:
    prompt = f"""
    Given these job postings and my current resume, provide specific 
    actionable recommendations:
    
    1. Keywords I'm missing that appear frequently in these postings
    2. Skills I should highlight more prominently  
    3. Suggested bullet point rewrites to better match job language
    4. Any gaps between what's being asked for and what I'm showing
    
    Job postings:
    {json.dumps(job_descriptions, indent=2)}
    
    My resume:
    {your_resume}
    """

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    if response.content and response.content[0].type == "text":
        return json.loads(response.content[0].text)
    else:
        raise ValueError(f"Unexpected response: {response}")