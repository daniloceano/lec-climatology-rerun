"""Prevent superseded renderers from emitting scientific replacements."""


def require_corrected_article_results() -> None:
    raise ValueError(
        "BLOCKED superseded five-cluster workflow: use "
        "python -m scripts.article_figures.reproduce_downstream. "
        "The author fixed K=4; archived products remain historical diagnostics."
    )


def require_resolved_figure16() -> None:
    """The definition is resolved; these old entry points remain invalid.

    Author decision: phase EOF loadings with the canonical Figures 5–8 matching.
    The dedicated gate-first wrapper implements that decision. Old renderers
    still contain raw-rank/group-mean alternatives and cannot bypass its gate.
    """
    raise ValueError(
        "BLOCKED Figure 16 / INVALID_AS_REPLACEMENT: this renderer is superseded. "
        "The author confirmed matched phase EOF loadings (definition resolved). "
        "Use python -m scripts.article_figures.reproduce_downstream; "
        "see docs/technical/downstream_reproduction.md."
    )
