"""
For Development Only Na!!!
"""

import requests
import time
from tqdm import tqdm
from difflib import SequenceMatcher
from django.core.management.base import BaseCommand
from api.models import Paper


#def similar(a, b):
#   """Calculate similarity between two strings (0.0–1.0)."""
#  return SequenceMatcher(None, a.lower(), b.lower()).ratio()


class Command(BaseCommand):
    help = "Fetch papers automatically from CrossRef (and enrich with Semantic Scholar) and save to DB"

    def add_arguments(self, parser):
        parser.add_argument("--author", type=str, help="Author name to search")
        parser.add_argument("--query", type=str, help="Keyword or topic to search")
        parser.add_argument("--start", type=int, help="Start year")
        parser.add_argument("--end", type=int, help="End year")

    def handle(self, *args, **options):
        author = options.get("author")
        query = options.get("query")
        start_year = options.get("start")
        end_year = options.get("end")

        if not author and not query:
            self.stdout.write(self.style.ERROR("Please provide --author or --query"))
            return

        target_author = author.lower().strip() if author else None
        url = "https://api.crossref.org/works"
        rows_per_page = 1000
        offset = 0
        total_fetched = 0

        # Query setup
        base_params = {
            "rows": rows_per_page,
            "filter": f"from-pub-date:{start_year},until-pub-date:{end_year}"
                      if start_year and end_year else None,
        }
        if author:
            base_params["query.author"] = author
            self.stdout.write(self.style.NOTICE(f"🔍 Searching by author: {author} ({start_year}-{end_year})"))
        if query:
            base_params["query"] = query
            self.stdout.write(self.style.NOTICE(f"🔍 Searching by keyword: {query} ({start_year}-{end_year})"))

        base_params = {k: v for k, v in base_params.items() if v is not None}

        # First API call to get total
        first_resp = requests.get(url, params={**base_params, "offset": 0})
        if first_resp.status_code != 200:
            self.stdout.write(self.style.ERROR(f"CrossRef API error ({first_resp.status_code})"))
            return

        total_results = first_resp.json().get("message", {}).get("total-results", 0)
        if total_results == 0:
            self.stdout.write(self.style.WARNING("No papers found."))
            return

        self.stdout.write(self.style.NOTICE(f"📚 Total available papers: {total_results}"))
        time.sleep(1)

        # Progress bar
        with tqdm(total=total_results, desc="Fetching papers", unit="paper", dynamic_ncols=True) as pbar:
            while True:
                params = base_params.copy()
                params["offset"] = offset

                response = requests.get(url, params=params)
                if response.status_code != 200:
                    self.stdout.write(self.style.ERROR(f"CrossRef API error: {response.status_code}"))
                    break

                data = response.json().get("message", {})
                items = data.get("items", [])
                if not items:
                    break

                for item in items:
                    doi = item.get("DOI")
                    title = " ".join(item.get("title", [])) or "(No Title)"
                    year = None
                    if "published-print" in item:
                        year = item["published-print"]["date-parts"][0][0]
                    elif "published-online" in item:
                        year = item["published-online"]["date-parts"][0][0]

                    authors = []
                    match_found = False

                    for a in item.get("author", []):
                        given = a.get("given", "")
                        family = a.get("family", "")
                        full_name = f"{given} {family}".strip()

                        # author matching
                        if target_author:
                            if full_name.lower() == target_author:
                                match_found = True
                            """
                            elif similar(full_name, target_author) >= 0.9:
                                match_found = True
                            """
                            
                        authors.append(full_name)

                    # หากไม่มี match เลย ข้าม
                    if target_author and not match_found:
                        pbar.update(1)
                        continue

                    venue = item.get("container-title", [None])[0]
                    url_link = item.get("URL")

                    pbar.set_postfix_str(f"Now: {title[:60]}...", refresh=True)

                    # Semantic Scholar enrichment
                    abstract, fields_of_study, citation_count = None, None, 0
                    if doi:
                        s2_url = f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}"
                        s2_params = {"fields": "title,abstract,fieldsOfStudy,citationCount"}
                        s2_resp = requests.get(s2_url, params=s2_params)
                        if s2_resp.status_code == 200:
                            s2_data = s2_resp.json()
                            abstract = s2_data.get("abstract")
                            fields_of_study = ",".join(s2_data.get("fieldsOfStudy", []) or [])
                            citation_count = s2_data.get("citationCount", 0)

                    # Save to DB
                    Paper.objects.get_or_create(
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

                    pbar.update(1)

                offset += rows_per_page
                total_fetched += len(items)

                if offset >= total_results:
                    break

                time.sleep(1)

        self.stdout.write(self.style.SUCCESS(f"\n✅ Total papers fetched and saved: {total_fetched}"))
