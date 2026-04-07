"""
AI Answer Generator for Question Papers
Uses Google Gemini API to generate answer suggestions for exam questions
"""

import google.generativeai as genai
from django.conf import settings
import json
import re


def configure_gemini():
    """Configure the Gemini API with the API key from settings"""
    api_key = getattr(settings, 'GEMINI_API_KEY', None)
    if not api_key:
        raise ValueError("GEMINI_API_KEY not configured in settings")
    genai.configure(api_key=api_key)


def generate_answer_options(question_text, marks, part_type='A', course_name='', num_options=4):
    """
    Generate multiple answer options for a given question using Gemini AI.
    
    Args:
        question_text: The question text
        marks: Marks for the question (2, 13, or 15)
        part_type: 'A' (2 marks), 'B' (13 marks), or 'C' (15 marks)
        course_name: Name of the course for context
        num_options: Number of answer options to generate (default 4)
    
    Returns:
        list: List of answer option dictionaries with 'answer' and 'brief' keys
    """
    try:
        configure_gemini()
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Determine answer length based on marks
        if part_type == 'A' or marks <= 2:
            answer_guidance = """This is a 2-mark SHORT ANSWER question. Provide:
- A clear, concise definition or explanation (2-3 sentences)
- Include relevant formula if applicable (with variable meanings)
- Keep it brief but complete enough to score full marks"""
        elif part_type == 'B' or marks <= 13:
            answer_guidance = """This is a 13-mark DESCRIPTIVE question. Provide a comprehensive answer with:
- Clear definition of key terms/concepts at the start
- Detailed explanation with 8-12 key points
- All relevant formulas with explanation of variables
- Step-by-step derivation or procedure if applicable
- Diagrams description: [Describe any diagram that should be drawn, e.g., "DIAGRAM: Draw a block diagram showing..."]
- Real-world examples or applications where relevant
- Conclusion or summary statement"""
        else:  # Part C - 15 marks
            answer_guidance = """This is a 15-mark CASE STUDY/PROBLEM SOLVING question. Provide an exhaustive answer with:
- Introduction and context setting
- Clear definitions of all technical terms used
- Complete theoretical background (4-5 points)
- All relevant formulas with detailed explanation of each variable
- Step-by-step solution methodology or procedure
- Diagrams description: [Describe diagrams needed, e.g., "DIAGRAM 1: Flowchart showing...", "DIAGRAM 2: Circuit diagram of..."]
- Numerical examples if applicable
- Advantages, disadvantages, or comparisons where relevant
- Real-world applications and case examples
- Conclusion summarizing key points"""
        
        prompt = f"""You are an expert academic who creates model answers for university exam questions.

Course: {course_name if course_name else 'Engineering/Science'}
Question: {question_text}
Marks: {marks}

{answer_guidance}

IMPORTANT GUIDELINES:
1. The answer depth MUST match the marks allocated - more marks = more detail
2. Always include definitions for technical terms
3. Include ALL relevant formulas with clear explanation of what each variable represents
4. For diagrams, write "[DIAGRAM: description of what to draw]" so students know what diagrams are expected
5. Use proper numbering and formatting for clarity
6. Make answers exam-ready - something a student can memorize and write

Generate exactly {num_options} different but correct answer options for this question. Each answer should be:
1. Academically accurate and complete for the marks allocated
2. Include definitions, formulas, and diagram descriptions as needed
3. Written in clear, structured exam-appropriate language
4. Different in approach or emphasis from other options

Return your response as a JSON array with exactly {num_options} objects, each containing:
- "answer": The full answer text
- "brief": A 1-line summary (max 10 words) describing this answer's approach

Example format:
[
  {{"answer": "Full answer text here...", "brief": "Focuses on theoretical aspects"}},
  {{"answer": "Another answer...", "brief": "Emphasizes practical examples"}}
]

IMPORTANT: Return ONLY the JSON array, no other text or markdown."""

        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Clean up response - remove markdown code blocks if present
        if response_text.startswith('```'):
            response_text = re.sub(r'^```json?\s*', '', response_text)
            response_text = re.sub(r'\s*```$', '', response_text)
        
        # Parse JSON response
        try:
            answers = json.loads(response_text)
            if isinstance(answers, list) and len(answers) > 0:
                return answers[:num_options]
        except json.JSONDecodeError:
            # If JSON parsing fails, try to extract answers from text
            pass
        
        # Fallback: return error message
        return [{"answer": "AI could not generate answers. Please try again.", "brief": "Error"}]
        
    except Exception as e:
        return [{"answer": f"Error generating answers: {str(e)}", "brief": "Error"}]


def generate_single_answer(question_text, marks, part_type='A', course_name=''):
    """
    Generate a single best answer for a question.
    
    Args:
        question_text: The question text
        marks: Marks for the question
        part_type: 'A', 'B', or 'C'
        course_name: Name of the course
    
    Returns:
        str: The generated answer
    """
    try:
        configure_gemini()
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        if part_type == 'A' or marks <= 2:
            answer_guidance = "Provide a concise answer (2-4 sentences). This is a 2-mark question."
        elif part_type == 'B' or marks <= 13:
            answer_guidance = "Provide a detailed answer with key points (8-12 points). This is a 13-mark question."
        else:
            answer_guidance = "Provide a comprehensive answer with examples (12-15 points). This is a 15-mark question."
        
        prompt = f"""You are an expert academic creating a model answer for a university exam.

Course: {course_name if course_name else 'Engineering/Science'}
Question: {question_text}
Marks: {marks}

{answer_guidance}

Provide ONLY the answer text, no additional commentary or formatting instructions."""

        response = model.generate_content(prompt)
        return response.text.strip()
        
    except Exception as e:
        return f"Error: {str(e)}"
