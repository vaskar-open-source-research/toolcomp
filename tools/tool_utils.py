import contextlib
import datetime
import re
import sys
from io import StringIO
import dateutil
from dateutil import parser
import pytz

def is_date(string, fuzzy=False):
    # Parse a string into a date and check its validity
    try:
        parser.parse(string, fuzzy=fuzzy)
        return True
    except ValueError:
        return False

def get_current_date():
    # Get the current date
    current_date = datetime.datetime.now(pytz.timezone("America/Los_Angeles")).strftime("%B %d, %Y")
    return current_date

def format_date(d):
    current_date = get_current_date()
    # Standardize the date format for each search result
    date = parser.parse(current_date, fuzzy=True).strftime("%b %d, %Y")
    if d is None:
        return None

    for t in ["second", "minute", "hour"]:
        if f"{t} ago" in d or f"{t}s ago" in d:
            return date

    t = "day"
    if f"{t} ago" in d or f"{t}s ago" in d:
        n_days = int(re.search("(\d+) days? ago", d).group(1))  # noqa: W605
        return (
            datetime.datetime.strptime(date, "%b %d, %Y") - datetime.timedelta(days=n_days)
        ).strftime("%b %d, %Y")

    try:
        return parser.parse(d, fuzzy=True).strftime("%b %d, %Y")
    except ValueError:
        for x in d.split():
            if is_date(x):
                return parser.parse(x, fuzzy=True).strftime("%b %d, %Y")

def extract_source_webpage(link):
    # Extract source webpage
    return (
        link.strip()
        .replace("https://www.", "")
        .replace("http://www.", "")
        .replace("https://", "")
        .replace("http://", "")
        .split("/")[0]
    )

def simplify_displayed_link(displayed_link):
    # Simplify displayed link
    if displayed_link is None:
        return None
    return extract_source_webpage(displayed_link.split(" › ")[0])

def format_search_results(search_data, title_field=None, highlight_field=None):
    # Standardize search results as shown in Figure 3 (left) in the paper
    field = "snippet_highlighted_words"
    if field in search_data and isinstance(search_data[field], list):
        search_data[field] = " | ".join(search_data[field])

    field = "displayed_link"
    if field in search_data:
        search_data[field] = simplify_displayed_link(search_data[field])

    # edge case 1
    if search_data.get("type") == "local_time":
        source = search_data.get("displayed_link")
        date = format_date(search_data.get("date"))
        title = search_data.get("title")

        snippet = search_data.get("snippet")
        if snippet is None and "result" in search_data:
            if "extensions" in search_data and isinstance(search_data["extensions"], list):
                snippet = "\n\t".join([search_data["result"]] + search_data["extensions"])
            else:
                snippet = search_data["result"]

        highlight = search_data.get("snippet_highlighted_words")
        if highlight is None and "result" in search_data:
            highlight = search_data["result"]

    # edge case 2
    elif "type" in search_data and search_data["type"] == "population_result":
        source = search_data.get("displayed_link")
        if source is None and "sources" in search_data:
            if isinstance(search_data["sources"], list) and "link" in search_data["sources"][0]:
                source = extract_source_webpage(search_data["sources"][0]["link"])

        date = format_date(search_data.get("date"))
        if date is None and "year" in search_data:
            date = format_date(search_data["year"])

        title = search_data.get("title")

        snippet = search_data.get("snippet")
        if snippet is None and "population" in search_data:
            if "place" in search_data:
                snippet = "\n\t".join(
                    [
                        f"{search_data['place']} / Population",
                    ]
                    + [
                        search_data["population"],
                    ]
                )
            else:
                snippet = search_data["population"]

        highlight = search_data.get("snippet_highlighted_words")
        if highlight is None and "population" in search_data:
            highlight = search_data["population"]

    else:
        source = search_data.get("displayed_link")
        date = format_date(search_data.get("date"))
        title = search_data.get("title") if title_field is None else search_data.get(title_field)
        highlight = (
            search_data.get("snippet_highlighted_words")
            if highlight_field is None
            else search_data.get(highlight_field)
        )
        snippet = search_data.get("snippet", "")

        if "rich_snippet" in search_data:
            for key in ["top", "bottom"]:
                if (
                    key in search_data["rich_snippet"]
                    and "extensions" in search_data["rich_snippet"][key]
                ):
                    snippet = "\n\t".join(
                        [snippet] + search_data["rich_snippet"][key]["extensions"]
                    )

        if "list" in search_data:
            assert isinstance(search_data["list"], list)
            snippet = "\n\t".join([snippet] + search_data["list"])

        if "contents" in search_data and "table" in search_data["contents"]:
            tbl = search_data["contents"]["table"]
            assert isinstance(tbl, list)
            snippet += "\n"
            for row in tbl:
                snippet += f'\n{",".join(row)}'

        if snippet is not None and snippet.strip() == "":
            snippet = None

    return {
        "source": source,
        "date": date,
        "title": title,
        "snippet": snippet,
        "highlight": highlight,
    }

def format_knowledge_graph(search_data):
    # Standardize knowledge graphs as shown in Figure 3 (left) in the paper
    source = None
    if "source" in search_data and "link" in search_data["source"]:
        source = extract_source_webpage(search_data["source"]["link"])

    date = None

    title = None
    if "title" in search_data:
        title = search_data["title"]
        if "type" in search_data:
            title += f"\n\t{search_data['type']}"

    snippet = ""
    for field in search_data:
        if (
            (field not in ["title", "type", "kgmid"])
            and ("_link" not in field)
            and ("_stick" not in field)
            and isinstance(search_data[field], str)
            and not search_data[field].startswith("http")
        ):
            snippet += f"\n\t{field}: {search_data[field]}"

    if snippet.strip() == "":
        snippet = None
    else:
        snippet = snippet.strip()

    highlight = None

    return {
        "source": source,
        "date": date,
        "title": title,
        "snippet": snippet,
        "highlight": highlight,
    }


@contextlib.contextmanager
def stdoutIO(stdout=None):
    old = sys.stdout
    if stdout is None:
        stdout = StringIO()
    sys.stdout = stdout
    yield stdout
    sys.stdout = old
