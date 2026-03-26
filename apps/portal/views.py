from django.views.generic import TemplateView


class HomeView(TemplateView):
    template_name = "portal/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "service_categories": [
                    {
                        "title": "Serviços Linguisticos e de Comunicação",
                        "description": "Language services for institutional, academic, and technical material.",
                    },
                    {
                        "title": "Interpreting support",
                        "description": "Professional communication support for meetings, events, and multilingual workflows.",
                    },
                    {
                        "title": "Data storytelling",
                        "description": "Visual explorations that connect language work, output history, and measurable impact.",
                    },
                ],
                "highlights": [
                    "Professional profile for linguistics, translation, and interpreting work.",
                    "Client intake path for commissioned language services.",
                    "A portfolio area for data analysis and visualization projects.",
                ],
            }
        )
        return context
