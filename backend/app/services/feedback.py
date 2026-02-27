import language_tool_python

_tool = None

def _get_tool():
    global _tool
    if _tool is None:
        _tool = language_tool_python.LanguageTool("en-US")
    return _tool

def grammar_feedback(text: str, max_items: int = 6):
    text = (text or "").strip()
    if not text:
        return text, []

    try:
        tool = _get_tool()
        matches = tool.check(text)
        corrected = language_tool_python.utils.correct(text, matches)

        corrections = []
        for m in matches[:max_items]:
            suggestion = m.replacements[0] if m.replacements else ""
            # ✅ هنا الفرق
            error_fragment = text[m.offset:m.offset + m.error_length]

            corrections.append({
                "offset": m.offset,
                "error": error_fragment,
                "suggestion": suggestion,
                "rule": getattr(m, "ruleId", ""),
                "message": m.message
            })
        return corrected, corrections
    except Exception:
        return text, []