from fastapi import APIRouter
from sar_agent.core.llm_engine import LLMEngine
from sar_agent.core.report_builder import build_pdf_report, build_xml_report

router = APIRouter()
llm = LLMEngine()

@router.post("/generate")
def generate_report(input_text: str):
    prompt = f"""
    You are a compliance reporting assistant. 
    Convert the following suspicious activity details into a structured SAR/STR report:
    {input_text}
    """
    llm_output = llm.infer(prompt, max_tokens=400)

    # Save as both PDF + XML
    pdf_path = build_pdf_report(llm_output, "sar_report.pdf")
    xml_path = build_xml_report({"ReportText": llm_output}, "sar_report.xml")

    return {
        "message": "Report generated successfully",
        "pdf_report": pdf_path,
        "xml_report": xml_path,
        "preview": llm_output[:300]
    }
