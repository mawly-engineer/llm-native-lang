"""LLM-Native Language - A language-native development ecosystem.

This package provides runtime support for LND (LLM-Native Declaration) and
LNC (LLM-Native Contract) formats, including interpreters, validators,
and replay systems.
"""

__version__ = "0.2.0"
__author__ = "KAIRO Evolution Team"
__license__ = "MIT"

# Import key modules at package level for convenience
try:
    from .runtime import interpreter_runtime as interpreter
    from .runtime import replay_harness
except ImportError:
    # Runtime modules may not be available in minimal installs
    interpreter = None
    replay_harness = None

try:
    from .validators import lnd_validate
    from .validators import lnc_validate
except ImportError:
    # Validators may not be available in minimal installs
    lnd_validate = None
    lnc_validate = None

__all__ = [
    "__version__",
    "interpreter",
    "replay_harness",
    "lnd_validate",
    "lnc_validate",
]