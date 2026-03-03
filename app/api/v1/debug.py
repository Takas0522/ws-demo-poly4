"""デバッグ用エンドポイント (開発・検証目的のみ)"""
from fastapi import APIRouter, Depends
from ...utils.dependencies import get_current_user

router = APIRouter(prefix="/debug", tags=["Debug"])


@router.get("/error500")
async def trigger_500_error(
    current_user: dict = Depends(get_current_user),
):
    """意図的に500エラーを発生させるデバッグ用エンドポイント"""
    raise RuntimeError("意図的な500エラー: デバッグ用エンドポイントが呼ばれました")
