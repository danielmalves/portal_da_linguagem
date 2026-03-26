from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from ..quotes.models import Quote, QuoteStatus

@login_required
@require_POST

def accept_quote(request, quote_id):
    quote = get_object_or_404(Quote, pk=quote_id)

    # Apenas o cliente que possuir a solicitação pode aceitar
    if quote.service_request.customer != request.user.customer_profile:
        return render(request, "partials/error.html", {"message": "Forbidden"}, status=403)

    if quote.status != QuoteStatus.SENT:
        return render(request, "partials/error.html", {"message": "Quote not in SENT state"}, status=400)

    # Em v1, reusar a cotação como um instantâneo
    quote.accept(terms_snapshot=quote.terms_snapshot or "")

    # Retornar um painel de cotação parcial atualizado
    return render(request, "quotes/_quote_panel.html", {"quote": quote, "req": quote.service_request})