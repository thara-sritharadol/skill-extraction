import requests
from django.core.management.base import BaseCommand
from api.models import Paper


class Command(BaseCommand):
    help = "Fetch papers from CrossRef (and enrich with Semantic Scholar) and save to DB"

    def add_arguments(self, parser):
        parser.add_argument("--author", type=str, help="Author name to search")
        parser.add_argument("--start", type=int, help="Start year")
        parser.add_argument("--end", type=int, help="End year")
        parser.add_argument("--rows", type=int, default=5, help="Number of results")

    def handle(self, *args, **options):
        author = options.get("author")
        start_year = options.get("start")
        end_year = options.get("end")
        rows = options.get("rows")

        if not author:
            self.stdout.write(self.style.ERROR("Please provide --author"))
            return

        # Fetch Data From CrossRef
        url = "https://api.crossref.org/works"
        params = {
            "query.author": author,
            "rows": rows,
            "filter": f"from-pub-date:{start_year},until-pub-date:{end_year}"
                      if start_year and end_year else None,
        }
        params = {k: v for k, v in params.items() if v is not None}  # Delete None

        response = requests.get(url, params=params)
        if response.status_code != 200:
            self.stdout.write(self.style.ERROR("CrossRef API error"))
            return

        items = response.json().get("message", {}).get("items", [])
        self.stdout.write(self.style.NOTICE(f"Found {len(items)} papers from CrossRef"))

        for item in items:
            doi = item.get("DOI")
            title = " ".join(item.get("title", []))
            year = None
            if "published-print" in item:
                year = item["published-print"]["date-parts"][0][0]
            elif "published-online" in item:
                year = item["published-online"]["date-parts"][0][0]

            authors = []
            for a in item.get("author", []):
                given = a.get("given", "")
                family = a.get("family", "")
                authors.append(f"{given} {family}".strip())

            venue = item.get("container-title", [None])[0]
            url_link = item.get("URL")

            # Additional Data From Semantic Scholar
            abstract, fields_of_study, citation_count = None, None, 0
            if doi:
                s2_url = f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}"
                s2_params = {"fields": "title,abstract,fieldsOfStudy,citationCount"}
                s2_resp = requests.get(s2_url, params=s2_params)
                if s2_resp.status_code == 200:
                    data = s2_resp.json()
                    abstract = data.get("abstract")
                    fields_of_study = ",".join(data.get("fieldsOfStudy", []) or [])
                    citation_count = data.get("citationCount", 0)

            # Save to DB
            paper, created = Paper.objects.get_or_create(
                doi=doi,
                defaults={
                    "title": title,
                    "authors": ", ".join(authors),
                    "year": year,
                    "venue": venue,
                    "url": url_link,
                    "abstract": abstract,
                    "fields_of_study": fields_of_study,
                    "citation_count": citation_count,
                },
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f"Added: {title} ({year})"))
            else:
                self.stdout.write(self.style.WARNING(f"Skipped (already exists): {title}"))

