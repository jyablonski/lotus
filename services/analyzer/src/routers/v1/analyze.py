# old endpoint
# from fastapi import APIRouter, Body, Depends, HTTPException, Response, status
# from sqlalchemy.orm import Session

# from src.crud.journal_details import create_or_update_analysis
# from src.dependencies import get_db
# from src.schemas.analyze import AnalyzeRequest
# from src.text_analyzer import analyze_text

# router = APIRouter()


# @router.post("/journals/{journal_id}/analyze", status_code=status.HTTP_204_NO_CONTENT)
# def analyze_journal_entry(
#     journal_id: int,
#     req: AnalyzeRequest = Body(...),
#     db: Session = Depends(get_db),
# ):
#     # run analysis on journal text
#     result = analyze_text(req.text)

#     # save journal analysis to database
#     try:
#         create_or_update_analysis(db=db, journal_id=journal_id, analysis=result)
#     except Exception:
#         raise HTTPException(status_code=500, detail="Failed to save analysis")

#     return Response(status_code=status.HTTP_204_NO_CONTENT)
