from fastapi import APIRouter

from ..providers.registry import capability_status
from ..schemas_tools import ProviderStatusOut

router = APIRouter()


@router.get("/providers/status", response_model=ProviderStatusOut)
def providers_status():
    """Which capabilities exist and how trustworthy each one is. Never contains key values."""
    return ProviderStatusOut(capabilities=capability_status())
