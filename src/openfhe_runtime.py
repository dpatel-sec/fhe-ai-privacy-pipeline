"""Load OpenFHE from a normal installation or a nearby local source build."""

from __future__ import annotations

import sys
from pathlib import Path


def _load_openfhe():
    try:
        from openfhe import CCParamsBFVRNS, GenCryptoContext, PKESchemeFeature

        return CCParamsBFVRNS, GenCryptoContext, PKESchemeFeature
    except ModuleNotFoundError:
        pass

    # This fallback is helpful when working beside a local OpenFHE source build.
    for directory in Path(__file__).resolve().parents:
        local_package = directory / "openfhe-python-package"
        if local_package.is_dir():
            sys.path.insert(0, str(local_package))
            from openfhe import CCParamsBFVRNS, GenCryptoContext, PKESchemeFeature

            return CCParamsBFVRNS, GenCryptoContext, PKESchemeFeature

    raise RuntimeError(
        "OpenFHE is not installed. Follow the setup guide in docs/INSTALL_OPENFHE.md."
    )


CCParamsBFVRNS, GenCryptoContext, PKESchemeFeature = _load_openfhe()
