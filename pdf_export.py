"""PDF导出 — 将题目导出为PDF文件"""
import io
from pathlib import Path

def export_questions_pdf(questions: list, title: str = "题目集") -> bytes:
    """将题目列表导出为PDF"""
    try:
        from fpdf import FPDF
        
        pdf = FPDF()
        pdf.add_page()
        
        # Try to use Chinese font
        font_path = "/System/Library/Fonts/STHeiti Medium.ttc"
        try:
            pdf.add_font("CN", "", font_path, uni=True)
            pdf.set_font("CN", "", 11)
        except:
            pdf.set_font("Helvetica", "", 11)
        
        pdf.cell(0, 12, title, ln=True, align="C")
        pdf.ln(6)
        
        for i, q in enumerate(questions, 1):
            q_text = q.get("q", "")
            opts = q.get("opts", [])
            ans = q.get("ans", "")
            exp = q.get("exp", "")
            source = q.get("source", "")
            chapter = q.get("chapter", "")
            
            # Question
            pdf.set_font("CN", "", 10)
            pdf.multi_cell(0, 7, f"{i}. {q_text}")
            if chapter:
                pdf.set_font("CN", "", 8)
                pdf.cell(0, 6, f"[{chapter}]", ln=True)
                pdf.set_font("CN", "", 10)
            
            # Options
            for opt in opts:
                pdf.multi_cell(0, 6, f"    {opt}")
            
            # Answer
            pdf.set_font("CN", "", 9)
            pdf.cell(0, 7, f"答案: {ans}", ln=True)
            
            # Explanation
            if exp:
                pdf.set_font("CN", "", 8)
                pdf.multi_cell(0, 6, f"解析: {exp}")
            
            # Source
            if source:
                pdf.set_font("CN", "", 7)
                pdf.cell(0, 5, f"来源: {source}", ln=True)
            
            pdf.ln(4)
        
        return pdf.output()
    except ImportError:
        # Fallback: plain text
        output = f"{title}\n\n"
        for i, q in enumerate(questions, 1):
            output += f"{i}. {q.get('q','')}\n"
            for opt in q.get('opts', []):
                output += f"    {opt}\n"
            output += f"答案: {q.get('ans','')}\n"
            if q.get('exp'):
                output += f"解析: {q['exp']}\n"
            if q.get('source'):
                output += f"来源: {q['source']}\n"
            output += "\n"
        return output.encode('utf-8')

def export_errors_pdf(username: str, subject: str) -> bytes:
    """导出用户的错题本为PDF"""
    from error_book import get_errors
    errors = get_errors(username, subject)
    questions = [e["question"] for e in errors if not e.get("mastered")]
    for e in errors:
        if not e.get("mastered"):
            q = e["question"]
            q["user_ans"] = e.get("user_answer", "")
    return export_questions_pdf(questions, f"错题本 - {subject}")
